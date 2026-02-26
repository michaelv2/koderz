from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

import duckdb

from agentmon.models.events import DNSEvent, Alert, Severity


class EventStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: duckdb.DuckDBPyConnection | None = None

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
        """Create tables: dns_events, alerts, domain_baseline."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        schema_sql = """
        CREATE TABLE IF NOT EXISTS dns_events (
            id VARCHAR PRIMARY KEY,
            timestamp TIMESTAMPTZ,
            client VARCHAR,
            domain VARCHAR,
            domain_tld VARCHAR,
            domain_registered VARCHAR,
            query_type VARCHAR,
            blocked BOOLEAN
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id VARCHAR PRIMARY KEY,
            timestamp TIMESTAMPTZ,
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
        );

        CREATE TABLE IF NOT EXISTS domain_baseline (
            client VARCHAR,
            domain VARCHAR,
            query_count INTEGER,
            first_seen TIMESTAMPTZ,
            last_seen TIMESTAMPTZ,
            PRIMARY KEY (client, domain)
        );
        """
        self.conn.execute(schema_sql)

    def insert_dns_event(self, event: DNSEvent) -> str:
        """Insert a DNS event with derived TLD and registered domain."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        event_id = str(uuid.uuid4())
        parts = event.domain.split(".")
        domain_tld = parts[-1] if parts else ""
        domain_registered = ".".join(parts[-2:]) if len(parts) >= 2 else event.domain

        sql = """
        INSERT INTO dns_events (
            id, timestamp, client, domain, domain_tld, domain_registered,
            query_type, blocked
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(
            sql,
            (
                event_id,
                event.timestamp,
                event.client,
                event.domain,
                domain_tld,
                domain_registered,
                event.query_type,
                event.blocked,
            ),
        )
        return event_id

    def insert_dns_events_batch(self, events: List[DNSEvent]) -> int:
        """Insert multiple DNS events. Return count inserted."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        if not events:
            return 0

        sql = """
        INSERT INTO dns_events (
            id, timestamp, client, domain, domain_tld, domain_registered,
            query_type, blocked
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        batch = []
        for event in events:
            event_id = str(uuid.uuid4())
            parts = event.domain.split(".")
            domain_tld = parts[-1] if parts else ""
            domain_registered = ".".join(parts[-2:]) if len(parts) >= 2 else event.domain
            batch.append(
                (
                    event_id,
                    event.timestamp,
                    event.client,
                    event.domain,
                    domain_tld,
                    domain_registered,
                    event.query_type,
                    event.blocked,
                )
            )
        self.conn.executemany(sql, batch)
        return len(events)

    def update_domain_baseline(self, client: str, domain: str, timestamp: datetime):
        """Upsert domain_baseline."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        sql = """
        INSERT INTO domain_baseline (client, domain, query_count, first_seen, last_seen)
        VALUES (?, ?, 1, ?, ?)
        ON CONFLICT(client, domain) DO UPDATE SET
            query_count = domain_baseline.query_count + 1,
            last_seen = excluded.last_seen
        """
        self.conn.execute(sql, (client, domain, timestamp, timestamp))

    def is_domain_known(self, client: str, domain: str) -> bool:
        """Return True if (client, domain) exists in domain_baseline."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        sql = """
        SELECT 1 FROM domain_baseline
        WHERE client = ? AND domain = ?
        LIMIT 1
        """
        result = self.conn.execute(sql, (client, domain)).fetchone()
        return result is not None

    def insert_alert(self, alert: Alert) -> str:
        """Insert an alert. Return the alert ID."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        alert_id = alert.id or str(uuid.uuid4())
        sql = """
        INSERT INTO alerts (
            id, timestamp, severity, title, description, source_event_type,
            client, domain, analyzer, confidence, llm_analysis, acknowledged
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(
            sql,
            (
                alert_id,
                alert.timestamp,
                alert.severity.value,
                alert.title,
                alert.description,
                alert.source_event_type,
                alert.client,
                alert.domain,
                alert.analyzer,
                alert.confidence,
                alert.llm_analysis,
                alert.acknowledged,
            ),
        )
        return alert_id

    def get_unacknowledged_alerts(
        self, min_severity: str = "info", limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Return unacknowledged alerts with severity >= min_severity."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        severity_order = {
            "info": 0,
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4,
        }
        min_val = severity_order.get(min_severity.lower(), 0)

        sql = """
        SELECT id, timestamp, severity, title, description, source_event_type,
               client, domain, analyzer, confidence
        FROM alerts
        WHERE acknowledged = FALSE
        LIMIT ?
        """
        rows = self.conn.execute(sql, (limit,)).fetchall()
        alerts = []
        for row in rows:
            sev_val = severity_order.get(row[2].lower(), 0)
            if sev_val >= min_val:
                alerts.append(
                    {
                        "id": row[0],
                        "timestamp": row[1],
                        "severity": row[2],
                        "title": row[3],
                        "description": row[4],
                        "source_event_type": row[5],
                        "client": row[6],
                        "domain": row[7],
                        "analyzer": row[8],
                        "confidence": row[9],
                    }
                )
        return alerts

    def mark_domain_blocked(self, domain: str, max_age_seconds: int = 5) -> bool:
        """Find recent unblocked dns_event for domain and set blocked=True."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        now = datetime.utcnow()
        threshold = now - timedelta(seconds=max_age_seconds)

        sql_find = """
        SELECT id FROM dns_events
        WHERE domain = ? AND blocked = FALSE AND timestamp >= ?
        ORDER BY timestamp DESC
        LIMIT 1
        """
        row = self.conn.execute(sql_find, (domain, threshold)).fetchone()
        if not row:
            return False

        event_id = row[0]
        sql_update = "UPDATE dns_events SET blocked = TRUE WHERE id = ?"
        self.conn.execute(sql_update, (event_id,))
        return True

    def cleanup_old_data(self, dns_days: int = 30, alerts_days: int = 30) -> Dict[str, int]:
        """Delete old dns_events and alerts. Return counts deleted."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        now = datetime.utcnow()
        dns_threshold = now - timedelta(days=dns_days)
        alerts_threshold = now - timedelta(days=alerts_days)

        dns_count_before = self.conn.execute(
            "SELECT COUNT(*) FROM dns_events WHERE timestamp < ?", (dns_threshold,)
        ).fetchone()[0]
        alerts_count_before = self.conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE timestamp < ?", (alerts_threshold,)
        ).fetchone()[0]

        self.conn.execute("DELETE FROM dns_events WHERE timestamp < ?", (dns_threshold,))
        self.conn.execute("DELETE FROM alerts WHERE timestamp < ?", (alerts_threshold,))

        return {
            "dns_events": dns_count_before,
            "alerts": alerts_count_before,
        }

    def get_client_stats(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Return per-client stats for events within the last N hours."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        now = datetime.utcnow()
        threshold = now - timedelta(hours=hours)

        sql = """
        SELECT
            client,
            COUNT(*) AS query_count,
            COUNT(DISTINCT domain) AS unique_domains,
            SUM(CASE WHEN blocked = TRUE THEN 1 ELSE 0 END) AS blocked_count
        FROM dns_events
        WHERE timestamp >= ?
        GROUP BY client
        """
        rows = self.conn.execute(sql, (threshold,)).fetchall()
        stats = []
        for row in rows:
            stats.append(
                {
                    "client": row[0],
                    "query_count": row[1],
                    "unique_domains": row[2],
                    "blocked_count": row[3],
                }
            )
        return stats
