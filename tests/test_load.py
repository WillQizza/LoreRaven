from git import Repo

from loreraven.ingest.load import load_documents


def test_loads_only_markdown_pages(wiki_repo: Repo) -> None:
	docs = load_documents(wiki_repo, "owner/repo")

	sources = sorted(doc.metadata["source"] for doc in docs)
	assert sources == ["Home.md", "Shouty.MD", "docs/Guide.md"]


def test_skips_non_markdown_and_blank_pages(wiki_repo: Repo) -> None:
	sources = {doc.metadata["source"] for doc in load_documents(wiki_repo, "owner/repo")}

	assert "notes.txt" not in sources
	assert "Empty.md" not in sources


def test_uppercase_extension_is_matched(wiki_repo: Repo) -> None:
	"""`.MD` must load - the suffix check lowercases before comparing."""
	sources = {doc.metadata["source"] for doc in load_documents(wiki_repo, "owner/repo")}

	assert "Shouty.MD" in sources


def test_every_document_carries_repo_and_source(wiki_repo: Repo) -> None:
	docs = load_documents(wiki_repo, "owner/repo")

	assert docs
	for doc in docs:
		assert doc.metadata["repo"] == "owner/repo"
		assert doc.metadata["source"]
		assert doc.page_content.strip()


def test_no_pages_returns_empty_list(tmp_path) -> None:
	empty = Repo.init(tmp_path / "bare")
	assert load_documents(empty, "owner/repo") == []
