# Fix: New Domain Detection Order

Fix the ordering bug in `agentmon/analyzers/dns_baseline.py` in the `analyze_event` method.

Put `# agentmon/analyzers/dns_baseline.py` as the first line in the code block. Rewrite the entire file.

## The Bug

The current code calls `self.store.update_domain_baseline()` BEFORE checking `self.store.is_domain_known()`. This means by the time we check if the domain is new, we've already added it to the baseline, so it always appears "known".

## The Fix

Check `is_domain_known` BEFORE calling `update_domain_baseline`. The correct order in analyze_event:

1. Check `is_known = self.store.is_domain_known(event.client, event.domain)` — BEFORE updating
2. Call `self.store.update_domain_baseline(event.client, event.domain, event.timestamp)` — always update, even for allowlisted
3. Skip if domain ends with any ignore_suffix → return []
4. Skip if domain in allowlist → return []
5. Check known-bad patterns → create HIGH alert
6. Check DGA → create MEDIUM alert
7. If NOT learning_mode AND NOT is_known → create INFO alert for new domain
8. Return alerts

Everything else stays the same — keep the AnalyzerConfig dataclass, _matches_at_label_boundary staticmethod, dedup logic, all imports.
