from __future__ import annotations

import datetime
import uuid
from typing import Dict, List, Tuple

import duckdb

from agentmon.models.events import Alert, DNSEvent, Severity


class EventStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: duckdb.DuckDBPyConnection | None = None

    # --------------------- Connection handling --------------------- #
    def connect(self) -> None:
        if self.conn is not None:
            return
        self.conn = duckdb.connect(self.db_path)
        self._create_tables()

    def _create_tables(self) -> None:
        assert self.conn is not None
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
                query_count INTEGER,
                PRIMARY KEY (client, domain)
            );
            """
        )
        self.conn.commit()

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self) -> "EventStore":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # --------------------- DNS event handling --------------------- #
    def insert_dns_event(self, event: DNSEvent) -> str:
        assert self.conn is not None
        domain_parts = event.domain.split(".")
        domain_tld = domain_parts[-1] if domain_parts else ""
        domain_registered = (
            ".".join(domain_parts[-2:]) if len(domain_parts) >= 2 else domain_parts[0]
        )
        event_id = str(uuid.uuid4())
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
        self.conn.commit()
        return event_id

    def insert_dns_events_batch(self, events: List[DNSEvent]) -> int:
        assert self.conn is not None
        if not events:
            return 0
        data: List[Tuple] = []
        for event in events:
            domain_parts = event.domain.split(".")
            domain_tld = domain_parts[-1] if domain_parts else ""
            domain_registered = (
                ".".join(domain_parts[-2:]) if len(domain_parts) >= 2 else domain_parts[0]
            )
            event_id = str(uuid.uuid4())
            data.append(
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
        self.conn.executemany(
            """
            INSERT INTO dns_events
            (id, timestamp, client, domain, domain_tld, domain_registered, query_type, blocked)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            data,
        )
        self.conn.commit()
        return len(events)

    def update_domain_baseline(self, client: str, domain: str, timestamp: datetime.datetime) -> None:
        assert self.conn is not None
        self.conn.execute(
            """
            INSERT INTO domain_baseline
            (client, domain, first_seen, last_seen, query_count)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT (client, domain) DO UPDATE
            SET query_count = domain_baseline.query_count + 1,
                last_seen = EXCLUDED.last_seen
            """,
            (client, domain, timestamp, timestamp),
        )
        self.conn.commit()

    def is_domain_known(self, client: str, domain: str) -> bool:
        assert self.conn is not None
        result = self.conn.execute(
            """
            SELECT 1 FROM domain_baseline
            WHERE client = ? AND domain = ?
            LIMIT 1
            """,
            (client, domain),
        ).fetchone()
        return result is not None

    # --------------------- Alert handling --------------------- #
    def insert_alert(self, alert: Alert) -> str:
        assert self.conn is not None
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
        self.conn.commit()
        return alert.id

    def get_unacknowledged_alerts(self, min_severity: str, limit: int) -> List[Dict]:
        assert self.conn is not None
        severity_order = {
            "info": 0,
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4,
        }
        min_rank = severity_order.get(min_severity.lower(), 0)
        result = self.conn.execute(
            """
            SELECT * FROM alerts
            WHERE acknowledged = FALSE
            """,
        )
        columns = [desc[0] for desc in result.description]
        rows = result.fetchall()
        alerts = [dict(zip(columns, row)) for row in rows]
        filtered = [
            a
            for a in alerts
            if severity_order.get(str(a["severity"]).lower(), 0) >= min_rank
        ]
        return filtered[:limit]

    # --------------------- Domain blocking --------------------- #
    def mark_domain_blocked(self, domain: str, max_age_seconds: int = None) -> bool:
        assert self.conn is not None
        if max_age_seconds is not None:
            now = datetime.datetime.now(datetime.timezone.utc)
            threshold = now - datetime.timedelta(seconds=max_age_seconds)
            row = self.conn.execute(
                """
                SELECT id FROM dns_events
                WHERE domain = ? AND blocked = FALSE AND timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (domain, threshold),
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
            UPDATE dns_events
            SET blocked = TRUE
            WHERE id = ?
            """,
            (event_id,),
        )
        self.conn.commit()
        return True

    # --------------------- Cleanup --------------------- #
    def cleanup_old_data(self, dns_days: int, alerts_days: int) -> Dict[str, int]:
        assert self.conn is not None
        now = datetime.datetime.now(datetime.timezone.utc)
        dns_threshold = now - datetime.timedelta(days=dns_days)
        alerts_threshold = now - datetime.timedelta(days=alerts_days)

        dns_count = self.conn.execute(
            "SELECT COUNT(*) FROM dns_events WHERE timestamp < ?",
            (dns_threshold,),
        ).fetchone()[0]
        self.conn.execute(
            "DELETE FROM dns_events WHERE timestamp < ?",
            (dns_threshold,),
        )

        alerts_count = self.conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE timestamp < ?",
            (alerts_threshold,),
        ).fetchone()[0]
        self.conn.execute(
            "DELETE FROM alerts WHERE timestamp < ?",
            (alerts_threshold,),
        )

        self.conn.commit()
        return {"dns_events": dns_count, "alerts": alerts_count}

    # --------------------- Client stats --------------------- #
    def get_client_stats(self, hours: int) -> List[Dict]:
        assert self.conn is not None
        now = datetime.datetime.now(datetime.timezone.utc)
        threshold = now - datetime.timedelta(hours=hours)
        rows = self.conn.execute(
            """
            SELECT client,
                   COUNT(*) AS query_count,
                   COUNT(DISTINCT domain) AS unique_domains
            FROM dns_events
            WHERE timestamp >= ?
            GROUP BY client
            """,
            (threshold,),
        ).fetchall()
        columns = ["client", "query_count", "unique_domains"]
        return [dict(zip(columns, row)) for row in rows]
