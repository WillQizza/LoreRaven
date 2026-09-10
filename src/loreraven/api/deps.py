from ..cli.query import Assistant

_assistant: Assistant | None = None


def init_assistant() -> None:
	"""Build the process-wide `Assistant`, opening the connection pool once."""
	global _assistant
	if _assistant is None:
		_assistant = Assistant()


def get_assistant() -> Assistant:
	"""FastAPI dependency. Overridden in tests with a fake."""
	if _assistant is None:
		raise RuntimeError("Assistant is not initialized; the app lifespan did not run.")

	return _assistant
