from functools import cache
from typing import Any

from asyncpg.exceptions import DuplicateTableError
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import Column, PGEngine, PGVectorStore
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from .. import config

# Columns of data associated with the embeddings
METADATA_COLUMNS = ("repo",)


@cache
def _engine() -> PGEngine:
	"""One connection pool per process, shared by `ensure_table` and `open_store`."""
	return PGEngine.from_connection_string(config.DATABASE_URL)


def ensure_vector_table_exists():
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
		raise RuntimeError(
			f"Table {config.TABLE!r} is missing or has an unexpected schema ({error})."
		) from error


async def _execute(statement: str, params: dict[str, Any]) -> list[dict[str, Any]]:
	async with _engine()._pool.begin() as connection:
		result = await connection.execute(text(statement), params)
		if not result.returns_rows:
			return []

		return [dict(row._mapping) for row in result]


def run_sql(statement: str, **params: Any) -> list[dict[str, Any]]:
	# Hacky way to run SQL stmts using the langchain postgres library
	return _engine()._run_as_sync(_execute(statement, params))
