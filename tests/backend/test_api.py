import json
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from loreraven.api.deps import get_assistant
from loreraven.api.routes import router


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
	assert response.headers["content-type"].startswith("text/event-stream")
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
