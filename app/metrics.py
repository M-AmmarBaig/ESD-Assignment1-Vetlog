"""
Central place for every Prometheus metric in the app.

Rule: define each metric ONCE here, import it everywhere it's needed.
Never call Counter()/Gauge()/Histogram() anywhere else - defining the
same metric name twice crashes the process (duplicate registration),
which happens easily with Uvicorn's --reload re-importing modules.
"""
from prometheus_client import Counter, Histogram, Gauge

# --- Hop 2: webhook ingest (app/routers/webhook.py) ---

webhook_batches_total = Counter(
    "webhook_batches_total",
    "Total batches received at the extension webhook",
)

webhook_messages_ingested_total = Counter(
    "webhook_messages_ingested_total",
    "New messages actually inserted (post-dedup)",
    ["chat_name"],
)

webhook_duplicates_skipped_total = Counter(
    "webhook_duplicates_skipped_total",
    "Messages skipped because they were already in the DB",
)

webhook_commit_failures_total = Counter(
    "webhook_commit_failures_total",
    "Times the DB commit for a batch failed and was rolled back",
)

webhook_timestamp_unparsed_total = Counter(
    "webhook_timestamp_unparsed_total",
    "Timestamps that didn't match a known format and were stored as-is",
)

webhook_batch_size = Histogram(
    "webhook_batch_size",
    "Number of messages per ingested batch",
    buckets=(1, 5, 10, 25, 50, 100, 250, 500),
)

# --- Hop 3: raw_messages persistence (app/database.py) ---

raw_messages_total = Gauge(
    "raw_messages_total",
    "Current row count in the raw_messages table",
)

raw_messages_last_captured_timestamp = Gauge(
    "raw_messages_last_captured_timestamp",
    "Unix timestamp of the most recently captured raw message",
)

raw_messages_db_size_bytes = Gauge(
    "raw_messages_db_size_bytes",
    "Size of the SQLite database file on disk",
)

# --- Hop 4: Chat request in (app/routers/chat.py) ---

chat_requests_total = Counter(
    "chat_requests_total", 
    "Total chat requests received", 
    ["stream"] # Labels: stream=true or stream=false
)

chat_request_duration_seconds = Histogram(
    "chat_request_duration_seconds", 
    "Duration of chat requests", 
    ["stream"],
    # Custom buckets (in seconds) tailored to LLM response times
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0] 
)

chat_active_sse_connections = Gauge(
    "chat_active_sse_connections",
    "Current number of active Server-Sent Events (SSE) connections"
)

# --- Hop 6: Agent invocation (FinOps / Usage) ---

agent_calls_total = Counter(
    "agent_calls_total",
    "Total agent invocations",
    ["provider"]
)

agent_tokens_total = Counter(
    "agent_tokens_total",
    "Cumulative tokens used",
    ["provider", "token_type"]
)

agent_cost_usd_total = Counter(
    "agent_cost_usd_total",
    "Cumulative cost in USD for LLM API usage",
    ["provider"]
)

# --- Hop 7: Tool execution (app/tools.py) ---

tool_calls_total = Counter(
    "tool_calls_total",
    "Total number of times a tool was called",
    ["tool_name"]
)

tool_call_duration_seconds = Histogram(
    "tool_call_duration_seconds",
    "Time taken to execute a tool",
    ["tool_name"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 15.0, 30.0]
)

agent_recursion_depth = Gauge(
    "agent_recursion_depth",
    "Current recursion/planning depth of the deepagents graph",
)

# --- Hop 9: Response out (app/routers/chat.py) ---

chat_errors_total = Counter(
    "chat_errors_total",
    "Failed chat requests",
    ["error_type"]
)

# --- Hop 10: Business metrics (Various) ---

reports_generated_total = Counter(
    "reports_generated_total",
    "Total number of reports generated",
    ["report_type"] # Labels: static or dynamic
)