# Vetlog AI - Known Issues & Architecture Backlog

This document tracks known architectural limitations for the backend AI agent.

_Last audited: 2026-09-23, against commit `e3201cd` (2026-08-12)._

---

### 4. Context Window Management (Memory Compaction) — PARTIALLY ADDRESSED, new regression introduced
- **GitHub Issue:** [#3](https://github.com/faraz18001/Vetlog-AI/issues/3)
- **What changed:** on 2026-07-17 (`4d96323`, `1651033`) the agent was migrated from `langgraph.prebuilt.create_react_agent` to `deepagents.create_deep_agent`. `deepagents` has its own internal planning/sub-agent harness (`HarnessProfile`, `write_todos`), which helps avoid dumping the entire raw history into one call the way plain `create_react_agent` does.
- **However:** no explicit summarization node, sliding window, or `RemoveMessage` pruning exists anywhere in `app/agent.py`. The `deepagents` harness changes *how* context is organized, but doesn't cap or compact it — so the original risk (long conversations eventually exceeding the model's context window) is still architecturally present, just pushed further out.
- **New issue introduced by the same migration:** the commit that made the switch is literally titled "deep agents replacement is working very well but the token cost is way too high from 20k to 68k per query" (`4d96323`). A follow-up the next day (`7e6f0cc`, "Fix token leaks and optimize SQL tools") trimmed the system prompt and tightened SQL tool-call guidance, but there's no benchmark or log confirming token cost actually came back down to the pre-migration baseline — worth measuring rather than assuming it's fixed.
- **Net assessment:** don't close this issue yet. Reframe it as "no hard cap on context growth for long chats" + "confirm per-query token cost after the deepagents migration," rather than the original framing.

### 8. Two divergent LLM-config code paths (security inconsistency)
- The DB-backed settings path (`app/routers/settings.py`) encrypts API keys at rest (`app/crypto.py`), while a legacy path (`app/config_manager.py` + `app/routers/config.py`, `update_env_file`) still writes API keys to `.env` in plaintext.
- If the legacy route is still reachable, it's an inconsistent security posture for the same kind of secret. Needs confirming whether `routers/config.py` is still mounted/reachable from the frontend before deciding if this matters in practice.
