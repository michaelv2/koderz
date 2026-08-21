from __future__ import annotations

import asyncio

import click


@click.group()
def main():
    """agentmon - DNS anomaly detection system."""
    pass


@main.command()
@click.option("--port", default=514, help="Syslog listen port")
@click.option("--protocol", default="tcp", type=click.Choice(["tcp", "udp"]))
@click.option("--config", "config_path", default=None, help="Path to config file")
@click.option("--learning/--no-learning", default=False, help="Enable learning mode")
@click.option("--llm/--no-llm", default=False, help="Enable LLM classification")
@click.option("--db", default=None, help="Path to database file")
def listen(port, protocol, config_path, learning, llm, db):
    """Start the syslog listener and detection pipeline."""
    from agentmon.analyzers.dns_baseline import AnalyzerConfig, DNSBaselineAnalyzer
    from agentmon.collectors.syslog_parsers import route_message
    from agentmon.collectors.syslog_receiver import SyslogConfig, SyslogReceiver
    from agentmon.config import load_config
    from agentmon.storage.db import EventStore

    config = load_config(config_path or "agentmon.toml")

    db_path = db or config.get("database", {}).get("path", "/tmp/agentmon.db")
    store = EventStore(db_path)
    store.connect()

    analyzer_cfg = AnalyzerConfig(
        known_bad_patterns=config.get("analyzer", {}).get("known_bad_patterns", ["c2-", "beacon"]),
        allowlist=set(config.get("analyzer", {}).get("allowlist", [])),
        ignore_suffixes=config.get("analyzer", {}).get("ignore_suffixes", [".local", ".lan", ".arpa"]),
        learning_mode=learning,
        llm_enabled=llm,
    )
    analyzer = DNSBaselineAnalyzer(store, analyzer_cfg)

    async def handle(msg):
        dns, conn = route_message(msg)
        if dns and dns.client != "__BLOCK_NOTIFICATION__":
            store.insert_dns_event(dns)
            alerts = analyzer.analyze_event(dns)
            for alert in alerts:
                store.insert_alert(alert)
        elif dns and dns.client == "__BLOCK_NOTIFICATION__":
            store.mark_domain_blocked(dns.domain)

    syslog_config = SyslogConfig(port=port, protocol=protocol)
    receiver = SyslogReceiver(syslog_config, handle)

    async def run():
        await receiver.start()
        click.echo(f"Listening on {protocol}://0.0.0.0:{port}")
        try:
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
        finally:
            await receiver.stop()
            store.close()

    asyncio.run(run())


@main.command()
@click.option("--hours", default=24, help="Time range in hours")
@click.option("--db", default=None, help="Path to database file")
def stats(hours, db):
    """Show client query statistics."""
    from agentmon.storage.db import EventStore

    db_path = db or "/tmp/agentmon.db"
    with EventStore(db_path) as store:
        results = store.get_client_stats(hours=hours)
        for s in results:
            click.echo(
                f"{s['client']}: {s['query_count']} queries, "
                f"{s['unique_domains']} unique domains, "
                f"{s['blocked_count']} blocked"
            )


@main.command()
@click.option("--severity", default="info", help="Minimum severity to show")
@click.option("--limit", default=50, help="Max alerts to show")
@click.option("--db", default=None, help="Path to database file")
def alerts(severity, limit, db):
    """Show unacknowledged alerts."""
    from agentmon.storage.db import EventStore

    db_path = db or "/tmp/agentmon.db"
    with EventStore(db_path) as store:
        results = store.get_unacknowledged_alerts(min_severity=severity, limit=limit)
        for a in results:
            click.echo(
                f"[{a['severity']}] {a['title']} - {a['domain']} "
                f"(client: {a['client']}, confidence: {a['confidence']:.0%})"
            )


@main.command()
@click.option("--enable/--disable", default=True, help="Enable/disable learning mode")
@click.option("--db", default=None, help="Path to database file")
def baseline(enable, db):
    """Manage baseline learning mode."""
    if enable:
        click.echo("Learning mode enabled. New domains will be added to baseline without alerting.")
    else:
        click.echo("Learning mode disabled. New domains will generate alerts.")


@main.command()
@click.option("--dns-days", default=30, help="Retain DNS events for N days")
@click.option("--alerts-days", default=30, help="Retain alerts for N days")
@click.option("--db", default=None, help="Path to database file")
def cleanup(dns_days, alerts_days, db):
    """Clean up old data from the database."""
    from agentmon.storage.db import EventStore

    db_path = db or "/tmp/agentmon.db"
    with EventStore(db_path) as store:
        counts = store.cleanup_old_data(dns_days=dns_days, alerts_days=alerts_days)
        click.echo(
            f"Cleaned up {counts['dns_events']} DNS events and "
            f"{counts['alerts']} alerts"
        )


@main.command()
@click.option("--update/--no-update", default=False, help="Download fresh feeds")
def feeds(update):
    """Manage threat intelligence feeds."""
    from agentmon.threat_feeds import ThreatFeedManager

    manager = ThreatFeedManager()
    domains = manager.get_malicious_domains()
    click.echo(f"Loaded {len(domains)} malicious domains from threat feeds")
    if update:
        click.echo("Updating feeds...")
        import asyncio
        asyncio.run(manager.update_feeds())
        click.echo("Feeds updated.")


if __name__ == "__main__":
    main()
