# Run A: Frontier Baseline Results

## Model
- **Model**: Claude Opus 4.6 (claude-opus-4-6)
- **Mode**: Single-session, direct implementation

## Metrics

| Metric | Value |
|--------|-------|
| **Wall-clock time** | 6m 30s |
| **API cost** | $2.13 |
| **Context usage** | ~46% |
| **Test pass rate** | 100/100 (100%) |
| **Iterations to pass** | 1 fix (block correlation default arg) |

## Implementation Summary

13 source files across 8 subpackages:

- `models/events.py` — Severity, DNSEvent (frozen), ConnectionEvent, Alert
- `storage/db.py` — DuckDB EventStore (schema, CRUD, baseline, cleanup)
- `collectors/syslog_receiver.py` — RFC 3164/5424 parsing, async TCP/UDP receiver
- `collectors/syslog_parsers.py` — PiholeParser, route_message
- `analyzers/entropy.py` — Shannon entropy, DGA detection (5-signal)
- `analyzers/dns_baseline.py` — Baseline learning/detection, known-bad patterns, dedup
- `llm/classifier.py` — Two-tier Ollama classification with caching
- `threat_feeds/__init__.py` — URL→domain extraction, subdomain matching
- `threat_intel/virustotal.py` — VirusTotal client with risk scoring
- `notifiers/slack.py` — Severity-filtered, color-coded Slack alerting
- `config.py` — TOML config loading + env var overrides
- `resolver.py` — Client IP → hostname resolution
- `cli.py` — Click CLI (listen, stats, alerts, baseline, cleanup, feeds)

## Notes

- All modules written in first pass; only 1 bug fix needed (mark_domain_blocked
  defaulted to 10s max_age which failed for syslog messages with historical timestamps;
  changed to no time filter when max_age_seconds not explicitly provided).
- No external references consulted beyond the acceptance test contract.
- Cost is well under the $20 budget ceiling estimated in SPEC.md.
