from pathlib import Path

import pytest
from git import Repo


def _write(root: Path, rel: str, text: str) -> None:
	path = root / rel
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(text, encoding="utf-8")


@pytest.fixture
def wiki_repo(tmp_path: Path) -> Repo:
	"""A local git repo shaped like a GitHub wiki, with a mix of files to filter."""

	root = tmp_path / "wiki"
	root.mkdir()
	repo = Repo.init(root)
	with repo.config_writer() as writer:
		writer.set_value("user", "name", "LoreRaven Tests")
		writer.set_value("user", "email", "tests@example.com")

	_write(root, "Home.md", "# Home\n\nWelcome to the wiki.\n")
	_write(root, "docs/Guide.md", "# Guide\n\nHow to use the thing.\n")
	_write(root, "Shouty.MD", "# Shouty\n\nUppercase extension.\n")
	_write(root, "notes.txt", "not markdown\n")
	_write(root, "Empty.md", "   \n\n")

	repo.index.add(["Home.md", "docs/Guide.md", "Shouty.MD", "notes.txt", "Empty.md"])
	repo.index.commit("Initial wiki")
	return repo
