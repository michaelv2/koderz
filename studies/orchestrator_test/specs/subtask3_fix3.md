# Fix: DNS Baseline Analyzer Alert Creation

Fix `agentmon/analyzers/dns_baseline.py`. The analyze_event method creates Alert objects with WRONG field names.

Put `# agentmon/analyzers/dns_baseline.py` as the first line in the code block.

Rewrite the entire file.

## Alert dataclass fields (from agentmon.models.events)

Alert requires these fields:
- `id` (str) — use `str(uuid.uuid4())` to generate
- `timestamp` (datetime)
- `severity` (Severity enum)
- `title` (str) — short description
- `description` (str) — detailed description
- `source_event_type` (str) — use "dns"

Optional fields (default None):
- `client` (str)
- `domain` (str)
- `analyzer` (str)
- `llm_analysis` (str)
- `confidence` (float, default 0.0)
- `acknowledged` (bool, default False)

Alert does NOT have: `message`, `details`.

Import uuid at the top of the file: `import uuid`

## analyze_event(self, event: DNSEvent) -> list[Alert]

Steps in order:

1. Always update baseline: `self.store.update_domain_baseline(event.client, event.domain, event.timestamp)`
2. Skip if domain ends with any ignore_suffix → return []
3. Skip if domain in allowlist → return []
4. Check known-bad patterns → Alert(id=str(uuid.uuid4()), timestamp=event.timestamp, severity=Severity.HIGH, title="Known-bad pattern detected", description=f"{event.domain} matches known-bad pattern '{pattern}'", source_event_type="dns", client=event.client, domain=event.domain, analyzer="known_bad_pattern", confidence=0.95)
5. Check DGA via looks_like_dga(event.domain) → Alert with severity=MEDIUM, analyzer="dga_detection"
6. Check new domain (only if NOT learning_mode AND not store.is_domain_known): → Alert with severity=INFO, analyzer="new_domain", title="New domain observed", description=f"First-seen domain: {event.domain}"
7. Return collected alerts

## Dedup logic

Key = (event.client, event.domain, analyzer_name). Before appending any alert, check if same key was alerted within 300 seconds. If so, skip. Otherwise record timestamp.

## _matches_at_label_boundary (keep existing, it works)

## AnalyzerConfig (keep existing, it works)
