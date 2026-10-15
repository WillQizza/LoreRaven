from pathlib import Path

from git import Repo
from langchain_core.documents import Document


def load_documents(repo: Repo, slug: str) -> list[Document]:
	"""Converts the wiki repository into a list of documents to be parsed"""

	if not repo.head.is_valid():
		return []

	docs = []
	for blob in repo.head.commit.tree.traverse():
		if blob.type != "blob" or Path(blob.path).suffix.lower() != ".md":
			continue

		text = blob.data_stream.read().decode("utf-8", errors="ignore")
		if not text.strip():
			continue

		metadata = {"source": blob.path, "repo": slug}
		docs.append(Document(page_content=text, metadata=metadata))
	return docs
