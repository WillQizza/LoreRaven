import pytest
from langchain_core.documents import Document

from loreraven.ingest import chunk as chunk_module
from loreraven.ingest.chunk import chunk_documents


def _page(source: str, body: str) -> Document:
	return Document(page_content=body, metadata={"source": source, "repo": "owner/repo"})


def test_short_page_stays_one_chunk() -> None:
	chunks = chunk_documents([_page("Home.md", "# Home\n\nShort page.\n")])

	assert len(chunks) == 1
	assert chunks[0].page_content.strip().startswith("# Home")


def test_long_page_is_split() -> None:
	body = "\n\n".join(f"## Section {i}\n\n{'word ' * 200}" for i in range(10))

	chunks = chunk_documents([_page("Long.md", body)])

	assert len(chunks) > 1


def test_metadata_is_copied_onto_every_chunk() -> None:
	"""Chunks inherit `repo`, which is what the reindex filter deletes on."""
	body = "\n\n".join(f"## Section {i}\n\n{'word ' * 200}" for i in range(10))

	chunks = chunk_documents([_page("Long.md", body)])

	assert len(chunks) > 1
	for chunk in chunks:
		assert chunk.metadata["repo"] == "owner/repo"
		assert chunk.metadata["source"] == "Long.md"


def test_pages_over_the_chunk_cap_are_dropped(monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setattr(chunk_module, "MAX_CHUNKS_PER_PAGE", 2)
	body = "\n\n".join(f"## Section {i}\n\n{'word ' * 200}" for i in range(10))

	chunks = chunk_documents([_page("Spammy.md", body)])

	assert chunks == []


def test_a_dropped_page_does_not_drop_its_neighbours(monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setattr(chunk_module, "MAX_CHUNKS_PER_PAGE", 2)
	body = "\n\n".join(f"## Section {i}\n\n{'word ' * 200}" for i in range(10))

	chunks = chunk_documents([
		_page("Spammy.md", body),
		_page("Home.md", "# Home\n\nShort page.\n"),
	])

	assert [chunk.metadata["source"] for chunk in chunks] == ["Home.md"]

def test_no_documents_gives_no_chunks() -> None:
	assert chunk_documents([]) == []
