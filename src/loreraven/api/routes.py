from collections.abc import Iterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ..cli.query import Assistant
from .deps import get_assistant
from .schemas import ChatRequest
from .sse import sse

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict[str, str]:
	return {"status": "ok"}


@router.post("/chat")
def chat(request: ChatRequest, assistant: Assistant = Depends(get_assistant)) -> StreamingResponse:
	"""Stream one answer as SSE: a `sources` frame, then `token` frames, then `done`."""

	def frames() -> Iterator[str]:
		try:
			for event, data in assistant.stream(request.question):
				yield sse(event, data)
		except Exception as error:
			# The response headers are already sent, so a status code is no longer
			# available to report this with.
			yield sse("error", str(error))

	return StreamingResponse(
		frames(),
		media_type="text/event-stream",
		# Proxies buffer `text/event-stream` by default, which defeats the point of streaming.
		headers={
			"Cache-Control": "no-cache",
			"X-Accel-Buffering": "no",
		},
	)
