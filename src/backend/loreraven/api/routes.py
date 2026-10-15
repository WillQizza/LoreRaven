from collections.abc import Iterator

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse

from ..cli.query import Assistant
from ..db import open_store, repositories
from ..ingest import normalize_wiki_url, repo_slug, run_ingest
from .deps import get_assistant
from .schemas import AddRepositoryRequest, ChatRequest, RepositoryResponse
from .sse import sse

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict[str, str]:
	return {"status": "ok"}


@router.post("/chat", response_class=StreamingResponse)
def chat(request: ChatRequest, assistant: Assistant = Depends(get_assistant)):
	"""Stream one answer as SSE: a `sources` frame, then `token` frames, then `done`."""

	try:
		for event, data in assistant.stream(request.question):
			yield sse(event, data)
	except Exception as error:
		# The response headers are already sent, so a status code is no longer
		# available to report this with.
		yield sse("error", str(error))


def _to_response(row: repositories.RepositoryRow) -> RepositoryResponse:
	return RepositoryResponse(
		id=row.id,
		url=row.url,
		status=row.status,
		error=row.error,
	)

@router.get("/repositories")
def get_repositories() -> list[RepositoryResponse]:
	return [_to_response(row) for row in repositories.list_repositories()]


@router.post("/repositories", status_code=202)
def add_repository(request: AddRepositoryRequest, background_tasks: BackgroundTasks) -> RepositoryResponse:
	url = normalize_wiki_url(request.url)
	slug = repo_slug(url)
	row = repositories.upsert_ingesting(slug, url)
	if row is None:
		raise HTTPException(status_code=409, detail="This repository is already being ingested.")

	background_tasks.add_task(run_ingest, slug, url)
	return _to_response(row)


@router.delete("/repositories/{id}", status_code=204)
def delete_repository(id: int) -> Response:
	row = repositories.get_repository(id)
	if row is None:
		raise HTTPException(status_code=404, detail="Repository not found.")

	if row.status == repositories.Status.INGESTING:
		raise HTTPException(status_code=409, detail="This repository is still being ingested.")

	open_store().delete(filter={"repo": row.slug})
	repositories.delete_repository(id)
	
	return Response(status_code=204)