# Fix: baseline must be updated even for allowlisted domains

The test `test_baseline_always_updated` sends an allowlisted domain ("safe.example.com") and expects the baseline to be updated.

The fix: `update_domain_baseline` must be called BEFORE the allowlist/ignore check returns early. But you also need to know if the domain was previously known BEFORE updating baseline (for the new-domain check).

The correct order in `analyze_event`:
1. Check if domain is known BEFORE updating: `was_known = self.store.is_domain_known(event.client, event.domain)`
2. Update baseline: `self.store.update_domain_baseline(event.client, event.domain, event.timestamp)` — always, for every event
3. Skip ignored suffixes → return []
4. Skip allowlisted → return []
5. Check known-bad patterns → HIGH alert
6. Check DGA → MEDIUM alert
7. Check new domain: if `not self.config.learning_mode and not was_known` → INFO alert
8. Return alerts

Remember to put `# agentmon/analyzers/dns_baseline.py` as the first line.
Output the COMPLETE file.
