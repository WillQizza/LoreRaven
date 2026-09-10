from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .. import __version__, config
from .deps import init_assistant
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
	try:
		config.require_env()
		init_assistant()
	except SystemExit as error:
		# `require_env` and `open_store` report failures by exiting, which a server would
		# swallow as a silent shutdown. Surface it as a real startup error instead.
		raise RuntimeError(str(error)) from error

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
