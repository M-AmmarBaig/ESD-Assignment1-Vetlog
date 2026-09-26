# V1 -> V2 Database Migration Plan

## 1. Goal
Migrate the underlying Vetlog database engine from SQLite to PostgreSQL to resolve concurrency locking bottlenecks (1-writer limit) affecting the webhook ingestion rate and chat latency under heavy load.

## 2. Infrastructure Changes (`docker-compose.yml`)
- Add a new `postgres` service using the `postgres:15-alpine` image.
- Configure persistent volume mounts (`postgres_data:/var/lib/postgresql/data`).
- Provide necessary environment variables (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`).

## 3. Configuration Changes
- `requirements.txt`: Add `psycopg2-binary` (for PostgreSQL synchronous connection) and `langgraph-checkpoint-postgres` (for AI thread memory).
- `.env`: Update `DATABASE_URL` from `sqlite:///data/vetlog.db` to `postgresql://vetlog:vetlog@postgres:5432/vetlogdb`.

## 4. Code Refactoring (The Difficult Part)
- `app/tools.py`: Massive refactor required. The AI tools (`execute_sql_query`, `generate_static_report`) currently hardcode the `sqlite3` Python library and bypass SQLAlchemy entirely. These must be rewritten to use Postgres connections. Additionally, `sqlglot` must be reconfigured to `read="postgres"`.
- `app/agent.py`: Replace `aiosqlite` and `AsyncSqliteSaver` with `psycopg` and `AsyncPostgresSaver` to persist LLM conversation threads correctly.
- `app/database.py` & `app/metrics.py`: Remove the logic calculating `raw_messages_db_size_bytes` based on SQLite file size.

## 5. Data Migration Strategy
- Create a new script `scripts/migrate_sqlite_to_postgres.py`.
- The script will connect to both the legacy SQLite `.db` file and the new Postgres container.
- It will perform a bulk `SELECT *` from `raw_messages`, `users`, `user_settings`, etc., and bulk insert them into Postgres.
- **CRITICAL:** The script must manually update/reset the PostgreSQL sequences (`setval`) after bulk insertion to prevent ID collision (e.g., trying to insert ID #1 when #1 was migrated from SQLite).

## 6. Risks
- LangGraph checkpoints (`checkpoints` and `writes` tables) have significantly different schemas in Postgres vs SQLite. We may need to abandon V1 chat threads and start fresh for V2, though the core WhatsApp message data will migrate perfectly.

## 7. Rollback Strategy
- Keep the `data/vetlog.db` file untouched.
- Create a backup of `docker-compose.yml` and `.env`.
- If rollback is needed, revert the `.env` string and restart the backend container.
