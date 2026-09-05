import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from .config import get_settings
from .routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ONE client for the whole process: it keeps TLS connections to Groq
    # alive between requests. Building one per request adds a full
    # handshake (~100ms+) to every single call.
    app.state.http = httpx.AsyncClient(
        limits=httpx.Limits(max_connections=20, max_keepalive_connections=10)
    )
    yield
    await app.state.http.aclose()


app = FastAPI(
    title="MediFind Symptom Sidecar",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)
app.include_router(router)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    # No auth, no Groq call. Answers one question: is the process alive?
    # Deliberately does NOT check Groq — a health check that depends on a
    # third party will restart your service during their outage.
    return {"status": "ok", "environment": settings.environment}
