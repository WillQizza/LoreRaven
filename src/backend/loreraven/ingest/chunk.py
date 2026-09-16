from langchain_core.documents import Document
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

# Too many chunks are likely to be a bunch of spam or noise. Skip it.
MAX_CHUNKS_PER_PAGE = 250


def chunk_documents(docs: list[Document]) -> list[Document]:
	"""Split pages into chunks, dropping any page that splits into too many."""

	splitter = RecursiveCharacterTextSplitter.from_language(
		language=Language.MARKDOWN, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
	)
	chunks = []
	for doc in docs:
		page_chunks = splitter.split_documents([doc])
		if len(page_chunks) > MAX_CHUNKS_PER_PAGE:
			print(
				f"Skipping {doc.metadata['source']}: {len(page_chunks)} chunks is over "
				f"the {MAX_CHUNKS_PER_PAGE} allowed per page."
			)
			continue
		chunks.extend(page_chunks)
	return chunks
