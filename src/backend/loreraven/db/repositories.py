from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .. import config
from .store import run_sql

_COLUMNS = "id, slug, url, status, error"


class Status(StrEnum):
	INGESTING = "ingesting"
	READY = "ready"
	FAILED = "failed"


@dataclass(frozen=True)
class RepositoryRow:
	id: int
	slug: str
	url: str
	status: Status
	error: str | None


def _table() -> str:
	name = f"{config.TABLE}_repositories".replace('"', '""')
	return f'"{name}"'


def _row(values: dict[str, Any]) -> RepositoryRow:
	return RepositoryRow(**{**values, "status": Status(values["status"])})


def ensure_registry_table_exists() -> None:
	run_sql(
		f"""
		CREATE TABLE IF NOT EXISTS {_table()} (
			id SERIAL PRIMARY KEY,
			slug TEXT NOT NULL UNIQUE,
			url TEXT NOT NULL,
			status TEXT NOT NULL,
			error TEXT,
			created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
			updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
		)
		"""
	)


def upsert_ingesting(slug: str, url: str) -> RepositoryRow | None:
	# Returns None when already ingesting, so the check and the claim are one atomic statement
	rows = run_sql(
		f"""
		INSERT INTO {_table()} AS repos (slug, url, status)
		VALUES (:slug, :url, :status)
		ON CONFLICT (slug) DO UPDATE SET
			url = EXCLUDED.url,
			status = EXCLUDED.status,
			error = NULL,
			updated_at = now()
		WHERE repos.status <> :status
		RETURNING {_COLUMNS}
		""",
		slug=slug,
		url=url,
		status=Status.INGESTING.value,
	)
	return _row(rows[0]) if rows else None


def set_status(slug: str, status: Status, *, error: str | None = None) -> None:
	run_sql(
		f"""
		UPDATE {_table()}
		SET status = :status, error = :error, updated_at = now()
		WHERE slug = :slug
		""",
		slug=slug,
		status=status.value,
		error=error,
	)


def list_repositories(status: Status | None = None) -> list[RepositoryRow]:
	if status is None:
		rows = run_sql(f"SELECT {_COLUMNS} FROM {_table()} ORDER BY created_at, id")
	else:
		rows = run_sql(
			f"SELECT {_COLUMNS} FROM {_table()} WHERE status = :status ORDER BY created_at, id",
			status=status.value,
		)

	return [_row(values) for values in rows]


def get_repository(id: int) -> RepositoryRow | None:
	rows = run_sql(f"SELECT {_COLUMNS} FROM {_table()} WHERE id = :id", id=id)
	return _row(rows[0]) if rows else None


def delete_repository(id: int) -> None:
	run_sql(f"DELETE FROM {_table()} WHERE id = :id", id=id)
