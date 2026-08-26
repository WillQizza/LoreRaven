from .. import config
from ..db import ensure_table_exists, open_store
from .chunk import chunk_documents
from .clone import clone_repo
from .load import load_documents
from .wiki import normalize_wiki_url, repo_slug


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
