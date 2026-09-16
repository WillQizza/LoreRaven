import stat
from pathlib import Path

import pytest
from git import Repo

from loreraven.ingest.clone import _remove_tree, clone_repo


def test_private_remove_tree_deletes_directory(tmp_path: Path) -> None:
	target = tmp_path / "tree"
	(target / "nested").mkdir(parents=True)
	(target / "nested" / "file.txt").write_text("data", encoding="utf-8")

	_remove_tree(target)

	assert not target.exists()


def test_clone_repo_checks_out_the_source(wiki_repo: Repo, tmp_path: Path) -> None:
	dest = tmp_path / "clone"

	cloned = clone_repo(wiki_repo.working_tree_dir, dest)

	assert Path(cloned.working_tree_dir) == dest
	assert (dest / "Home.md").exists()


def test_clone_repo_replaces_an_existing_checkout(wiki_repo: Repo, tmp_path: Path) -> None:
	dest = tmp_path / "clone"
	clone_repo(wiki_repo.working_tree_dir, dest)
	stale = dest / "stale-marker.txt"
	stale.write_text("left over from a previous ingest", encoding="utf-8")

	clone_repo(wiki_repo.working_tree_dir, dest)

	assert not stale.exists()
	assert (dest / "Home.md").exists()