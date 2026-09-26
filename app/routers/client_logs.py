from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Any, Dict, Optional
from app.logger import logger

router = APIRouter(prefix="/logs", tags=["logs"])

class ClientLog(BaseModel):
    level: str
    message: str
    url: Optional[str] = "unknown"
    userAgent: Optional[str] = "unknown"
    errorInfo: Optional[Dict[str, Any]] = None

@router.post("/client")
def log_client_error(payload: ClientLog, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    log_msg = f"[FRONTEND] {payload.message} | URL: {payload.url} | IP: {client_ip} | Info: {payload.errorInfo}"
    
    level = payload.level.lower()
    if level == "error":
        logger.error(log_msg)
    elif level == "warning":
        logger.warning(log_msg)
    elif level == "debug":
        logger.debug(log_msg)
    else:
        logger.info(log_msg)
        
    return {"status": "Logged successfully"}
