# Subtask 1: Data Models + DuckDB Storage Layer

Implement the foundation data models and storage layer for a DNS anomaly detection system called `agentmon`.

## File Structure

You must produce exactly these files (put `# path/to/file.py` as the first line in each code block):

- `agentmon/__init__.py` (empty)
- `agentmon/models/__init__.py` (empty)
- `agentmon/models/events.py`
- `agentmon/storage/__init__.py` (empty)
- `agentmon/storage/db.py`

## Module: `agentmon/models/events.py`

### `Severity` (enum.Enum)
- 5 levels: INFO, LOW, MEDIUM, HIGH, CRITICAL
- String values: `"info"`, `"low"`, `"medium"`, `"high"`, `"critical"`

### `DNSEvent` (frozen dataclass)
- Fields: `timestamp` (datetime), `client` (str), `domain` (str), `query_type` (str), `blocked` (bool)
- Method `domain_parts() -> list[str]`: splits `self.domain` on `"."` and returns the list of labels
- Must be immutable (frozen=True) — assigning to any field raises AttributeError or TypeError

### `ConnectionEvent` (dataclass)
- Fields: `timestamp` (datetime), `client` (str), `src_port` (int), `dst_ip` (str), `dst_port` (int), `protocol` (str)
- Default `bytes_sent` = 0, `bytes_received` = 0

### `Alert` (dataclass, NOT frozen)
- Fields: `id` (str), `timestamp` (datetime), `severity` (Severity), `title` (str), `description` (str), `source_event_type` (str)
- Optional fields with default empty string `""`: `client`, `domain`, `analyzer`
- `llm_analysis` (str | None, default None)
- `confidence` (float, default 0.0)
- `acknowledged` (bool, default False)
- Severity MUST be mutable (for LLM downgrade)

## Module: `agentmon/storage/db.py`

### `EventStore`
- `__init__(self, db_path: str)`: stores path, sets `self.conn = None`
- `connect(self)`: opens DuckDB connection, creates tables (see schema below)
- `close(self)`: closes connection
- Context manager support: `__enter__` calls connect and returns self, `__exit__` calls close

#### Schema (created in `connect`):
- Table `dns_events`: columns `id` (VARCHAR, primary key — use UUID), `timestamp` (TIMESTAMP), `client` (VARCHAR), `domain` (VARCHAR), `domain_tld` (VARCHAR), `domain_registered` (VARCHAR), `query_type` (VARCHAR), `blocked` (BOOLEAN)
- Table `alerts`: columns `id` (VARCHAR, primary key), `timestamp` (TIMESTAMP), `severity` (VARCHAR), `title` (VARCHAR), `description` (VARCHAR), `source_event_type` (VARCHAR), `client` (VARCHAR), `domain` (VARCHAR), `analyzer` (VARCHAR), `confidence` (DOUBLE), `acknowledged` (BOOLEAN), `llm_analysis` (VARCHAR)
- Table `domain_baseline`: columns `client` (VARCHAR), `domain` (VARCHAR), `first_seen` (TIMESTAMP), `last_seen` (TIMESTAMP), `query_count` (INTEGER) — composite primary key on (client, domain)

#### Methods:

**`insert_dns_event(self, event: DNSEvent) -> str`**
- Generates a UUID id
- Derives `domain_tld` = last label of domain (e.g. "com" from "api.github.com")
- Derives `domain_registered` = last 2 labels joined by "." (e.g. "github.com")
- Inserts into dns_events, returns the id

**`insert_dns_events_batch(self, events: list[DNSEvent]) -> int`**
- Inserts all events, returns count inserted

**`update_domain_baseline(self, client: str, domain: str, timestamp: datetime)`**
- If (client, domain) row exists: increment query_count, update last_seen
- If not: insert new row with query_count=1, first_seen=timestamp, last_seen=timestamp
- Use a SELECT to check existence, then INSERT or UPDATE accordingly

**`is_domain_known(self, client: str, domain: str) -> bool`**
- Returns True if (client, domain) exists in domain_baseline

**`insert_alert(self, alert: Alert) -> str`**
- Inserts alert into alerts table, returns the alert.id

**`get_unacknowledged_alerts(self, min_severity: str, limit: int) -> list[dict]`**
- Returns alerts where acknowledged=False and severity >= min_severity
- Severity ordering: info < low < medium < high < critical
- Returns list of dicts with keys matching column names
- Order by timestamp DESC, limit results

**`mark_domain_blocked(self, domain: str, max_age_seconds: int = 5) -> bool`**
- Find the most recent dns_events row for this domain that is NOT blocked and was inserted within max_age_seconds of NOW
- If found: UPDATE that row to blocked=True, return True
- If not found: return False
- Compare timestamps using current_timestamp (DuckDB function) minus interval

**`cleanup_old_data(self, dns_days: int, alerts_days: int) -> dict`**
- DELETE dns_events older than dns_days
- DELETE alerts older than alerts_days
- Return dict like `{"dns_events": <count_deleted>, "alerts": <count_deleted>}`
- To count deleted rows: query COUNT before and after, or use a SELECT COUNT first

**`get_client_stats(self, hours: int) -> list[dict]`**
- For events within the last `hours` hours, GROUP BY client
- Return list of dicts with keys: `client`, `query_count`, `unique_domains`
- `query_count` = total events, `unique_domains` = COUNT(DISTINCT domain)
