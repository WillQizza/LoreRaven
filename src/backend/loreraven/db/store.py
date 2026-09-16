from functools import cache

from asyncpg.exceptions import DuplicateTableError
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import Column, PGEngine, PGVectorStore
from sqlalchemy.exc import ProgrammingError

from .. import config

# Columns of data associated with the embeddings
METADATA_COLUMNS = ("repo",)


@cache
def _engine() -> PGEngine:
	"""One connection pool per process, shared by `ensure_table` and `open_store`."""
	return PGEngine.from_connection_string(config.DATABASE_URL)


def ensure_table_exists():
	"""Create the vector table if it is absent."""

	try:
		_engine().init_vectorstore_table(
			config.TABLE,
			vector_size=config.EMBED_DIM,
			metadata_columns=[Column(name, "TEXT") for name in METADATA_COLUMNS],
		)
	except ProgrammingError as error:
		# Initialization failed somehow perhaps?
		if getattr(error.orig, "sqlstate", None) != DuplicateTableError.sqlstate:
			raise


def open_store() -> PGVectorStore:
	"""Return a `PGVectorStore` for the configured table, which must already exist."""

	embeddings = OpenAIEmbeddings(model=config.EMBED_MODEL)
	try:
		return PGVectorStore.create_sync(
			_engine(),
			embeddings,
			config.TABLE,
			metadata_columns=list(METADATA_COLUMNS),
		)
	except ValueError as error:
		# `create_sync` builds its column map from `information_schema`, where a missing
		# table is indistinguishable from a mismatched one: both come back empty.
		raise SystemExit(
			f"Table {config.TABLE!r} is missing or has an unexpected schema ({error}). "
			"Run `loreraven ingest <repo>` to build it."
		) from error
