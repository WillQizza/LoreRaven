import json
from collections.abc import Iterator
from dataclasses import replace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from loreraven.api import routes
from loreraven.api.deps import get_assistant
from loreraven.api.routes import router
from loreraven.db import repositories
from loreraven.ingest import IngestError, IngestResult, job


class FakeAssistant:
	def __init__(self, events: list[tuple[str, Any]] | None = None, error: str | None = None):
		self.events = events or []
		self.error = error
		self.calls: list[str] = []

	def stream(self, question: str, k: int | None = None) -> Iterator[tuple[str, Any]]:
		self.calls.append(question)
		yield from self.events
		if self.error:
			raise RuntimeError(self.error)


def build_client(assistant: FakeAssistant) -> TestClient:
	app = FastAPI()
	app.include_router(router)
	app.dependency_overrides[get_assistant] = lambda: assistant

	return TestClient(app)


def parse_frames(body: str) -> list[tuple[str, Any]]:
	"""Turn a raw SSE body back into `(event, data)` pairs."""
	frames = []
	for block in body.strip().split("\n\n"):
		lines = block.splitlines()
		event = next(line.removeprefix("event: ") for line in lines if line.startswith("event: "))
		data = next(line.removeprefix("data: ") for line in lines if line.startswith("data: "))
		frames.append((event, json.loads(data)))

	return frames


@pytest.fixture
def answering() -> FakeAssistant:
	return FakeAssistant([
		("sources", ["owner/repo/Home.md"]),
		("token", "Lore"),
		("token", "Raven"),
		("done", None),
	])


def test_health_reports_ok() -> None:
	client = build_client(FakeAssistant())

	response = client.get("/api/health")

	assert response.status_code == 200
	assert response.json() == {"status": "ok"}


def test_chat_streams_sources_then_tokens_then_done(answering: FakeAssistant) -> None:
	response = build_client(answering).post("/api/chat", json={"question": "who?"})

	assert response.status_code == 200
	assert parse_frames(response.text) == [
		("sources", ["owner/repo/Home.md"]),
		("token", "Lore"),
		("token", "Raven"),
		("done", None),
	]


def test_chat_passes_the_question_through(answering: FakeAssistant) -> None:
	build_client(answering).post("/api/chat", json={"question": "who?"})
	assert answering.calls == ["who?"]

def test_chat_reports_a_mid_stream_failure_as_an_error_event() -> None:
	assistant = FakeAssistant([("token", "partial")], error="the database broke")

	response = build_client(assistant).post("/api/chat", json={"question": "who?"})

	assert response.status_code == 200
	assert parse_frames(response.text) == [
		("token", "partial"),
		("error", "the database broke"),
	]


class FakeRegistry:
	Status = repositories.Status
	RepositoryRow = repositories.RepositoryRow

	def __init__(self) -> None:
		self.rows: dict[str, repositories.RepositoryRow] = {}
		self.next_id = 1

	def upsert_ingesting(self, slug: str, url: str):
		existing = self.rows.get(slug)
		if existing is not None and existing.status == self.Status.INGESTING:
			return None

		row_id = existing.id if existing is not None else self.next_id
		if existing is None:
			self.next_id += 1

		row = repositories.RepositoryRow(row_id, slug, url, self.Status.INGESTING, None)
		self.rows[slug] = row
		return row

	def set_status(self, slug: str, status: repositories.Status, *, error: str | None = None) -> None:
		self.rows[slug] = replace(self.rows[slug], status=status, error=error)

	def list_repositories(self, status: repositories.Status | None = None) -> list[repositories.RepositoryRow]:
		return [row for row in self.rows.values() if status is None or row.status == status]

	def get_repository(self, id: int):
		return next((row for row in self.rows.values() if row.id == id), None)

	def delete_repository(self, id: int) -> None:
		self.rows = {slug: row for slug, row in self.rows.items() if row.id != id}


@pytest.fixture
def registry(monkeypatch: pytest.MonkeyPatch) -> FakeRegistry:
	fake = FakeRegistry()
	monkeypatch.setattr(routes, "repositories", fake)
	monkeypatch.setattr(job, "repositories", fake)
	monkeypatch.setattr(
		job,
		"ingest_repo",
		lambda url: IngestResult(slug="owner/repo", pages=2, chunks=5),
	)
	return fake


@pytest.fixture
def deleted_chunks(monkeypatch: pytest.MonkeyPatch) -> list[str]:
	slugs: list[str] = []

	class FakeStore:
		def delete(self, filter: dict[str, str]) -> None:
			slugs.append(filter["repo"])

	monkeypatch.setattr(routes, "open_store", FakeStore)
	return slugs


def test_repositories_starts_empty(registry: FakeRegistry) -> None:
	response = build_client(FakeAssistant()).get("/api/repositories")

	assert response.status_code == 200
	assert response.json() == []


def test_adding_a_repository_returns_202_and_finishes_ready(registry: FakeRegistry) -> None:
	client = build_client(FakeAssistant())

	response = client.post("/api/repositories", json={"url": "https://github.com/owner/repo"})

	assert response.status_code == 202
	body = response.json()
	assert body["status"] == "ingesting"
	assert body["url"] == "https://github.com/owner/repo.wiki.git"

	listed = client.get("/api/repositories").json()
	assert listed == [{"id": body["id"], "url": body["url"], "status": "ready", "error": None}]


def test_adding_a_repository_that_is_ingesting_is_a_conflict(registry: FakeRegistry) -> None:
	registry.upsert_ingesting("owner/repo", "https://github.com/owner/repo.wiki.git")

	response = build_client(FakeAssistant()).post(
		"/api/repositories", json={"url": "https://github.com/owner/repo"}
	)

	assert response.status_code == 409


@pytest.mark.parametrize(
	"url",
	[
		"",
		"owner/repo",
		"/tmp/local",
		"https://github.com/a b",
		"https://gitlab.com/owner/repo",
		"https://github.com.evil.com/owner/repo",
		"ftp://github.com/owner/repo",
	],
)
def test_adding_rejects_urls_that_are_not_github_repositories(registry: FakeRegistry, url: str) -> None:
	response = build_client(FakeAssistant()).post("/api/repositories", json={"url": url})

	assert response.status_code == 422


def test_a_failed_ingest_is_recorded_on_the_row(registry: FakeRegistry, monkeypatch: pytest.MonkeyPatch) -> None:
	def fail(url: str):
		raise IngestError("No markdown pages found in the wiki.")

	monkeypatch.setattr(job, "ingest_repo", fail)
	client = build_client(FakeAssistant())

	client.post("/api/repositories", json={"url": "https://github.com/owner/repo"})

	row = client.get("/api/repositories").json()[0]
	assert row["status"] == "failed"
	assert row["error"] == "No markdown pages found in the wiki."


def test_an_unexpected_ingest_error_does_not_leak_details(registry: FakeRegistry, monkeypatch: pytest.MonkeyPatch) -> None:
	def fail(url: str):
		raise RuntimeError("password=hunter2")

	monkeypatch.setattr(job, "ingest_repo", fail)
	client = build_client(FakeAssistant())

	client.post("/api/repositories", json={"url": "https://github.com/owner/repo"})

	row = client.get("/api/repositories").json()[0]
	assert row["status"] == "failed"
	assert "hunter2" not in row["error"]


def test_deleting_removes_the_chunks_and_the_row(registry: FakeRegistry, deleted_chunks: list[str]) -> None:
	client = build_client(FakeAssistant())
	created = client.post("/api/repositories", json={"url": "https://github.com/owner/repo"}).json()

	response = client.delete(f"/api/repositories/{created['id']}")

	assert response.status_code == 204
	assert deleted_chunks == ["owner/repo"]
	assert client.get("/api/repositories").json() == []


def test_deleting_an_unknown_repository_is_404(registry: FakeRegistry, deleted_chunks: list[str]) -> None:
	response = build_client(FakeAssistant()).delete("/api/repositories/99")

	assert response.status_code == 404
	assert deleted_chunks == []


def test_deleting_a_repository_that_is_ingesting_is_a_conflict(registry: FakeRegistry, deleted_chunks: list[str]) -> None:
	row = registry.upsert_ingesting("owner/repo", "https://github.com/owner/repo.wiki.git")

	response = build_client(FakeAssistant()).delete(f"/api/repositories/{row.id}")

	assert response.status_code == 409
	assert deleted_chunks == []
