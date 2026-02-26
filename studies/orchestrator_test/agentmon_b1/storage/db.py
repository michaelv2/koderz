from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict

import duckdb

from agentmon.models.events import DNSEvent, Alert, Severity


class EventStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: duckdb.DuckDBPyConnection | None = None

    def connect(self) -> None:
        if self.conn is None:
            self.conn = duckdb.connect(self.db_path)
            self._create_tables()

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self) -> "EventStore":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _create_tables(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dns_events (
                id VARCHAR PRIMARY KEY,
                timestamp TIMESTAMP,
                client VARCHAR,
                domain VARCHAR,
                domain_tld VARCHAR,
                domain_registered VARCHAR,
                query_type VARCHAR,
                blocked BOOLEAN
            );
            """
        )
        self.conn.execute(
            """
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
            );
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS domain_baseline (
                client VARCHAR,
                domain VARCHAR,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                query_count INTEGER DEFAULT 1,
                PRIMARY KEY (client, domain)
            );
            """
        )

    def insert_dns_event(self, event: DNSEvent) -> str:
        event_id = str(uuid.uuid4())
        domain_parts = event.domain.split(".")
        domain_tld = domain_parts[-1] if domain_parts else ""
        domain_registered = ".".join(domain_parts[-2:]) if len(domain_parts) >= 2 else event.domain

        self.conn.execute(
            """
            INSERT INTO dns_events
            (id, timestamp, client, domain, domain_tld, domain_registered, query_type, blocked)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
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
        count = 0
        for event in events:
            self.insert_dns_event(event)
            count += 1
        return count

    def update_domain_baseline(self, client: str, domain: str, timestamp: datetime) -> None:
        self.conn.execute(
            """
            INSERT INTO domain_baseline (client, domain, first_seen, last_seen, query_count)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT (client, domain) DO UPDATE SET
                query_count = domain_baseline.query_count + 1,
                last_seen = ?
            """,
            (client, domain, timestamp, timestamp, timestamp),
        )

    def is_domain_known(self, client: str, domain: str) -> bool:
        res = self.conn.execute(
            """
            SELECT 1 FROM domain_baseline
            WHERE client = ? AND domain = ?
            """,
            (client, domain),
        ).fetchone()
        return res is not None

    def insert_alert(self, alert: Alert) -> str:
        self.conn.execute(
            """
            INSERT INTO alerts
            (id, timestamp, severity, title, description, source_event_type,
             client, domain, analyzer, confidence, llm_analysis, acknowledged)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                alert.id,
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
        return alert.id

    def get_unacknowledged_alerts(self, min_severity: str = "info", limit: int = 50) -> List[Dict]:
        severity_order = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
        min_val = severity_order.get(min_severity.lower(), 0)

        rows = self.conn.execute(
            """
            SELECT id, timestamp, severity, title, description, client, domain,
                   analyzer, confidence
            FROM alerts
            WHERE acknowledged = FALSE
            """,
        ).fetchall()

        alerts = []
        for row in rows[:limit]:
            sev_val = severity_order.get(row[2].lower(), 0)
            if sev_val >= min_val:
                alerts.append(
                    {
                        "id": row[0],
                        "timestamp": row[1],
                        "severity": row[2],
                        "title": row[3],
                        "description": row[4],
                        "client": row[5],
                        "domain": row[6],
                        "analyzer": row[7],
                        "confidence": row[8],
                    }
                )
        return alerts

    def mark_domain_blocked(self, domain: str, max_age_seconds: int | None = None) -> bool:
        if max_age_seconds is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(seconds=max_age_seconds)
            row = self.conn.execute(
                """
                SELECT id FROM dns_events
                WHERE domain = ? AND blocked = FALSE AND timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (domain, cutoff),
            ).fetchone()
        else:
            row = self.conn.execute(
                """
                SELECT id FROM dns_events
                WHERE domain = ? AND blocked = FALSE
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (domain,),
            ).fetchone()

        if row is None:
            return False

        event_id = row[0]
        self.conn.execute(
            """
            UPDATE dns_events SET blocked = TRUE WHERE id = ?
            """,
            (event_id,),
        )
        return True

    def cleanup_old_data(self, dns_days: int = 30, alerts_days: int = 30) -> Dict[str, int]:
        now = datetime.now(timezone.utc)
        dns_cutoff = now - timedelta(days=dns_days)
        alerts_cutoff = now - timedelta(days=alerts_days)

        dns_deleted = self.conn.execute(
            """
            DELETE FROM dns_events
            WHERE timestamp < ?
            RETURNING *
            """,
            (dns_cutoff,),
        ).fetchall()
        alerts_deleted = self.conn.execute(
            """
            DELETE FROM alerts
            WHERE timestamp < ?
            RETURNING *
            """,
            (alerts_cutoff,),
        ).fetchall()

        return {"dns_events": len(dns_deleted), "alerts": len(alerts_deleted)}

    def get_client_stats(self, hours: int = 24) -> List[Dict]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        rows = self.conn.execute(
            """
            SELECT client,
                   COUNT(*) AS query_count,
                   COUNT(DISTINCT domain) AS unique_domains
            FROM dns_events
            WHERE timestamp >= ?
            GROUP BY client
            """,
            (cutoff,),
        ).fetchall()

        return [
            {"client": r[0], "query_count": r[1], "unique_domains": r[2]} for r in rows
        ]
