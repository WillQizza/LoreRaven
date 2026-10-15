from .repositories import ensure_registry_table_exists
from .store import ensure_vector_table_exists


def ensure_schema() -> None:
	ensure_vector_table_exists()
	ensure_registry_table_exists()
