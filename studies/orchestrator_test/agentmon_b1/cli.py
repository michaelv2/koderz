from __future__ import annotations
import click


@click.group()
def main():
    """Agentmon - DNS anomaly detection system."""
    pass


@main.command()
@click.option("--port", default=514, type=int, help="Syslog port")
@click.option("--protocol", default="tcp", type=click.Choice(["tcp", "udp"]))
@click.option("--config", "config_path", default=None, help="Config file path")
@click.option("--learning/--no-learning", default=False)
@click.option("--llm/--no-llm", default=False)
@click.option("--db", default=None, help="Database path")
def listen(port, protocol, config_path, learning, llm, db):
    """Start syslog listener and detection pipeline."""
    click.echo(f"Starting listener on {protocol}://0.0.0.0:{port}")


@main.command()
@click.option("--hours", default=24, type=int)
@click.option("--db", default=None)
def stats(hours, db):
    """Show client query statistics."""
    click.echo(f"Stats for last {hours} hours")


@main.command()
@click.option("--severity", default="info")
@click.option("--limit", default=50, type=int)
@click.option("--db", default=None)
def alerts(severity, limit, db):
    """Show unacknowledged alerts."""
    click.echo(f"Alerts (min severity: {severity})")


@main.command()
@click.option("--enable/--disable", default=None)
@click.option("--db", default=None)
def baseline(enable, db):
    """Manage baseline learning mode."""
    click.echo("Baseline management")


@main.command()
@click.option("--dns-days", default=30, type=int)
@click.option("--alerts-days", default=30, type=int)
@click.option("--db", default=None)
def cleanup(dns_days, alerts_days, db):
    """Clean up old data."""
    click.echo(f"Cleaning up data older than {dns_days}/{alerts_days} days")


@main.command()
@click.option("--update/--no-update", default=False)
def feeds(update):
    """Manage threat intelligence feeds."""
    click.echo("Threat feed management")
