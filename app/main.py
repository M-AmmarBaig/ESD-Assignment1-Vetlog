from contextlib import asynccontextmanager
import time
from fastapi import FastAPI, Response, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.database import init_db
from app.agent import get_current_agent, init_checkpointer
from app.routers import auth, chat, config, conversations, reports, settings, webhook
from app.logger import logger, set_request_id

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await init_checkpointer()
    get_current_agent()
    logger.info("Agent ready. Application startup complete.")
    yield

app = FastAPI(title="Vetlog AI Backend", lifespan=lifespan)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the full stack trace with the request context
    logger.exception(f"Unhandled exception during {request.method} {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )

# Logging Middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    # Set a unique Request ID for this HTTP request cycle
    req_id = set_request_id()
    
    start_time = time.time()
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"Completed request: {request.method} {request.url.path} - Status: {response.status_code} - Latency: {process_time:.3f}s")
        # Optional: Attach Request ID to response headers so the frontend can track it
        response.headers["X-Request-ID"] = req_id
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Failed request: {request.method} {request.url.path} - Latency: {process_time:.3f}s - Error: {str(e)}")
        raise

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import auth, chat, config, conversations, reports, settings, webhook, client_logs

# Register all route modules
app.include_router(config.router)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(reports.router)
app.include_router(webhook.router)
app.include_router(settings.router)
app.include_router(client_logs.router)

@app.get("/")
def root():
    """Health-check endpoint."""
    logger.debug("Health check hit")
    return {"status": "alive"}

@app.get("/metrics")
def metrics():
    """Scraped by Prometheus. Returns current values of every metric in app/metrics.py."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
