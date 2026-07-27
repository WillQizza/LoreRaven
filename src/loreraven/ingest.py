import shutil
from pathlib import Path

from git import Repo
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter
from sqlalchemy import delete as sa_delete

from . import config

# GitHub wiki (.wiki.git) repos are made up of markdown pages, so those are all we index.
PAGE_EXTENSIONS = {".md", ".markdown"}
MAX_FILE_BYTES = 200_000


def normalize_wiki_url(repo_url):
	url = repo_url.rstrip("/")
	if url.endswith(".wiki.git"):
		return url
	
	if url.endswith(".git"):
		url = url[: -len(".git")]

	if url.endswith(".wiki"):
		return url + ".git"
	
	return url + ".wiki.git"


def repo_slug(repo_url):
	url = repo_url.rstrip("/")
	for suffix in (".wiki.git", ".wiki", ".git"):
		if url.endswith(suffix):
			url = url[: -len(suffix)]
			break
	# Drop the scheme and any `user@host:` / `host/` prefix, keeping the path.
	url = url.split("://", 1)[-1].replace(":", "/")
	parts = [p for p in url.split("/") if p]
	if len(parts) >= 2:
		return "/".join(parts[-2:])
	return parts[-1] if parts else repo_url


def clone_repo(repo_url, dest, branch=None):
	dest = Path(dest)
	if dest.exists():
		shutil.rmtree(dest)
	dest.parent.mkdir(parents=True, exist_ok=True)
	kwargs = {"depth": 1}
	if branch:
		kwargs["branch"] = branch
	return Repo.clone_from(repo_url, str(dest), **kwargs)


def load_documents(repo, slug):
	root = Path(repo.working_tree_dir)
	tracked = repo.git.ls_files().splitlines()
	docs = []
	for rel in tracked:
		path = root / rel
		if path.suffix.lower() not in PAGE_EXTENSIONS:
			continue
		try:
			if not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
				continue
			text = path.read_text(encoding="utf-8", errors="ignore")
		except OSError:
			continue
		if not text.strip():
			continue
		docs.append(Document(page_content=text, metadata={"source": rel, "repo": slug}))
	return docs


def delete_repo_docs(store, slug):
	with store._make_sync_session() as session:
		collection = store.get_collection(session)
		if collection is None:
			return
		embedding = store.EmbeddingStore
		stmt = (
			sa_delete(embedding)
			.where(embedding.collection_id == collection.uuid)
			.where(embedding.cmetadata["repo"].astext == slug)
		)
		session.execute(stmt)
		session.commit()


def ingest_repo(repo_url, branch=None):
	repo_url = normalize_wiki_url(repo_url)
	slug = repo_slug(repo_url)
	print(f"Cloning {repo_url}...")
	repo = clone_repo(repo_url, config.REPO_DIR, branch=branch)

	print("Collecting wiki pages...")
	docs = load_documents(repo, slug)
	if not docs:
		raise SystemExit("No markdown pages found in the wiki.")

	splitter = RecursiveCharacterTextSplitter.from_language(
		language=Language.MARKDOWN, chunk_size=1000, chunk_overlap=150
	)
	chunks = splitter.split_documents(docs)
	print(f"{len(docs)} pages -> {len(chunks)} chunks. Embedding with {config.EMBED_MODEL}...")

	embeddings = OpenAIEmbeddings(model=config.EMBED_MODEL)
	store = PGVector(
		embeddings=embeddings,
		collection_name=config.COLLECTION,
		connection=config.DATABASE_URL,
		use_jsonb=True,
	)

	delete_repo_docs(store, slug)
	store.add_documents(chunks)
	print(f'Done. Ask away with: loreraven query "your question"')
