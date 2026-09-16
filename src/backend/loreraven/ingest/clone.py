import shutil
import stat
from pathlib import Path

from git import Repo


def _remove_tree(path: Path) -> None:
	"""Utility to delete a folder"""

	# Windows has a issue where files need to be changed from readonly before
	# they can be deleted.
	for child in path.rglob("*"):
		if child.is_file():
			child.chmod(child.stat().st_mode | stat.S_IWRITE)

	shutil.rmtree(path)


def clone_repo(repo_url: str, dest: str | Path, branch: str | None = None) -> Repo:
	"""Clones a repository"""

	dest = Path(dest)
	if dest.exists():
		_remove_tree(dest)
	dest.parent.mkdir(parents=True, exist_ok=True)
	kwargs = {"depth": 1}
	if branch:
		kwargs["branch"] = branch
	return Repo.clone_from(repo_url, str(dest), **kwargs)
