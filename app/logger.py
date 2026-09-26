import sys
import uuid
import contextvars
from loguru import logger

# Context variable to hold the request ID for the current async task
request_id_var = contextvars.ContextVar("request_id", default="SYSTEM")

def _request_id_filter(record):
    """Injects the request ID from the context variable into the log record."""
    record["extra"]["request_id"] = request_id_var.get()
    return True

# Remove the default logger
logger.remove()

# 1. Console Output (Human Readable)
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{extra[request_id]}</cyan> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    filter=_request_id_filter,
    colorize=True,
    level="INFO"
)

# 2. File Output (Structured JSON for ELK/Filebeat)
logger.add(
    "logs/vetlog.jsonl",
    serialize=True,           # This makes it output pure JSON
    filter=_request_id_filter,
    rotation="500 MB",        # Rotate file when it gets too big
    retention="10 days",      # Keep old logs for 10 days
    level="DEBUG",            # Store everything in the JSON log
    backtrace=True,           # Include full exception traces
    diagnose=True             # Show variable values in exceptions
)

def set_request_id(request_id: str = None) -> str:
    """Sets a unique request ID for the current async context."""
    if not request_id:
        request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    return request_id
