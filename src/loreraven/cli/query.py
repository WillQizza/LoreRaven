from collections.abc import Iterator
from typing import Any

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from .. import config
from ..db import open_store

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

	def answer(self, question: str, k: int | None = None) -> tuple[str, list[str]]:
		"""Answers a question without streaming. Used for CLI"""
		docs_count = k if k is not None else config.TOP_K
		docs = self.store.similarity_search(question, k=docs_count)
		if not docs:
			return ("No indexed content found. Have you run `ingest` yet?", [])

		messages = PROMPT.format_messages(question=question, context=format_docs(docs))
		response = self.llm.invoke(messages)

		sources = sorted({cite(d.metadata) for d in docs})
		return (response.text, sources)

	def stream(self, question: str, k: int | None = None) -> Iterator[tuple[str, Any]]:
		"""Streams LLM chunks for SSE"""
		docs_count = k if k is not None else config.TOP_K
		docs = self.store.similarity_search(question, k=docs_count)
		if not docs:
			yield ("token", "No indexed content found. Have you run `ingest` yet?")
			yield ("done", None)
			return

		yield ("sources", sorted({cite(d.metadata) for d in docs}))

		messages = PROMPT.format_messages(question=question, context=format_docs(docs))
		for chunk in self.llm.stream(messages):
			if chunk.text:
				yield ("token", chunk.text)

		yield ("done", None)
