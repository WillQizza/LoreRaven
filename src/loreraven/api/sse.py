import json
from typing import Any


def sse(event: str, data: Any) -> str:
	"""Format one Server-Sent Events frame.

	`data` is always JSON, so the browser has a single parse path for every event type.
	"""
	return f"event: {event}\ndata: {json.dumps(data)}\n\n"
