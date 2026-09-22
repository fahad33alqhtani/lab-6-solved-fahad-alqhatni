"""Application factory with lifespan model loading, trace/timing
middleware, and a global exception handler that never leaks a stack
trace to the client.
"""
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from fraud_service.adapters.sklearn_model import SklearnModel
from fraud_service.config import Settings
from fraud_service.logging_setup import configure_logging
from fraud_service.service.scorer import FraudScorer

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = Settings()
    configure_logging(settings.log_level)
    t0 = time.perf_counter()
    model = SklearnModel.load(settings.model_path)
    # warm-up: pay lazy-init cost now, not on the first user request
    model.predict_proba({"amount_log": 0.0, "is_night": 0})
    log.info("model_loaded", version=model.model_version,
             seconds=round(time.perf_counter() - t0, 3),
             git_sha=settings.git_sha)

    app.state.scorer = FraudScorer(model=model, block_threshold=settings.block_threshold)
    app.state.settings = settings
    yield
    # teardown (nothing to close here yet)


def create_app() -> FastAPI:
    app = FastAPI(title="Fraud Scoring Service", version="1.0.0", lifespan=lifespan)

    from fraud_service.api.routes import router
    app.include_router(router, prefix="/v1")

    @app.middleware("http")
    async def trace_and_time(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        trace_id = request.headers.get("X-Trace-Id", uuid.uuid4().hex[:16])
        request.state.trace_id = trace_id
        # BIND BEFORE call_next: the route's own log lines (prediction_served)
        # only carry trace_id if the context vars are bound before it runs.
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            trace_id=trace_id, path=request.url.path, method=request.method)
        t0 = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        response.headers["X-Trace-Id"] = trace_id
        response.headers["X-Response-Time-Ms"] = str(elapsed_ms)
        log.info("http_request", status=response.status_code, latency_ms=elapsed_ms)
        return response

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception) -> JSONResponse:
        trace_id = getattr(request.state, "trace_id", "unknown")
        return JSONResponse(status_code=500, content={"error": {
            "code": "INTERNAL_ERROR",
            "message": "Unexpected error; contact support with trace_id",
            "trace_id": trace_id}})

    return app


app = create_app()
