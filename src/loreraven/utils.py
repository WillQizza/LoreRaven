import shutil
import stat
from pathlib import Path


def remove_tree(path: Path) -> None:
	"""Utility to delete a folder"""
	
	# Windows has a issue where files need to be changed from readonly before 
	# they can be deleted.
	for child in path.rglob("*"):
		if child.is_file():
			child.chmod(child.stat().st_mode | stat.S_IWRITE)

	shutil.rmtree(path)
