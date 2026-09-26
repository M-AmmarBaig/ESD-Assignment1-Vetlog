import time
from uuid import UUID
from typing import Any, Dict, List, Optional
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from app.logger import logger

class LoguruCallbackHandler(BaseCallbackHandler):
    """Callback Handler that logs LLM execution times and token usage to Loguru."""

    def __init__(self):
        self.start_times: Dict[UUID, float] = {}

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], *, run_id: UUID, parent_run_id: Optional[UUID] = None, tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> None:
        """Run when LLM starts running."""
        self.start_times[run_id] = time.time()
        logger.debug(f"LLM Call Started [run_id: {run_id}] - Waiting for response...")

    def on_llm_end(
        self, response: LLMResult, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any
    ) -> None:
        """Run when LLM ends running."""
        end_time = time.time()
        start_time = self.start_times.pop(run_id, end_time)
        latency = end_time - start_time
        
        # Try to extract token counts if the LLM provider returns them
        tokens = "Unknown"
        
        # 1. Try checking llm_output directly (OpenAI style)
        if response.llm_output and "token_usage" in response.llm_output:
            tokens = response.llm_output["token_usage"].get("total_tokens", "Unknown")
            
        # 2. Try checking message metadata (LangChain Chat Models style)
        if tokens == "Unknown" and response.generations:
            try:
                msg = response.generations[0][0].message
                if hasattr(msg, 'response_metadata') and msg.response_metadata:
                    if 'token_usage' in msg.response_metadata:
                        tokens = msg.response_metadata['token_usage'].get('total_tokens', 'Unknown')
                    elif 'usage_metadata' in msg.response_metadata:
                        tokens = msg.response_metadata['usage_metadata'].get('total_tokens', 'Unknown')
                if tokens == "Unknown" and hasattr(msg, 'usage_metadata') and msg.usage_metadata:
                    tokens = msg.usage_metadata.get('total_tokens', 'Unknown')
            except Exception:
                pass
            
        logger.info(f"LLM Call Completed [run_id: {run_id}] - Latency: {latency:.3f}s - Tokens: {tokens}")

    def on_llm_error(
        self, error: Exception, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any
    ) -> None:
        """Run when LLM errors."""
        end_time = time.time()
        start_time = self.start_times.pop(run_id, end_time)
        latency = end_time - start_time
        logger.error(f"LLM Call Failed [run_id: {run_id}] - Latency: {latency:.3f}s - Error: {error}")
