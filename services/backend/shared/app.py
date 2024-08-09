from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from home.settings import settings

from shared.lib.db import open_database_connection_pool, close_database_connection_pool
from shared.lib.routes import register_route_class, register_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    await open_database_connection_pool()
    yield
    await close_database_connection_pool()


app = FastAPI(
    title=settings.service_name,
    docs_url="/docs" if settings.enable_swagger else None,
    redoc_url="/redoc" if settings.enable_swagger else None,
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["GET", "PUT", "POST", "DELETE", "OPTIONS"],
            allow_headers=["*"],
        )
    ],
    lifespan=lifespan,
)

register_route_class(app)
register_routes(app)
