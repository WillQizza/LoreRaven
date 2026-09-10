from types import SimpleNamespace

from langchain_core.documents import Document

from loreraven import config
from loreraven.cli.query import Assistant, cite, format_docs


def build_assistant(
	docs: list[Document], tokens: list[str], searches: list[int] | None = None
) -> Assistant:
	"""An `Assistant` with both collaborators faked, bypassing `__init__`.

	`searches`, when given, records the `k` each retrieval ran with.
	"""

	def similarity_search(question: str, k: int) -> list[Document]:
		if searches is not None:
			searches.append(k)

		return docs

	assistant = Assistant.__new__(Assistant)
	assistant.store = SimpleNamespace(similarity_search=similarity_search)
	assistant.llm = SimpleNamespace(
		stream=lambda messages: (SimpleNamespace(text=token) for token in tokens)
	)

	return assistant


def test_cite_joins_repo_and_source() -> None:
	assert cite({"repo": "owner/repo", "source": "Home.md"}) == "owner/repo/Home.md"


def test_cite_marks_an_unknown_source() -> None:
	assert cite({"repo": "owner/repo"}) == "owner/repo/?"


def test_cite_formats_every_ingested_document() -> None:
	"""`load_documents` always sets both keys, so this is the shape `cite` really sees."""
	metadata = {"source": "docs/Guide.md", "repo": "owner/repo"}

	assert cite(metadata) == "owner/repo/docs/Guide.md"


def test_format_docs_on_no_documents() -> None:
	assert format_docs([]) == ""


def test_stream_retrieves_top_k_chunks_by_default() -> None:
	searches: list[int] = []
	assistant = build_assistant([], [], searches)

	list(assistant.stream("who?"))

	assert searches == [config.TOP_K]


def test_stream_lets_a_caller_override_top_k() -> None:
	searches: list[int] = []
	assistant = build_assistant([], [], searches)

	list(assistant.stream("who?", k=9))

	assert searches == [9]
