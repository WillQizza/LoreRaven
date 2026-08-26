from pathlib import Path

from git import Repo
from langchain_core.documents import Document
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

from . import config
from .store import ensure_table_exists, open_store
from .utils import remove_tree

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

# Too many chunks are likely to be a bunch of spam or noise. Skip it.
MAX_CHUNKS_PER_PAGE = 250


def normalize_wiki_url(repo_url: str) -> str:
	"""Ensures repo urls always end with .wiki.git"""

	url = repo_url.rstrip("/")
	if url.endswith(".wiki.git"):
		return url
	
	if url.endswith(".git"):
		url = url[: -len(".git")]

	if url.endswith(".wiki"):
		return url + ".git"
	
	return url + ".wiki.git"


def repo_slug(repo_url: str) -> str:
	"""Converts the repository URL into a slug"""

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


def clone_repo(repo_url: str, dest: str | Path, branch: str | None = None) -> Repo:
	"""Clones a repository"""

	dest = Path(dest)
	if dest.exists():
		remove_tree(dest)
	dest.parent.mkdir(parents=True, exist_ok=True)
	kwargs = {"depth": 1}
	if branch:
		kwargs["branch"] = branch
	return Repo.clone_from(repo_url, str(dest), **kwargs)


def load_documents(repo: Repo, slug: str) -> list[Document]:
	"""Converts the wiki repository into a list of documents to be parsed"""

	root = Path(repo.working_tree_dir)
	tracked = repo.git.ls_files().splitlines()
	docs = []
	for rel in tracked:
		path = root / rel
		if path.suffix.lower() != ".md":
			continue
		try:
			if not path.is_file():
				continue
			text = path.read_text(encoding="utf-8", errors="ignore")
		except OSError:
			print(f"Skipping {rel}: could not be read.")
			continue
		if not text.strip():
			continue
		metadata = {"source": rel, "repo": slug}
		docs.append(Document(page_content=text, metadata=metadata))
	return docs


def chunk_documents(docs: list[Document]) -> list[Document]:
	"""Split pages into chunks, dropping any page that splits into too many."""

	splitter = RecursiveCharacterTextSplitter.from_language(
		language=Language.MARKDOWN, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
	)
	chunks = []
	for doc in docs:
		page_chunks = splitter.split_documents([doc])
		if len(page_chunks) > MAX_CHUNKS_PER_PAGE:
			print(
				f"Skipping {doc.metadata['source']}: {len(page_chunks)} chunks is over "
				f"the {MAX_CHUNKS_PER_PAGE} allowed per page."
			)
			continue
		chunks.extend(page_chunks)
	return chunks


def ingest_repo(repo_url: str, branch: str | None = None) -> None:
	"""Ingests a repository into the embeddings."""

	repo_url = normalize_wiki_url(repo_url)
	slug = repo_slug(repo_url)
	print(f"Cloning {repo_url}...")
	repo = clone_repo(repo_url, config.REPO_DIR, branch=branch)

	print("Collecting wiki pages...")
	docs = load_documents(repo, slug)
	if not docs:
		raise SystemExit("No markdown pages found in the wiki.")

	chunks = chunk_documents(docs)
	if not chunks:
		raise SystemExit("Every page was skipped; there is nothing to index.")
	print(f"{len(docs)} pages -> {len(chunks)} chunks. Embedding with {config.EMBED_MODEL}...")

	ensure_table_exists()
	store = open_store()
	store.delete(filter={"repo": slug})
	store.add_documents(chunks)
	print("Ingested")
