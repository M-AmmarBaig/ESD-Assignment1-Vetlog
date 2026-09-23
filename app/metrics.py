"""
Central place for every Prometheus metric in the app.

Rule: define each metric ONCE here, import it everywhere it's needed.
Never call Counter()/Gauge()/Histogram() anywhere else - defining the
same metric name twice crashes the process (duplicate registration),
which happens easily with Uvicorn's --reload re-importing modules.
"""
from prometheus_client import Counter, Histogram

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