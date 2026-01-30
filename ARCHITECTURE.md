# Koderz Architecture

Technical architecture and design decisions for the Koderz multi-model swarm framework.

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         User CLI                            │
│                    (koderz command)                         │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   ExperimentOrchestrator                    │
│  - Coordinates experiment workflow                          │
│  - Manages iteration loop                                   │
│  - Triggers checkpoints                                     │
│  - Collects cost analytics                                  │
└─┬──────────┬──────────┬──────────┬────────────────────────┬─┘
  │          │          │          │                        │
  ▼          ▼          ▼          ▼                        ▼
┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌────────────────────┐
│Cortex│  │Local │  │Fronti│  │Human │  │    CostAnalyzer    │
│Client│  │Model │  │ er   │  │ Eval │  │                    │
└──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘  └────────────────────┘
   │         │         │         │
   ▼         ▼         ▼         ▼
┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
│ MCP  │  │Ollama│  │Claude│  │Tests │
│Server│  │ API  │  │ API  │  │ .py  │
└──────┘  └──────┘  └──────┘  └──────┘
```

## Core Components

### 1. ExperimentOrchestrator

**Purpose**: Main control loop for experiments

**Responsibilities**:
- Load problems from benchmark
- Coordinate 4-phase workflow (spec → iterate → checkpoint → complete)
- Manage iteration state
- Track costs via CostAnalyzer
- Store all data in cortex

**Key Methods**:
```python
async def run_experiment(problem, max_iterations) -> dict:
    """Main entry point - runs complete experiment"""

async def _build_iteration_prompt(exp_id, spec, iteration) -> str:
    """Constructs prompt for local model with context"""

async def _checkpoint(exp_id, iteration) -> str:
    """Triggers frontier review every N iterations"""

async def _complete_experiment(exp_id, success) -> dict:
    """Finalizes experiment and stores results"""
```

**State Management**:
- Stateless (all state in cortex)
- Each method is idempotent
- Async/await for I/O operations

### 2. CortexClient

**Purpose**: MCP client for claude-cortex-core server

**Protocol**: Model Context Protocol (MCP) over stdio

**Key Operations**:
```python
async def remember(title, content, category, tags, metadata):
    """Store memory in cortex"""

async def recall(query, tags, category, limit, mode):
    """Query memories from cortex"""

async def start_session(context):
    """Begin experiment session"""

async def end_session():
    """End session and trigger consolidation"""
```

**Connection Pattern**:
```python
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("remember", params)
```

**Why MCP?**
- Standard protocol for AI memory systems
- Persistent storage across experiments
- Queryable for analysis
- Automatic consolidation
- No database code in koderz

### 3. OllamaClient

**Purpose**: Interface to local models via Ollama API

**API**: HTTP REST to `http://localhost:11434`

**Key Endpoints**:
```python
POST /api/generate  # Generate completion
POST /api/pull      # Download model
GET  /api/tags      # List models
```

**Generation Pattern**:
```python
response = requests.post(
    f"{base_url}/api/generate",
    json={
        "model": "codellama:70b",
        "prompt": prompt,
        "stream": False  # Wait for complete response
    }
)
```

**Why Ollama?**
- Simple HTTP API
- Model management built-in
- Supports large models (70B+)
- No CUDA/GPU setup code needed
- Cross-platform

### 4. FrontierClient

**Purpose**: Interface to Claude models via Anthropic API

**API**: Official Anthropic Python SDK

**Key Operations**:
```python
def generate_spec(problem, model) -> dict:
    """Generate implementation spec (Phase 1)"""

def checkpoint_review(iterations, model) -> dict:
    """Review recent attempts (Phase 3)"""
```

**Cost Tracking**:
```python
def _calculate_cost(usage, model) -> float:
    input_cost = (usage.input_tokens / 1_000_000) * pricing["input"]
    output_cost = (usage.output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost
```

**Pricing Table** (as of Jan 2025):
| Model | Input ($/1M) | Output ($/1M) |
|-------|--------------|---------------|
| Opus 4.5 | $15 | $75 |
| Sonnet 4.5 | $3 | $15 |

**Why Anthropic?**
- Best reasoning for spec generation
- Cheaper Sonnet for checkpoints
- Structured output support
- Rate limiting handled by SDK

### 5. HumanEval Harness

**Purpose**: Load and execute coding problems

**Dataset Format** (JSONL):
```json
{
  "task_id": "HumanEval/0",
  "prompt": "def has_close_elements(...)...",
  "entry_point": "has_close_elements",
  "test": "def check(candidate): assert ...",
  "canonical_solution": "..."
}
```

**Execution Sandbox**:
```python
def execute_solution(code: str, test: str) -> dict:
    # Write code + tests to temp file
    # Run with subprocess.run(timeout=5)
    # Return {success, stdout, stderr, error}
```

**Security**:
- Timeout enforced (5 seconds default)
- Subprocess isolation
- No network access
- Temp file cleanup

**Why HumanEval?**
- Standard benchmark (164 problems)
- Well-tested
- Covers common patterns
- Objective pass/fail

### 6. CostAnalyzer

**Purpose**: Track and analyze experiment costs

**Metrics Tracked**:
- Frontier costs per call (spec, checkpoint)
- Local costs (always $0)
- Estimated frontier-only cost
- Savings percentage

**Calculation**:
```python
def calculate_savings(iterations: int) -> dict:
    actual = total_frontier_cost()
    frontier_only = estimate_frontier_only_cost(iterations)
    savings = frontier_only - actual
    savings_pct = (savings / frontier_only * 100)
```

**Assumptions**:
- Local models cost $0 (ignores electricity)
- Frontier-only estimate: avg_frontier_cost × iterations
- Typical: $0.05/iteration for Opus

## Data Flow

### Phase 1: Spec Generation

```
Problem → FrontierClient.generate_spec()
              ↓
         [Anthropic API]
              ↓
          Spec (text)
              ↓
     CortexClient.remember()
              ↓
         [MCP Server]
              ↓
      SQLite + FTS5
```

**Stored Metadata**:
```python
{
    "experiment_id": "exp_a1b2c3d4",
    "problem_id": "HumanEval/0",
    "model": "claude-opus-4-5",
    "cost": 0.0342,
    "timestamp": "2025-01-29T12:00:00"
}
```

### Phase 2: Iteration Loop

```
Spec + Context → OllamaClient.generate()
                      ↓
                 [Ollama API]
                      ↓
                 Solution (code)
                      ↓
              execute_solution()
                      ↓
              Test Results
                      ↓
         CortexClient.remember()
                      ↓
              [MCP Server]
```

**Iteration Metadata**:
```python
{
    "experiment_id": "exp_a1b2c3d4",
    "iteration": 8,
    "model": "codellama:70b",
    "success": True/False,
    "error": "...",
    "timestamp": "2025-01-29T12:05:00"
}
```

### Phase 3: Checkpoint

```
CortexClient.recall() → Last 5 iterations
           ↓
FrontierClient.checkpoint_review()
           ↓
      [Anthropic API]
           ↓
    Review + Guidance
           ↓
CortexClient.remember()
           ↓
     [MCP Server]
```

**Checkpoint Metadata**:
```python
{
    "experiment_id": "exp_a1b2c3d4",
    "checkpoint_num": 2,
    "iteration": 10,
    "model": "claude-sonnet-4-5",
    "cost": 0.0121,
    "timestamp": "2025-01-29T12:06:00"
}
```

### Phase 4: Completion

```
All Memories → CostAnalyzer.calculate_savings()
                     ↓
              Analysis Results
                     ↓
         CortexClient.remember()
                     ↓
              [MCP Server]
                     ↓
         Final Result Memory
```

**Result Metadata**:
```python
{
    "experiment_id": "exp_a1b2c3d4",
    "success": True,
    "iterations": 8,
    "frontier_cost": 0.0463,
    "frontier_only_cost": 0.1368,
    "savings": 0.0905,
    "savings_pct": 66.2,
    "timestamp": "2025-01-29T12:07:00"
}
```

## Design Decisions

### Why Async/Await?

- MCP client is async (stdio requires async I/O)
- Allows future parallelization (beam search)
- Clean error handling
- Non-blocking I/O

### Why Store Everything in Cortex?

**Pros**:
- No database code in koderz
- Queryable via Claude Code
- Automatic consolidation
- Persistent across runs
- Time-based decay
- FTS5 search

**Cons**:
- Dependency on cortex-core
- MCP overhead
- SQLite size limits

**Alternative Considered**: PostgreSQL
- **Rejected**: Too heavy for MVP

### Why Checkpoint Every 5 Iterations?

**Trade-off Analysis**:
- Too frequent (every iteration): High cost, slow
- Too rare (every 20): Local model stuck
- Sweet spot: 5 iterations (~$0.01/checkpoint with Sonnet)

**Adaptive Checkpointing** (future):
- Trigger on error rate increase
- Skip if local model improving
- Escalate to Opus if stuck

### Why CodeLlama?

**Compared**:
| Model | Size | Quality | Speed |
|-------|------|---------|-------|
| CodeLlama | 70B | Good | Medium |
| DeepSeek Coder | 33B | Better | Fast |
| StarCoder | 15B | OK | Very Fast |

**Choice**: CodeLlama 70B
- Best open-source code model
- Proven on HumanEval
- Instruction-tuned variant available

### Why HumanEval?

**Alternatives**:
- **MBPP**: Similar to HumanEval, smaller
- **SWE-bench**: Real GitHub issues (too hard)
- **CodeContests**: Competitive programming (too specialized)

**Choice**: HumanEval
- Standard benchmark
- Well-tested
- Right difficulty (solvable but non-trivial)
- Fast execution

## Scalability Considerations

### Current Limits

- **Sequential execution**: 1 problem at a time
- **Memory**: All experiment data in cortex (~100MB limit)
- **Network**: Anthropic rate limits (~50 req/min)
- **Disk**: Ollama model cache (~40GB per model)

### Scaling Up

**Parallel Experiments**:
```python
async with asyncio.TaskGroup() as tg:
    for problem in problems:
        tg.create_task(run_experiment(problem))
```

**Distributed Local Models**:
```python
# Round-robin across multiple Ollama instances
ollama_clients = [
    OllamaClient("http://server1:11434"),
    OllamaClient("http://server2:11434"),
]
```

**Separate Cortex per Experiment**:
```python
# Avoid SQLite lock contention
cortex = CortexClient(
    cortex_path,
    db_path=f"~/.claude-cortex/exp_{exp_id}.db"
)
```

## Error Handling

### Retry Strategy

```python
@retry(tries=3, delay=2, backoff=2)
async def call_with_retry(fn, *args):
    return await fn(*args)
```

### Graceful Degradation

1. **Ollama down**: Use frontier for all (expensive fallback)
2. **Anthropic rate limit**: Exponential backoff
3. **Cortex unavailable**: Log to file (lose queryability)
4. **Test timeout**: Skip iteration, continue

### Checkpointing

- All data in cortex (resumable)
- Experiment ID = resumable handle
- Future: `koderz resume exp_a1b2c3d4`

## Performance Optimization

### Current Bottlenecks

1. **Ollama generation**: 2-10s per iteration (70B model)
2. **MCP overhead**: ~100ms per remember/recall
3. **Anthropic API**: 1-3s per checkpoint

### Future Optimizations

**Batch MCP Calls**:
```python
# Single connection for multiple operations
async with cortex.session():
    await cortex.remember(...)
    await cortex.remember(...)
    await cortex.recall(...)
```

**Prompt Caching** (Anthropic):
- Cache spec in system prompt
- Reduces cost by ~90% for checkpoints

**Beam Search**:
- Generate N solutions in parallel
- Pick best via frontier review
- Trade latency for quality

**Quantized Models**:
- CodeLlama 70B GGUF Q4_K_M
- ~50% faster, minimal quality loss

## Security

### Threat Model

**In Scope**:
- Malicious code in solutions (sandbox escape)
- API key leakage
- DoS via infinite loops

**Out of Scope**:
- Ollama server compromise
- Network attacks
- Supply chain attacks

### Mitigations

1. **Subprocess timeout**: Hard limit on execution
2. **No network**: Solutions run offline
3. **Temp files**: Automatic cleanup
4. **API key**: Environment variable only
5. **Input validation**: Sanitize problem IDs

### Future Hardening

- Docker sandbox for execution
- Resource limits (CPU, memory)
- Audit logging
- API key rotation

## Testing Strategy

### Unit Tests

- Component isolation (mocks)
- Fast feedback (<1s)
- Coverage target: 80%

### Integration Tests

- Real Ollama (if available)
- Mock Anthropic (expensive)
- Fixture-based

### End-to-End Tests

- Real HumanEval problem
- All components live
- CI skip (expensive)

### Manual Tests

- Verification script (`setup_and_verify.sh`)
- Smoke tests for each command
- Cost capped at $0.10

## Monitoring

### Metrics to Track

- **Success rate**: % problems solved
- **Iterations to success**: Distribution
- **Cost per success**: $/problem
- **Frontier vs local ratio**: % of work done by each
- **Checkpoint effectiveness**: Improvement after checkpoint

### Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
```

### Future: Telemetry

- OpenTelemetry integration
- Grafana dashboards
- Alerting on errors

## Extensibility

### Adding New Benchmarks

1. Create `koderz/benchmarks/mbpp.py`
2. Implement `load_problems()` and `verify_solution()`
3. Add CLI command

### Custom Models

```python
# In .env
LOCAL_MODEL=deepseek-coder:33b
FRONTIER_MODEL=claude-opus-4-5

# Usage
koderz run --local-model $LOCAL_MODEL
```

### Custom Checkpointing

Override `_checkpoint()` in subclass:

```python
class AdaptiveOrchestrator(ExperimentOrchestrator):
    async def _checkpoint(self, exp_id, iteration):
        if self._should_checkpoint(iteration):
            return await super()._checkpoint(exp_id, iteration)
```

## Future Architecture

### Multi-Agent Swarm

```
       ┌──────────────┐
       │ Coordinator  │
       └──────┬───────┘
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
┌────────┐ ┌──────┐ ┌──────┐
│Generator│ │Critic│ │Tester│
└────────┘ └──────┘ └──────┘
```

### Beam Search

```
Iteration 1: Generate N solutions → Pick top K
Iteration 2: Refine K solutions → Pick top K
...
Iteration N: Frontier picks best
```

### Reinforcement Learning

```
Reward = (success ? 1.0 : 0.0) - (cost * 10)
Policy = checkpoint_frequency(error_rate, cost_budget)
```

---

## References

- [MCP Specification](https://github.com/modelcontextprotocol/specification)
- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Anthropic API](https://docs.anthropic.com/en/api)
- [HumanEval](https://github.com/openai/human-eval)
- [Claude Cortex Core](../README.md)
