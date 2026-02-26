import click


@click.group()
def main():
    """agentmon - DNS anomaly detection system."""
    pass


@main.command()
@click.option("--port", type=int, default=514, help="Syslog listen port")
@click.option("--protocol", type=click.Choice(["tcp", "udp"]), default="tcp", help="Syslog protocol")
@click.option("--config", "config_path", type=click.Path(), default=None, help="Config file path")
@click.option("--learning", is_flag=True, default=False, help="Enable learning mode")
@click.option("--llm", is_flag=True, default=False, help="Enable LLM classification")
def listen(port, protocol, config_path, learning, llm):
    """Listen for syslog messages and analyze DNS traffic."""
    click.echo(f"Listening on {protocol}:{port}")


@main.command()
@click.option("--hours", type=int, default=24, help="Time window in hours")
@click.option("--db", "db_path", type=click.Path(), default=None, help="Database path")
def stats(hours, db_path):
    """Show client query statistics."""
    click.echo("Stats")


@main.command()
@click.option("--severity", type=click.Choice(["info", "low", "medium", "high", "critical"]), default="info")
@click.option("--limit", type=int, default=50, help="Max alerts to show")
@click.option("--db", "db_path", type=click.Path(), default=None, help="Database path")
def alerts(severity, limit, db_path):
    """Show recent alerts."""
    click.echo("Alerts")


@main.command()
@click.option("--mode", type=click.Choice(["start", "stop", "status"]), default="status")
@click.option("--db", "db_path", type=click.Path(), default=None, help="Database path")
def baseline(mode, db_path):
    """Manage baseline learning."""
    click.echo(f"Baseline {mode}")


@main.command()
@click.option("--dns-days", type=int, default=30, help="DNS retention days")
@click.option("--alerts-days", type=int, default=30, help="Alerts retention days")
@click.option("--db", "db_path", type=click.Path(), default=None, help="Database path")
def cleanup(dns_days, alerts_days, db_path):
    """Clean up old data."""
    click.echo("Cleanup")


@main.command()
@click.option("--update", is_flag=True, help="Download latest feeds")
@click.option("--cache-dir", type=click.Path(), default=None, help="Feed cache directory")
def feeds(update, cache_dir):
    """Manage threat feeds."""
    click.echo("Feeds")
