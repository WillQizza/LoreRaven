import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path

from git import GitCommandError, Repo

from .. import config
from ..db import ensure_vector_table_exists, open_store
from .chunk import chunk_documents
from .clone import clone_repo, remove_tree
from .errors import IngestError
from .load import load_documents
from .wiki import normalize_wiki_url, repo_slug

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IngestResult:
	slug: str
	pages: int
	chunks: int


def ingest_repo(repo_url: str) -> IngestResult:
	"""Ingests a repository into the embeddings."""

	repo_url = normalize_wiki_url(repo_url)
	slug = repo_slug(repo_url)

	root = Path(config.REPO_DIR)
	root.mkdir(parents=True, exist_ok=True)
	workdir = Path(tempfile.mkdtemp(dir=root))
	repo: Repo | None = None
	try:
		logger.info("Cloning %s...", repo_url)
		try:
			repo = clone_repo(repo_url, workdir / "wiki")
		except GitCommandError as error:
			raise IngestError(f"Could not clone {repo_url}.") from error

		logger.info("Collecting wiki pages...")
		docs = load_documents(repo, slug)
		if not docs:
			raise IngestError("No markdown pages found in the wiki.")

		chunks = chunk_documents(docs)
		if not chunks:
			raise IngestError("Every page was skipped; there is nothing to index.")
		logger.info(
			"%d pages -> %d chunks. Embedding with %s...",
			len(docs),
			len(chunks),
			config.EMBED_MODEL,
		)

		store = open_store()
		store.delete(filter={"repo": slug})
		store.add_documents(chunks)
		logger.info("Ingested")
		return IngestResult(slug=slug, pages=len(docs), chunks=len(chunks))
	finally:
		# Windows keeps git files open until the repo is closed
		if repo is not None:
			repo.close()
		try:
			remove_tree(workdir)
		except OSError:
			logger.warning("Could not remove the temporary clone at %s.", workdir)
