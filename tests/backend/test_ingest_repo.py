from pathlib import Path
from typing import Any

import pytest
from git import Repo

from loreraven import config
from loreraven.ingest import IngestError, repo as repo_module
from loreraven.ingest.repo import ingest_repo


class FakeStore:
	def __init__(self) -> None:
		self.deleted: list[dict[str, str]] = []
		self.added: list[Any] = []

	def delete(self, filter: dict[str, str]) -> None:
		self.deleted.append(filter)

	def add_documents(self, docs: list[Any]) -> None:
		self.added.extend(docs)


@pytest.fixture
def store(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> FakeStore:
	fake = FakeStore()
	monkeypatch.setattr(config, "REPO_DIR", str(tmp_path / "work"))
	monkeypatch.setattr(repo_module, "open_store", lambda: fake)
	monkeypatch.setattr(repo_module, "ensure_vector_table_exists", lambda: None)
	return fake


@pytest.fixture
def serve_wiki(monkeypatch: pytest.MonkeyPatch, wiki_repo: Repo) -> None:
	real_clone = repo_module.clone_repo
	monkeypatch.setattr(
		repo_module,
		"clone_repo",
		lambda url, dest: real_clone(wiki_repo.working_tree_dir, dest),
	)


def test_ingest_replaces_the_repo_chunks_and_reports_counts(store: FakeStore, serve_wiki: None) -> None:
	result = ingest_repo("https://github.com/owner/repo")

	assert result.slug == "owner/repo"
	assert result.pages == 3
	assert result.chunks == len(store.added) > 0
	assert store.deleted == [{"repo": "owner/repo"}]


def test_ingest_removes_its_temporary_clone(store: FakeStore, serve_wiki: None, tmp_path: Path) -> None:
	ingest_repo("https://github.com/owner/repo")

	assert list((tmp_path / "work").iterdir()) == []


def test_ingest_raises_when_the_wiki_has_no_pages(
	store: FakeStore, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	empty = tmp_path / "empty"
	empty.mkdir()
	Repo.init(empty)
	real_clone = repo_module.clone_repo
	monkeypatch.setattr(
		repo_module, "clone_repo", lambda url, dest: real_clone(str(empty), dest)
	)

	with pytest.raises(IngestError):
		ingest_repo("https://github.com/owner/repo")

	assert store.added == []
	assert list((tmp_path / "work").iterdir()) == []


def test_ingest_wraps_clone_failures(store: FakeStore, tmp_path: Path) -> None:
	missing = tmp_path / "does-not-exist"
	with pytest.raises(IngestError, match="Could not clone"):
		ingest_repo(str(missing))
