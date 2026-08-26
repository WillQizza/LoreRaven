import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DATABASE_URL = os.getenv("LORERAVEN_DATABASE_URL")

CHAT_MODEL = os.getenv("LORERAVEN_CHAT_MODEL", "gpt-4o-mini")
TABLE = os.getenv("LORERAVEN_TABLE", "loreraven")
REPO_DIR = os.getenv("LORERAVEN_REPO_DIR", ".loreraven/repo")

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
