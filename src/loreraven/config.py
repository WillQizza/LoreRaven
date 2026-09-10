import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DATABASE_URL = os.getenv("LORERAVEN_DATABASE_URL")

CHAT_MODEL = os.getenv("LORERAVEN_CHAT_MODEL", "gpt-4o-mini")
TABLE = os.getenv("LORERAVEN_TABLE", "loreraven")
REPO_DIR = os.getenv("LORERAVEN_REPO_DIR", ".loreraven/repo")

# Chunks pulled from the store per question.
TOP_K = int(os.getenv("LORERAVEN_TOP_K", "4"))

# Browsers the web API accepts cross-origin requests from. The `ng serve` dev proxy makes
# these same-origin, so this only matters when the frontend is served from elsewhere.
CORS_ORIGINS = [
	origin.strip()
	for origin in os.getenv("LORERAVEN_CORS_ORIGINS", "http://localhost:4200").split(",")
	if origin.strip()
]

EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536


def require_env() -> None:
	missing = []
	if not OPENAI_API_KEY:
		missing.append("OPENAI_API_KEY")
	if not DATABASE_URL:
		missing.append("LORERAVEN_DATABASE_URL")

	if missing:
		raise SystemExit(
			"Missing required settings: "
			+ ", ".join(missing)
			+ "\nCopy .env.example to .env and fill it in."
		)
