# Subtask 1: Data Models + DuckDB Storage Layer

You must implement TWO Python files. Output them clearly separated.

## File 1: `agentmon/models/events.py`

Implement these exact classes:

### `Severity` (str enum with 5 levels)
```python
from enum import Enum

class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
```

### `DNSEvent` (frozen dataclass — immutable)
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class DNSEvent:
    timestamp: datetime
    client: str
    domain: str
    query_type: str
    blocked: bool

    def domain_parts(self) -> list[str]:
        """Split domain into labels. 'sub.example.co.uk' -> ['sub', 'example', 'co', 'uk']"""
        return self.domain.split(".")
```

### `ConnectionEvent` (frozen dataclass)
```python
@dataclass(frozen=True)
class ConnectionEvent:
    timestamp: datetime
    client: str
    src_port: int
    dst_ip: str
    dst_port: int
    protocol: str
    bytes_sent: int = 0
    bytes_received: int = 0
```

### `Alert` (mutable dataclass — NOT frozen, severity must be changeable)
```python
@dataclass
class Alert:
    id: str
    timestamp: datetime
    severity: Severity
    title: str
    description: str
    source_event_type: str
    client: str = ""
    domain: str = ""
    analyzer: str = ""
    confidence: float = 0.0
    llm_analysis: str | None = None
    acknowledged: bool = False
```

**CRITICAL**: `DNSEvent` and `ConnectionEvent` MUST be `frozen=True`. `Alert` MUST NOT be frozen (severity can be modified later for LLM downgrade).

## File 2: `agentmon/storage/db.py`

Implement `EventStore` class using DuckDB. Here is the full contract:

```python
import duckdb
import uuid
from datetime import datetime, timedelta, timezone
from agentmon.models.events import DNSEvent, Alert, Severity

class EventStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Connect to DuckDB and create schema."""
        self.conn = duckdb.connect(self.db_path)
        self._create_schema()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()

    def _create_schema(self):
        """Create tables: dns_events, alerts, domain_baseline.
        
        dns_events columns: id VARCHAR PRIMARY KEY, timestamp TIMESTAMPTZ, client VARCHAR,
            domain VARCHAR, domain_tld VARCHAR, domain_registered VARCHAR, 
            query_type VARCHAR, blocked BOOLEAN
            
        alerts columns: id VARCHAR PRIMARY KEY, timestamp TIMESTAMPTZ, severity VARCHAR,
            title VARCHAR, description VARCHAR, source_event_type VARCHAR,
            client VARCHAR, domain VARCHAR, analyzer VARCHAR, confidence DOUBLE,
            llm_analysis VARCHAR, acknowledged BOOLEAN
            
        domain_baseline columns: client VARCHAR, domain VARCHAR, query_count INTEGER,
            first_seen TIMESTAMPTZ, last_seen TIMESTAMPTZ,
            PRIMARY KEY (client, domain)
        """
        pass  # YOU IMPLEMENT THIS

    def insert_dns_event(self, event: DNSEvent) -> str:
        """Insert a DNS event. Derive domain_tld and domain_registered from domain.
        
        domain_tld = last label (e.g., 'com' from 'api.github.com')
        domain_registered = last two labels (e.g., 'github.com' from 'api.github.com')
        
        Returns: the generated event ID (UUID string)
        """
        pass

    def insert_dns_events_batch(self, events: list) -> int:
        """Insert multiple DNS events. Return count inserted."""
        pass

    def update_domain_baseline(self, client: str, domain: str, timestamp: datetime):
        """Upsert domain_baseline: create with query_count=1 on first call,
        increment query_count on subsequent calls. Update last_seen."""
        pass

    def is_domain_known(self, client: str, domain: str) -> bool:
        """Return True if (client, domain) exists in domain_baseline."""
        pass

    def insert_alert(self, alert: Alert) -> str:
        """Insert an alert. Return the alert ID."""
        pass

    def get_unacknowledged_alerts(self, min_severity: str = "info", limit: int = 100) -> list:
        """Return unacknowledged alerts with severity >= min_severity.
        
        Severity ordering for filtering: info=0, low=1, medium=2, high=3, critical=4
        
        Return list of dicts with keys: id, timestamp, severity, title, description,
        source_event_type, client, domain, analyzer, confidence.
        """
        pass

    def mark_domain_blocked(self, domain: str, max_age_seconds: int = 5) -> bool:
        """Find the most recent unblocked dns_event with this domain
        within max_age_seconds of current UTC time, and set its blocked=True.
        
        Return True if a matching event was found and updated, False otherwise.
        """
        pass

    def cleanup_old_data(self, dns_days: int = 30, alerts_days: int = 30) -> dict:
        """Delete dns_events older than dns_days and alerts older than alerts_days.
        Return dict: {'dns_events': count_deleted, 'alerts': count_deleted}"""
        pass

    def get_client_stats(self, hours: int = 24) -> list:
        """Return per-client stats for events within the last N hours.
        Each dict: {'client': str, 'query_count': int, 'unique_domains': int, 'blocked_count': int}"""
        pass
```

### DuckDB-specific notes:
- Use `duckdb.connect(db_path)` to open
- DuckDB supports standard SQL. It does NOT support `gen_random_uuid()` — generate UUIDs in Python with `str(uuid.uuid4())`
- For UPSERT use: `INSERT INTO ... ON CONFLICT(col1, col2) DO UPDATE SET ...`
- `information_schema.tables` works for checking table existence
- Timestamps: use `TIMESTAMPTZ` type. Pass Python datetime objects directly in parameterized queries
- Boolean: use `BOOLEAN` type
- For counting deletes: execute DELETE and use `fetchone()` to get count, OR count before and after
- DuckDB `.execute()` takes SQL string and optional list of parameters using `?` placeholders
- DuckDB returns changes via: `conn.execute("DELETE FROM t WHERE ...").fetchone()` won't return count directly. Instead: count first with SELECT COUNT, then DELETE. Or use a trick like `SELECT COUNT(*) FROM (DELETE FROM ... RETURNING *)`.

Actually the simplest approach for cleanup_old_data: count before delete, delete, count after, diff is the deleted count.

### What the tests check:
1. After connect(), `information_schema.tables` shows dns_events, alerts, domain_baseline
2. insert_dns_event stores with derived domain_tld='com', domain_registered='github.com' for 'api.github.com'
3. insert_dns_events_batch returns count=10 for 10 events
4. update_domain_baseline: first call sets query_count=1, second call sets query_count=2
5. is_domain_known returns False before, True after update_domain_baseline
6. insert_alert + get_unacknowledged_alerts: alerts with severity >= min_severity are returned as dicts with 'domain' key
7. mark_domain_blocked: finds recent (within max_age_seconds) unblocked event for domain, sets blocked=True, returns True. Returns False if event too old.
8. cleanup_old_data: deletes events older than N days, counts deleted in returned dict with key 'dns_events'
9. get_client_stats: returns list of dicts with 'client', 'query_count', 'unique_domains' keys
10. Context manager (__enter__/__exit__) works: `with EventStore(path) as store: store.conn.execute("SELECT 1")`

Write COMPLETE, RUNNABLE code for both files. No stubs, no TODOs. Wrap each file in ```python blocks with the filename as a comment on the first line.
