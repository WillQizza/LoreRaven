import logging

from ..db import repositories
from .errors import IngestError
from .repo import IngestResult, ingest_repo

logger = logging.getLogger(__name__)


def record_ingest(slug: str, url: str) -> IngestResult:
	try:
		result = ingest_repo(url)
	except Exception as error:
		message = str(error) if isinstance(error, IngestError) else "Ingestion failed unexpectedly."
		repositories.set_status(slug, repositories.Status.FAILED, error=message)
		raise

	repositories.set_status(slug, repositories.Status.READY)
	return result


def run_ingest(slug: str, url: str) -> None:
	try:
		record_ingest(slug, url)
	except Exception:
		logger.exception("Ingesting %s failed", url)
