from typing import Any

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from . import config
from .db import open_store

PROMPT = ChatPromptTemplate.from_messages([
	(
		"system",
		"You are LoreRaven, an assistant that answers technical questions using documentation. "
		"Answer using only the provided context. If the context is insufficient, "
		"say so plainly. Cite wiki repositories when relevant.",
	),
	("human", "Question: {question}\n\nContext:\n{context}"),
])


def cite(metadata: dict[str, Any]) -> str:
	"""`owner/name/Page.md` citation for a chunk."""
	source = metadata.get("source", "?")
	repo = metadata.get("repo")
	return f"{repo}/{source}"


def format_docs(docs: list[Document]) -> str:
	blocks = []
	for doc in docs:
		blocks.append(f"# {cite(doc.metadata)}\n{doc.page_content}")

	return "\n\n".join(blocks)


class Assistant:
	def __init__(self) -> None:
		self.store = open_store()
		self.llm = ChatOpenAI(model=config.CHAT_MODEL, temperature=0)

	def answer(self, question: str, k: int = 4) -> tuple[str, list[str]]:
		"""Return (answer_text, sorted_source_paths) for a question."""
		docs = self.store.similarity_search(question, k=k)
		if not docs:
			return ("No indexed content found. Have you run `ingest` yet?", [])

		messages = PROMPT.format_messages(question=question, context=format_docs(docs))
		response = self.llm.invoke(messages)

		sources = sorted({cite(d.metadata) for d in docs})
		return (response.text, sources)
