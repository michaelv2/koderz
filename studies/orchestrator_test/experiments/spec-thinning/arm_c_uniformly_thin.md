# Subtask 1: Data Models + DuckDB Storage Layer

Implement data models and a DuckDB storage layer for a DNS anomaly detection system called `agentmon`.

Put `# path/to/file.py` as the first line in each code block.

## Files to produce

- `agentmon/__init__.py` (empty)
- `agentmon/models/__init__.py` (empty)
- `agentmon/models/events.py` — Severity enum, DNSEvent, ConnectionEvent, Alert dataclasses
- `agentmon/storage/__init__.py` (empty)
- `agentmon/storage/db.py` — EventStore class with DuckDB backend

## events.py

- `Severity` enum with 5 levels (INFO, LOW, MEDIUM, HIGH, CRITICAL) with lowercase string values
- `DNSEvent` frozen dataclass: timestamp, client, domain, query_type, blocked. Has `domain_parts()` method.
- `ConnectionEvent` dataclass: timestamp, client, src_port, dst_ip, dst_port, protocol, bytes_sent=0, bytes_received=0
- `Alert` mutable dataclass: id, timestamp, severity, title, description, source_event_type, plus optional client/domain/analyzer/llm_analysis, confidence=0.0, acknowledged=False

## db.py

`EventStore` class backed by DuckDB with:
- `__init__(db_path)`, `connect()`, `close()`, context manager support
- Three tables: `dns_events`, `alerts`, `domain_baseline`
- `insert_dns_event(event)` — returns UUID id
- `insert_dns_events_batch(events)` — returns count
- `update_domain_baseline(client, domain, timestamp)` — upsert
- `is_domain_known(client, domain)` — bool
- `insert_alert(alert)` — returns id
- `get_unacknowledged_alerts(min_severity, limit)` — filtered by severity rank, returns list of dicts
- `mark_domain_blocked(domain, max_age_seconds=5)` — correlate recent query with block
- `cleanup_old_data(dns_days, alerts_days)` — returns dict with counts deleted
- `get_client_stats(hours)` — per-client query_count and unique_domains
