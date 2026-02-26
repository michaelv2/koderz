# Subtask 1: Data Models + DuckDB Storage Layer

Implement two files for a DNS anomaly detection system called `agentmon`.

## File 1: `agentmon/models/events.py`

### Severity (enum.Enum)
- 5 levels with string values: `INFO="info"`, `LOW="low"`, `MEDIUM="medium"`, `HIGH="high"`, `CRITICAL="critical"`

### DNSEvent (frozen dataclass)
- Fields: `timestamp` (datetime), `client` (str), `domain` (str), `query_type` (str), `blocked` (bool)
- Method `domain_parts() -> list[str]`: splits `self.domain` on "." and returns the list of labels
- Must be immutable (frozen=True). Setting an attribute after creation must raise AttributeError or TypeError.

### ConnectionEvent (frozen dataclass)
- Fields: `timestamp` (datetime), `client` (str), `src_port` (int), `dst_ip` (str), `dst_port` (int), `protocol` (str), `bytes_sent` (int, default=0), `bytes_received` (int, default=0)

### Alert (regular dataclass, NOT frozen)
- Fields: `id` (str), `timestamp` (datetime), `severity` (Severity), `title` (str), `description` (str), `source_event_type` (str), `client` (str, default=""), `domain` (str, default=""), `analyzer` (str, default=""), `confidence` (float, default=0.0), `llm_analysis` (optional str, default=None), `acknowledged` (bool, default=False)
- Must be mutable — in particular, `severity` must be reassignable after creation.

## File 2: `agentmon/storage/db.py`

### EventStore
- Constructor: `__init__(self, db_path: str)` — stores the path, does NOT connect yet.
- `connect()` — opens DuckDB connection to `self.db_path`, creates tables:
  - `dns_events`: columns `id` (VARCHAR primary key, use UUID), `timestamp` (TIMESTAMP), `client` (VARCHAR), `domain` (VARCHAR), `domain_tld` (VARCHAR), `domain_registered` (VARCHAR), `query_type` (VARCHAR), `blocked` (BOOLEAN)
  - `alerts`: columns `id` (VARCHAR primary key), `timestamp` (TIMESTAMP), `severity` (VARCHAR), `title` (VARCHAR), `description` (VARCHAR), `source_event_type` (VARCHAR), `client` (VARCHAR), `domain` (VARCHAR), `analyzer` (VARCHAR), `confidence` (DOUBLE), `llm_analysis` (VARCHAR), `acknowledged` (BOOLEAN)
  - `domain_baseline`: columns `client` (VARCHAR), `domain` (VARCHAR), `first_seen` (TIMESTAMP), `last_seen` (TIMESTAMP), `query_count` (INTEGER), plus PRIMARY KEY on (client, domain)
- `close()` — closes the DuckDB connection
- Context manager support: `__enter__` calls connect and returns self, `__exit__` calls close.
- `insert_dns_event(event: DNSEvent) -> str` — inserts the event, deriving:
  - `domain_tld`: last label of the domain (e.g., "com" from "api.github.com")
  - `domain_registered`: last two labels (e.g., "github.com" from "api.github.com")
  - `id`: generate a UUID string
  - Returns the generated id.
- `insert_dns_events_batch(events: list[DNSEvent]) -> int` — batch inserts, returns count.
- `update_domain_baseline(client: str, domain: str, timestamp: datetime)` — upserts into domain_baseline:
  - If no row for (client, domain): INSERT with query_count=1, first_seen=timestamp, last_seen=timestamp
  - If row exists: INCREMENT query_count, UPDATE last_seen=timestamp
- `is_domain_known(client: str, domain: str) -> bool` — returns True if a baseline row exists for (client, domain).
- `insert_alert(alert: Alert) -> str` — inserts the alert, returns alert.id.
- `get_unacknowledged_alerts(min_severity: str, limit: int) -> list[dict]` — returns alerts where `acknowledged=False` and severity >= min_severity. Return as list of dicts with keys matching column names. For severity comparison, use ordering: info < low < medium < high < critical.
- `mark_domain_blocked(domain: str, max_age_seconds: int = 5) -> bool` — finds the most recent dns_event for this domain where blocked=False AND timestamp is within max_age_seconds of now. If found, set blocked=True and return True. Otherwise return False. Time comparison must work correctly with the stored timestamps.
- `cleanup_old_data(dns_days: int, alerts_days: int) -> dict` — deletes events/alerts older than the specified days. Returns dict with keys "dns_events" and "alerts" containing counts of deleted rows.
- `get_client_stats(hours: int) -> list[dict]` — returns per-client stats for events within the last N hours. Each dict has keys: `client`, `query_count`, `unique_domains`.

Dependencies: `duckdb`, `uuid`, `datetime` (all available).

Write ONLY these two files. Output them as two separate fenced code blocks, each preceded by a comment with the file path.
