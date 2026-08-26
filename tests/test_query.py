from langchain_core.documents import Document

from loreraven.query import cite, format_docs


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
