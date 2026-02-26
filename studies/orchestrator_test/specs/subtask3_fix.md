# Fix: dns_baseline.py Alert construction and new-domain detection

## Problem 1: Alert constructor uses wrong kwargs
The Alert dataclass fields are: `id`, `timestamp`, `severity`, `title`, `description`, `source_event_type`, plus optional `client`, `domain`, `analyzer`, `confidence`, `llm_analysis`, `acknowledged`.

There is NO `message` field. Every Alert creation must include at minimum: `id` (use `str(uuid.uuid4())`), `timestamp` (use `event.timestamp`), `severity`, `title`, `description`, `source_event_type` (use `"dns"`).

Fix every `Alert(...)` call to use the correct fields. Import uuid at the top.

## Problem 2: New domain INFO alert missing
When NOT in learning_mode and the domain is NOT known (i.e. `not self.store.is_domain_known(event.client, event.domain)`), you must create an Alert with `severity=Severity.INFO`, `analyzer="new_domain"`, `title="New domain"`, `description=f"First-seen domain: {event.domain}"`, `source_event_type="dns"`, `client=event.client`, `domain=event.domain`.

Note: `update_domain_baseline` is called FIRST (step 1) which means the domain IS now known. The check for new domain must happen BEFORE updating baseline OR you should check `is_domain_known` BEFORE calling `update_domain_baseline`. Move the baseline update to the END or check new-domain status before the update.

Remember to put `# agentmon/analyzers/dns_baseline.py` as the first line of the code block.
Output the COMPLETE file.
