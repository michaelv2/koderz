## Project outline

Key question: is hierarchical orchestration viable?

Key unknowns:

  1. Can an orchestrator help coordinate smaller models for non-trivial coding tasks?
  2. What's the cost of knowledge transfer (spec generation, guidance, docs) between the orchestrator and workers?
  3. Does the total system (orchestrator + small workers) cost less than having the large model author everything directly?
  
The ultimate goal for Koderz is to assess whether we can build a system that uses a big frontier model (e.g. Opus 4.6) for planning and strategy (i.e. as an orchestrator), and for the actual work (i.e. code writing) to be handed to smaller models (either small frontier models, or free local models) for implementation.

The assessment metric becomes: how much cheaper is this for a realistic software project, and how much additional clock time does it require as a result (and is it even a net savings, because the expert knowledge of the large frontier model will need to be made "explicit" when communicating to the small models).

## Project selection criteria

The test project must satisfy all of the following:

- **Multi-file**: requires multiple modules/files with clear interfaces between them (not a single function or script)
- **Library usage**: involves at least one external library (to test knowledge-transfer for API surfaces the small model may not know well)
- **Objectively verifiable**: has acceptance criteria that can be checked by an automated test suite, not subjective judgment
- **Frontier-completable in ~1 hour**: Opus 4.6 should be able to finish it in a single session, keeping baseline cost under ~$20
- **Decomposable**: the work should naturally break into 3-5 independent subtasks that could be assigned to separate workers

The test suite is written upfront (before either run) and held constant across both approaches. Neither the frontier baseline nor the orchestrated run may modify the acceptance tests. This isolates the variable to implementation strategy, not test quality.

## Test project: agentmon clone

The test project is a clone of [agentmon](https://github.com/michaelv2/agentmon) — a DNS anomaly detection system that monitors Pi-hole syslog traffic, learns per-client baselines, and alerts on suspicious activity via Slack.

### Why agentmon

- **Multi-file with clear module boundaries**: syslog receiver, DuckDB storage, detection engine, LLM classifier, Slack alerting, threat feed ingestion, configuration — 6+ modules with well-defined interfaces
- **Library diversity**: DuckDB (less common, tests knowledge transfer), asyncio syslog protocol, httpx, ollama SDK, Click CLI — not all well-represented in training data
- **Subtle integration requirements**: per-client state survives DHCP reassignment, block correlation across separate syslog messages within a time window, label-boundary pattern matching (must NOT match "ec2-" when checking for "c2-"), two-tier LLM triage with confidence-based escalation, alert deduplication with TTL cache
- **Mixed difficulty**: some subtasks are straightforward (Slack webhook, TOML config loading) and some require precise specification (DGA detection heuristics, baseline learning vs. detection modes, syslog RFC parsing)
- **Decomposable into 5 subtasks** with clear dependency graph (see below)

### Subtask decomposition

```
Subtask 1: Data models + storage layer
  - DNSEvent, ConnectionEvent, Alert, Severity dataclasses
  - DuckDB EventStore (schema creation, insert, query, baseline upsert, retention cleanup)
  - No external dependencies beyond duckdb
  - Foundation for all other subtasks

Subtask 2: Syslog receiver + parsers
  - Async TCP/UDP syslog server (asyncio protocols)
  - RFC 3164 / 5424 message parsing
  - Pi-hole dnsmasq parser (query, block with client, block without client)
  - OpenWRT firewall/conntrack parser
  - Message routing
  - Depends on: Subtask 1 (DNSEvent/ConnectionEvent models)

Subtask 3: Detection engine
  - Shannon entropy calculation
  - DGA detection (multi-signal: entropy + consonant ratio + long alphanumeric + alternating pattern + no vowels)
  - Known-bad pattern matching at label boundaries
  - DNS baseline analyzer (learning mode vs detection mode, alert generation)
  - Alert deduplication (TTL cache)
  - Depends on: Subtask 1 (EventStore for baseline queries)

Subtask 4: LLM classifier + threat intelligence
  - Two-tier Ollama classification (triage model -> escalation model)
  - Domain sanitization (prompt injection defense)
  - VirusTotal client with negative caching
  - Threat feed manager (URLhaus, Feodo Tracker download + domain extraction)
  - Classification result caching (24h TTL)
  - Depends on: Subtask 1 (Alert model for severity downgrade)

Subtask 5: CLI + alerting + configuration
  - Click CLI (listen, collect, stats, alerts, baseline, cleanup, feeds commands)
  - TOML configuration loading with env var overrides
  - Client IP -> hostname resolver (reverse DNS, suffix stripping, explicit mappings)
  - Async Slack webhook notifier (severity filtering, color-coded formatting)
  - Integration: wiring the listen pipeline (syslog -> storage -> analysis -> alerting)
  - Depends on: Subtasks 1-4
```

### Execution plan (2 parallel workers)

```
Phase 1 (sequential):  Subtask 1 — models + storage (foundation)
Phase 2 (parallel):    Subtask 2 (syslog) + Subtask 3 (detection) — on 2 workers
Phase 3 (parallel):    Subtask 4 (LLM/threat intel) + Subtask 5 (CLI/alerting) — on 2 workers
                        (Subtask 5 integration tests will run after 4 completes)
```

### Scope boundaries

The clone implements the core detection pipeline. The following features from the original are **excluded** to keep scope within the ~1 hour frontier baseline target:

- Parental controls (policies/, category classifier, device manager, time rules)
- Device activity analyzer (activity-hours anomaly detection)
- Pi-hole pull-mode collector (SSH/paramiko direct DB access)
- OpenWRT connection event processing (firewall/conntrack parsing)
- ProcessNetworkEvent handling
- Systemd service configuration

The clone **includes**: syslog receiver (TCP/UDP), dnsmasq DNS parsing, DuckDB storage with baseline tracking, entropy/DGA detection, known-bad pattern matching with label-boundary semantics, DNS baseline analysis (learning + detection modes), two-tier LLM classification with VirusTotal enrichment, threat feed integration, alert deduplication, Slack alerting, TOML configuration, client hostname resolution, Click CLI, and data retention/cleanup.

## Proposed workflow

### Run A: Frontier baseline

- Implement the project entirely using Opus 4.6 in a single session
- Record: wall-clock time, total input/output tokens, API cost, test pass rate
- This establishes the accuracy ceiling and the cost to beat

### Run B: Orchestrated (planner + workers)

- **Planning phase**: Opus 4.6 reads the project spec and decomposes it into subtasks, producing a work package per subtask (spec, interface contracts, relevant API docs/examples, expected test behavior)
- **Execution phase**: Small models (gpt-oss:20b-128k, nemotron-3-nano:30b) implement each subtask, running subtask-level tests as they go
- **Review checkpoints**: After each subtask completes (or after N failed attempts), Opus reviews the output and provides corrective guidance if needed
- **Integration**: Once all subtasks pass individually, run the full acceptance suite

### Escalation policy

When a small model is stuck (same error for 3+ consecutive iterations, or zero progress after exhausting its iteration budget), the orchestrator must choose from a defined escalation ladder:

1. **Re-spec**: Rewrite the subtask spec with more detail, worked examples, or explicit API usage patterns (costs orchestrator tokens, resets the worker's iteration count)
2. **Decompose further**: Break the failing subtask into smaller pieces (costs orchestrator tokens + coordination overhead)
3. **Take over**: The orchestrator implements the subtask directly (costs frontier tokens, counts against the orchestrated run's budget)

Every escalation event is logged with its trigger, cost, and outcome. The fraction of work completed by escalation (especially "take over") is a key result — if the orchestrator must implement >50% of the code itself, the architecture is not viable.

## Hardware and parallelism

**Available compute:**
- Ollama host (192.168.1.74): 2x NVIDIA RTX 3090 — can serve 2 concurrent model instances

This gives **2 confirmed simultaneous local workers**. The orchestrated approach can exploit this parallelism: if the project decomposes into independent subtasks, workers run concurrently at zero marginal cost. The frontier baseline (Opus via API) is inherently sequential.

Wall-time comparison should account for this: if the orchestrated approach takes 2x longer per-task but runs 2 tasks in parallel, effective wall time is comparable. The spec's "order of magnitude slower = failure" criterion applies to total wall-clock time including parallelism, not per-task time.

## Measurement criteria

### Primary metrics

| Metric | What it measures |
|--------|-----------------|
| **Total cost** | API spend (orchestrator + workers). Local model cost = $0. |
| **Orchestration overhead** | Tokens spent on planning, specs, reviews, and escalation — tracked separately from worker code-generation tokens. Measures the "making knowledge explicit" tax. |
| **Wall-clock time** | End-to-end including planning, execution (with parallelism), and integration. |
| **Test pass rate** | Fraction of acceptance tests passing. Must reach 100% for the run to count as successful. |
| **Escalation rate** | Fraction of subtasks requiring re-spec, further decomposition, or orchestrator takeover. |

### Success criteria

- The orchestrated approach must pass 100% of acceptance tests (same bar as frontier baseline)
- Total cost must be equal to or less than the frontier baseline
- Wall-clock time within 10x of the frontier baseline (accounting for parallelism)
- Escalation takeover rate below 50% of subtasks

### Frontier curve

Establish a cost vs. wall-time frontier by varying:
- Worker model (gpt-oss:20b-128k, nemotron-3-nano:30b, gpt-5-nano)
- Spec richness (minimal spec vs. detailed spec with examples and API docs)
- Review frequency (every subtask vs. only on failure vs. never)
- Parallelism (1, 2, or 3 concurrent workers)

Methodology changes from prior Koderz studies (prompt tuning, temperature variation, model ensembles, cascade strategies) can be applied to shift points along this frontier.

### Output quality

Beyond test-passing, the final codebase from each run will be evaluated on a brief qualitative review: reasonable file organization, no obvious anti-patterns, no hardcoded workarounds that bypass the problem. This is not a scored metric but a sanity check — if the orchestrated approach produces working but unmaintainable code, that is noted as a limitation.