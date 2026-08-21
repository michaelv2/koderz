from __future__ import annotations


import click


@click.group()
def main():
    """Agentmon - DNS anomaly detection system."""
    pass


@main.command()
@click.option("--port", default=514, help="Syslog listen port")
@click.option("--protocol", default="udp", type=click.Choice(["tcp", "udp"]))
@click.option("--config", "config_path", default=None, help="Config file path")
@click.option("--learning", is_flag=True, help="Enable learning mode")
@click.option("--llm", is_flag=True, help="Enable LLM classification")
@click.option("--bind", default="0.0.0.0", help="Bind address")
def listen(port, protocol, config_path, learning, llm, bind):
    """Listen for syslog messages and analyze DNS traffic."""
    click.echo(f"Listening on {bind}:{port} ({protocol})")
    click.echo(f"Learning mode: {learning}, LLM: {llm}")


@main.command()
@click.option("--config", "config_path", default=None, help="Config file path")
@click.option("--hours", default=24, help="Stats window in hours")
def stats(config_path, hours):
    """Display client statistics."""
    click.echo(f"Stats for last {hours} hours")


@main.command()
@click.option("--config", "config_path", default=None, help="Config file path")
@click.option("--severity", default="info", help="Minimum severity filter")
@click.option("--limit", default=50, help="Max alerts to show")
def alerts(config_path, severity, limit):
    """Display recent alerts."""
    click.echo(f"Alerts (min severity: {severity}, limit: {limit})")


@main.command()
@click.option("--config", "config_path", default=None, help="Config file path")
@click.option("--client", default=None, help="Filter by client")
def baseline(config_path, client):
    """Display or manage domain baselines."""
    click.echo("Baseline management")


@main.command()
@click.option("--config", "config_path", default=None, help="Config file path")
@click.option("--dns-days", default=30, help="DNS retention days")
@click.option("--alerts-days", default=90, help="Alerts retention days")
def cleanup(config_path, dns_days, alerts_days):
    """Clean up old data."""
    click.echo(f"Cleanup: DNS {dns_days}d, Alerts {alerts_days}d")


@main.command()
@click.option("--config", "config_path", default=None, help="Config file path")
@click.option("--update", is_flag=True, help="Download fresh feeds")
def feeds(config_path, update):
    """Manage threat intelligence feeds."""
    click.echo("Threat feeds management")


if __name__ == "__main__":
    main()
