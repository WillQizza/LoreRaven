from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from threading import Thread

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .. import __version__, config
from ..db import ensure_schema, repositories
from ..ingest import run_ingest
from .deps import init_assistant
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
	try:
		config.require_env()
	except SystemExit as error:
		raise RuntimeError(str(error)) from error

	ensure_schema()
	init_assistant()

	for row in repositories.list_repositories(repositories.Status.INGESTING):
		Thread(target=run_ingest, args=(row.slug, row.url), daemon=True).start()

	yield


def create_app() -> FastAPI:
	app = FastAPI(title="LoreRaven", version=__version__, lifespan=lifespan)

	app.add_middleware(
		CORSMiddleware,
		allow_origins=config.CORS_ORIGINS,
		allow_methods=["*"],
		allow_headers=["*"],
	)
	app.include_router(router)

	return app
