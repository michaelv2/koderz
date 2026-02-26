# Subtask 1: Data Models + Storage Layer

You must implement TWO Python files. Output them as TWO separate fenced code blocks, clearly labeled.

## File 1: `agentmon/models/events.py`

Implement these exact classes:

### `Severity` (enum.Enum)
- Values: INFO="info", LOW="low", MEDIUM="medium", HIGH="high", CRITICAL="critical"

### `DNSEvent` (frozen dataclass)
Fields:
- `timestamp`: datetime
- `client`: str
- `domain`: str
- `query_type`: str (default "A")
- `blocked`: bool (default False)

Methods:
- `domain_parts() -> list[str]`: splits domain by "." and returns list of labels
  - Example: `"sub.example.co.uk"` -> `["sub", "example", "co", "uk"]`

CRITICAL: This dataclass MUST be frozen (immutable). Use `@dataclass(frozen=True)`.

### `ConnectionEvent` (frozen dataclass)
Fields:
- `timestamp`: datetime
- `client`: str
- `src_port`: int
- `dst_ip`: str
- `dst_port`: int
- `protocol`: str
- `bytes_sent`: int (default 0)
- `bytes_received`: int (default 0)

### `Alert` (regular mutable dataclass, NOT frozen)
Fields:
- `id`: str
- `timestamp`: datetime
- `severity`: Severity
- `title`: str
- `description`: str
- `source_event_type`: str
- `client`: str (default None)
- `domain`: str (default None)
- `analyzer`: str (default None)
- `confidence`: float (default 0.0)
- `llm_analysis`: str (default None)
- `acknowledged`: bool (default False)

Alert must be MUTABLE (not frozen) because tests modify severity after creation.

## File 2: `agentmon/storage/db.py`

Implement the `EventStore` class using DuckDB.

```python
import duckdb
import uuid
from datetime import datetime, timezone, timedelta
from agentmon.models.events import DNSEvent, Alert, Severity
```

### `EventStore` class

Constructor: `__init__(self, db_path: str)`
- Store db_path, conn=None

### Methods:

#### `connect(self)`
Create DuckDB connection and create these tables:

```sql
CREATE TABLE IF NOT EXISTS dns_events (
    id VARCHAR PRIMARY KEY,
    timestamp TIMESTAMP,
    client VARCHAR,
    domain VARCHAR,
    domain_tld VARCHAR,
    domain_registered VARCHAR,
    query_type VARCHAR,
    blocked BOOLEAN
)

CREATE TABLE IF NOT EXISTS alerts (
    id VARCHAR PRIMARY KEY,
    timestamp TIMESTAMP,
    severity VARCHAR,
    title VARCHAR,
    description VARCHAR,
    source_event_type VARCHAR,
    client VARCHAR,
    domain VARCHAR,
    analyzer VARCHAR,
    confidence DOUBLE,
    llm_analysis VARCHAR,
    acknowledged BOOLEAN
)

CREATE TABLE IF NOT EXISTS domain_baseline (
    client VARCHAR,
    domain VARCHAR,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    query_count INTEGER DEFAULT 1,
    PRIMARY KEY (client, domain)
)
```

#### `close(self)`
Close the DuckDB connection.

#### Context manager: `__enter__` returns self (calls connect()), `__exit__` calls close()

#### `insert_dns_event(self, event: DNSEvent) -> str`
- Generate UUID for id
- Extract domain_tld: last part after final "." (e.g., "com" from "api.github.com")
- Extract domain_registered: last two parts joined by "." (e.g., "github.com" from "api.github.com")
- Insert into dns_events table
- Return the id

#### `insert_dns_events_batch(self, events: list[DNSEvent]) -> int`
- Insert all events using a loop
- Return count of inserted events

#### `update_domain_baseline(self, client: str, domain: str, timestamp: datetime)`
- Try to INSERT into domain_baseline
- If entry already exists (client+domain), UPDATE: increment query_count, update last_seen
- Use INSERT ... ON CONFLICT pattern or try/except

#### `is_domain_known(self, client: str, domain: str) -> bool`
- Query domain_baseline for this client+domain pair
- Return True if found, False otherwise

#### `insert_alert(self, alert: Alert) -> str`
- Insert alert into alerts table
- Return alert.id

#### `get_unacknowledged_alerts(self, min_severity: str = "info", limit: int = 50) -> list[dict]`
- Query alerts where acknowledged=False
- Filter by severity: define ordering info=0, low=1, medium=2, high=3, critical=4
- Return list of dicts with keys: id, timestamp, severity, title, description, client, domain, analyzer, confidence

#### `mark_domain_blocked(self, domain: str, max_age_seconds: int = None) -> bool`
- If max_age_seconds is None, default to 10
- Find most recent dns_events row with this domain, blocked=False, within max_age_seconds of now
- If found, UPDATE that row to set blocked=True, return True
- If not found, return False

#### `cleanup_old_data(self, dns_days: int = 30, alerts_days: int = 30) -> dict[str, int]`
- DELETE dns_events older than dns_days
- DELETE alerts older than alerts_days
- Return dict like {"dns_events": N, "alerts": M} with counts of deleted rows

#### `get_client_stats(self, hours: int = 24) -> list[dict]`
- Query dns_events from last `hours` hours
- GROUP BY client
- Return list of dicts with: client, query_count, unique_domains (COUNT DISTINCT domain)

## Important Notes
- Use `from __future__ import annotations` at the top of both files
- Use `import enum` for Severity
- All Optional fields in Alert should use `= None` defaults
- The `mark_domain_blocked` default for max_age_seconds: if None is passed, use 10 seconds
- For severity filtering in get_unacknowledged_alerts, map string severity names to numeric values for comparison
- Use `datetime.now(timezone.utc)` for current time comparisons
