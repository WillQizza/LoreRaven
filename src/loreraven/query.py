from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector

from . import config

PROMPT = ChatPromptTemplate.from_messages([
	(
		"system",
		"You are LoreRaven, an assistant that answers technical questions using documentation. "
		"Answer using only the provided context. If the context is insufficient, "
		"say so plainly. Cite wiki repositories when relevant.",
	),
	("human", "Question: {question}\n\nContext:\n{context}"),
])


def cite(metadata):
	"""`owner/name/Page.md` citation for a chunk, or just the page if no repo."""
	source = metadata.get("source", "?")
	repo = metadata.get("repo")
	if repo:
		return f"{repo}/{source}"

	return source


def format_docs(docs):
	blocks = []
	for doc in docs:
		blocks.append(f"# {cite(doc.metadata)}\n{doc.page_content}")

	return "\n\n".join(blocks)


class Assistant:
	def __init__(self):
		embeddings = OpenAIEmbeddings(model=config.EMBED_MODEL)
		self.store = PGVector(
			embeddings=embeddings,
			collection_name=config.COLLECTION,
			connection=config.DATABASE_URL,
			use_jsonb=True,
		)
		self.llm = ChatOpenAI(model=config.CHAT_MODEL, temperature=0)

	def answer(self, question, k=4):
		"""Return (answer_text, sorted_source_paths) for a question."""
		docs = self.store.similarity_search(question, k=k)
		if not docs:
			return ("No indexed content found. Have you run `ingest` yet?", [])

		messages = PROMPT.format_messages(question=question, context=format_docs(docs))
		response = self.llm.invoke(messages)

		sources = sorted({cite(d.metadata) for d in docs})
		return (response.content, sources)
