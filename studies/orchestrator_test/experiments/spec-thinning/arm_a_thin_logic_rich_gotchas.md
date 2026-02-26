# Subtask 1: Data Models + DuckDB Storage Layer

Implement data models and a DuckDB storage layer for a DNS anomaly detection system called `agentmon`.

Put `# path/to/file.py` as the first line in each code block.

## Files to produce

- `agentmon/__init__.py` (empty)
- `agentmon/models/__init__.py` (empty)
- `agentmon/models/events.py` — Severity enum, DNSEvent (frozen dataclass), ConnectionEvent, Alert dataclasses
- `agentmon/storage/__init__.py` (empty)
- `agentmon/storage/db.py` — EventStore class with DuckDB backend

## What to build

`events.py`: A Severity enum (INFO through CRITICAL with string values), a frozen DNSEvent dataclass (timestamp, client, domain, query_type, blocked) with a domain_parts() method that splits on ".", a ConnectionEvent dataclass (timestamp, client, src_port, dst_ip, dst_port, protocol, bytes_sent=0, bytes_received=0), and an Alert dataclass (id, timestamp, severity, title, description, source_event_type, plus optional client/domain/analyzer/llm_analysis, confidence=0.0, acknowledged=False).

`db.py`: An EventStore class with connect/close/context-manager, three tables (dns_events, alerts, domain_baseline), and methods for CRUD operations, baseline tracking, block correlation, cleanup, and client stats.

## Gotchas — read these carefully

1. **DuckDB does not support `?` placeholders inside INTERVAL expressions.** Use Python f-strings to interpolate integer values directly into the SQL for interval parts (e.g. `f"INTERVAL '{hours} hours'"` not `INTERVAL ? HOUR`). This affects `mark_domain_blocked`, `cleanup_old_data`, and `get_client_stats`.

2. **DuckDB `.rowcount` returns -1 for DELETE statements.** In `cleanup_old_data`, use `SELECT COUNT(*)` before each DELETE to get the count of rows that will be removed, then DELETE.

3. **`mark_domain_blocked(domain, max_age_seconds=5)`** must compare against `current_timestamp` (DuckDB built-in) minus the interval. Find the most recent unblocked row for that domain within the time window, UPDATE it to blocked=True.

4. **`update_domain_baseline`** must use INSERT ... ON CONFLICT DO UPDATE (upsert), not separate SELECT + INSERT/UPDATE. DuckDB supports this syntax.

5. **Alert.severity must be mutable** (not frozen) — the LLM classifier needs to downgrade severity later.

6. **DNSEvent must be frozen** (immutable) — assignment to fields must raise an error.

7. **`insert_dns_event`** must derive `domain_tld` (last label) and `domain_registered` (last 2 labels joined by ".") from the domain string before inserting.

8. **`get_unacknowledged_alerts(min_severity, limit)`** must filter by severity rank (info=1 < low=2 < medium=3 < high=4 < critical=5), return list of dicts with column-name keys, ordered by timestamp DESC.
