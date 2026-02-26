# Fix: DNSBaselineAnalyzer Alert Creation and Baseline Update

The `dns_baseline.py` file has two bugs:

## Bug 1: Wrong Alert fields

Alert does NOT have a `message` field. The Alert dataclass has `title` and `description` fields. Every place where `message=...` is used must be changed to use `title` and `description` instead, and must also include `id` and `source_event_type`.

Correct way to create an Alert:
```
Alert(
    id=str(uuid.uuid4()),
    timestamp=event.timestamp,
    severity=Severity.HIGH,
    title="Known-bad pattern match",
    description=f"Domain {event.domain} matches known-bad pattern: {pattern}",
    source_event_type="dns",
    client=event.client,
    domain=event.domain,
    analyzer="known_bad_pattern",
    confidence=0.95,
)
```

Required imports: `import uuid` and `from agentmon.models.events import Alert, Severity, DNSEvent`

## Bug 2: Baseline not updated for allowlisted domains

The spec says "Always update baseline FIRST — even for allowlisted domains." The current code checks is_domain_known first but returns [] before calling update_domain_baseline for allowlisted and ignored-suffix domains.

The correct order in `analyze_event` is:
1. Call `self.store.update_domain_baseline(event.client, event.domain, event.timestamp)` FIRST — before any checks
2. Then check ignore_suffixes → return []
3. Then check allowlist → return []
4. Then check known-bad patterns, DGA, new domain

Rewrite the entire `agentmon/analyzers/dns_baseline.py` file. Put `# agentmon/analyzers/dns_baseline.py` as the first line in the code block.
