from pathlib import Path

from git import Repo
from langchain_core.documents import Document


def load_documents(repo: Repo, slug: str) -> list[Document]:
	"""Converts the wiki repository into a list of documents to be parsed"""

	root = Path(repo.working_tree_dir)
	tracked = repo.git.ls_files().splitlines()
	docs = []
	for rel in tracked:
		path = root / rel
		if path.suffix.lower() != ".md":
			continue
		try:
			if not path.is_file():
				continue
			text = path.read_text(encoding="utf-8", errors="ignore")
		except OSError:
			print(f"Skipping {rel}: could not be read.")
			continue
		if not text.strip():
			continue
		metadata = {"source": rel, "repo": slug}
		docs.append(Document(page_content=text, metadata=metadata))
	return docs
