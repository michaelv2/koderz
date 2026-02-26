```
╔════════════════════════════════════════════════════════════════════════╗
║                                                                        ║
║          ██╗  ██╗ ██████╗ ██████╗ ███████╗██████╗ ███████╗             ║
║          ██║ ██╔╝██╔═══██╗██╔══██╗██╔════╝██╔══██╗╚══███╔╝             ║
║          █████╔╝ ██║   ██║██║  ██║█████╗  ██████╔╝  ███╔╝              ║
║          ██╔═██╗ ██║   ██║██║  ██║██╔══╝  ██╔══██╗ ███╔╝               ║
║          ██║  ██╗╚██████╔╝██████╔╝███████╗██║  ██║███████╗             ║
║          ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝             ║
║                                                                        ║
║              Multi-Model Swarm Experiment Framework                    ║
║                                                                        ║
╚════════════════════════════════════════════════════════════════════════╝
```

Koderz is a **multi-model swarm experiment framework** that orchestrates coding experiments across HumanEval, BigCodeBench-Hard, and SWE-bench Verified benchmarks using local models (e.g. gpt-oss:20b, qwen3-coder) or small frontier models (e.g. GPT-4o-mini, Claude Haiku) for iterations, supervised by larger frontier models (Claude Sonnet/Opus) for checkpoint feedback, with all experimental data tracked via the `claude-cortex-core` MCP server.

It grew out of frustration with usage limits on cloud provider base paid tiers, but is essentially a poor man's implementation of [Augment](https://www.augmentcode.com/) or [Refact.ai](https://refact.ai/) that also works with local models. Unlike those solutions, the koderz orchestrator doesn't write any (or very minimal) code, which is much closer to how a human tech lead might work.

That doesn't necessarily make it optimal, but I believe the best way to understand these models to *use* them, so while koderz may not advance the state-of-the-art with regards to agentic workflows, it can be a useful harness for experimentation.

## Core Research Questions

- Is it viable to use local open source or small frontier models (individually or as an ensemble) with unlimited time and iterative feedback for software development? Can we trade clock time for lower API cost?

- If a frontier orchestrator delegates task instructions to local models, how high is the "knowledge transfer" tax (vs. the frontier model executing the task directly)?

- Where should intelligence optimally reside within a development loop (planning, orchestration, feedback, execution, etc.)? Does imposing process parsimony on frontier models surface subtle alignment issues (e.g. reward hacking)?

- To what extent do published benchmarks (e.g. pass@k) mask the non-deteministic nature of LLMs, or just represent the modern equivalent of p-hacking?

## Architecture

```
┌──────────────────────────────────┐
│  koderz (Python CLI)             │
│  - Experiment orchestration      │
│  - Model clients:                │
│    • Ollama (local)              │
│    • Anthropic API (frontier)    │
│    • OpenAI API (small frontier) │
│  - Benchmark harnesses           │
│    (HumanEval, BCB-Hard,         │
│     SWE-bench)                   │
│  - MCP client → cortex           │
└──────────────────────────────────┘
         │ (MCP protocol)
         ▼
┌──────────────────────────────────┐
│  claude-cortex-core              │
│  - Memory storage/retrieval      │
│  - 15 existing tools (no changes)│
│  - SQLite backend                │
└──────────────────────────────────┘
```

### Model Tiers

1. **Local** (Free) - Ollama models (gpt-oss:20b, qwen3-coder:latest, qwen2.5-coder:32b)
2. **Small Frontier** (Cheap) - GPT-4o-mini ($0.15/$0.60 per 1M tokens), Claude Haiku ($0.80/$4.00 per 1M tokens)
3. **Full Frontier** (Expensive) - Claude Opus ($15/$75 per 1M tokens), Claude Sonnet ($3/$15 per 1M tokens), GPT-4o ($2.50/$10 per 1M tokens)

### Recommended Model Configuration

```bash
--frontier-spec-model "gpt-oss:20b"              # Problem spec generation (FREE)
--local-model "qwen2.5-coder:32b"                # Code implementation (FREE)
--frontier-checkpoint-model "claude-sonnet-4-5"  # Checkpoint feedback (paid)
```

## Workflow

### Phase 1: Spec Generation
1. Load problem from benchmark dataset
2. Spec model (default: gpt-oss:20b) generates detailed implementation spec (skipped for zero-shot / no-spec tests)
3. Store spec in cortex via `remember` tool

### Phase 2: Iterative Execution (Local Model Swarm)
1. Local model (via Ollama) generates solution based on spec
2. Execute solution against tests
3. Store iteration in cortex
4. If tests pass → Complete (Phase 4)
5. If tests fail → Feed errors back to local model, repeat

### Phase 3: Frontier Checkpoint (Every 5 Iterations)
1. Query cortex for last 5 iterations
2. Frontier model reviews attempts and provides guidance
3. Store checkpoint in cortex
4. Feed guidance back to local model

### Phase 4: Completion & Analysis
1. Calculate cost analysis (frontier vs local)
2. Store final result in cortex
3. Display savings compared to frontier-only approach

## Installation

### Prerequisites

1. **Node.js 18+** (for claude-cortex-core)
2. **Python 3.10+**
3. **Ollama** - Local model server
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama pull codellama:70b
   ```
4. **Benchmark datasets** - Download via CLI
   ```bash
   # HumanEval+ (164 problems, ~764 tests each)
   poetry run koderz download-data --dataset humaneval+

   # BigCodeBench-Hard (148 multi-step library tasks)
   poetry run koderz download-data --dataset bigcodebench-hard

   # SWE-bench Verified (real-world GitHub issues)
   poetry run koderz download-data --dataset swebench-verified
   poetry run koderz setup-repos --dataset swebench-verified
   ```

### Install Koderz

```bash
cd koderz

# Using pip
pip install -e .

# Or using Poetry
poetry install
```

### Configure Environment

You can use environment variables directly or create a `.env` file:

**Option 1: Bash environment variables (recommended)**

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-proj-...  # Optional, for small frontier models
export OLLAMA_HOST=http://localhost:11434
export CORTEX_PATH=/path/to/claude-cortex-core/dist/index.js
```

**Option 2: .env file**

```bash
cp .env.example .env
# Edit .env with your keys
```

### Build Cortex Core

```bash
cd ../claude-cortex-core
npm install
npm run build
```

## Usage

### Run Single Experiment

**Default (gpt-oss:20b spec, local iterations - RECOMMENDED):**
```bash
poetry run koderz run --problem-id "HumanEval/0"
# Uses: gpt-oss:20b for spec (free), codellama:70b for iterations (free)
```

**All free local models:**
```bash
poetry run koderz run --problem-id "HumanEval/0" \
  --frontier-spec-model "gpt-oss:20b" \
  --local-model "qwen2.5-coder:32b" \
  --frontier-checkpoint-model "gpt-oss:20b"
```

**Maximum quality (paid):**
```bash
poetry run koderz run --problem-id "HumanEval/0" \
  --frontier-spec-model "claude-opus-4-5" \
  --local-model "gpt-4o-mini" \
  --frontier-checkpoint-model "claude-sonnet-4-5"
```

**Reuse existing spec (save 60-75% on costs):**
```bash
poetry run koderz run --problem-id "HumanEval/0" \
  --local-model "gpt-4o-mini" \
  --reuse-spec
```

**Debug mode (save all outputs as JSON for analysis):**
```bash
poetry run koderz run --problem-id "HumanEval/0" \
  --debug \
  --debug-dir ./debug_output
```

### Options

- `--local-model` - Model for iterations (default: `codellama:70b`)
  - Local: `qwen3-coder:latest` (fastest, 140 tok/s), `gpt-oss:20b`, `qwen2.5-coder:32b`, `codellama:70b`, `llama3.3:70b`
  - Small frontier: `gpt-4o-mini`, `claude-haiku-4-5`
  - Full frontier: `claude-sonnet-4-5`, `gpt-4o`
- `--frontier-spec-model` - Model for spec generation (default: `gpt-oss:20b`)
  - Recommended: `gpt-oss:20b` (validated 100% first-try success, free)
  - Alternative: `claude-sonnet-4-5`, `claude-opus-4-5`, `qwen2.5-coder:32b`
- `--frontier-checkpoint-model` - Model for checkpoints (default: `claude-sonnet-4-5`)
- `--max-iterations` - Max iterations (default: 50)
- `--checkpoint-interval` - Checkpoint every N iterations (default: 5, used with `fixed` strategy)
- `--checkpoint-strategy` - `fixed` (every N iterations, default) or `on-demand` (triggers on stuck patterns: plateau, oscillation, zero progress)
- `--reuse-spec` - Reuse existing spec from Cortex instead of regenerating (recommended for benchmarks)
- `--mode` - Evaluation mode: `zero-shot` (single attempt, no feedback) or `iterative` (with test feedback, default)
- `--timeout` - Request timeout in seconds for Ollama (default: 300)
- `--max-retries` - Maximum retry attempts for Ollama timeouts/overload (default: 3)
- `--num-ctx` - Context window size for Ollama models in tokens (default: 5120, tuned from real data)
- `--debug` - Enable debug mode: saves raw outputs, extracted code, and test results
- `--debug-dir` - Directory for debug outputs (default: `./debug`)
- `--no-cot` - Disable chain-of-thought prompting
- `--seed` - Random seed for reproducibility
- `--temperature` - Sampling temperature for model generation
- `--dataset` - Dataset to use: `humaneval` (default), `humaneval+`, `bigcodebench`, `bigcodebench-hard`, `swebench-verified`, `swebench-lite`
- `--test-timeout` - Test execution timeout in seconds

Ablation modes:

- `--no-spec` - Skip spec generation
- `--no-checkpoints` - Disable checkpoint reviews

### Run Benchmark

```bash
# Standard iterative benchmark (HumanEval)
poetry run koderz benchmark --start 0 --end 10 \
  --local-model "gpt-4o-mini"

# Zero-shot benchmark (single attempt per problem, no feedback)
poetry run koderz benchmark --start 0 --end 10 \
  --local-model "gpt-4o-mini" --mode zero-shot

# Comparative benchmark (runs both zero-shot and iterative, then compares)
poetry run koderz benchmark --start 0 --end 10 \
  --local-model "gpt-4o-mini" --mode comparative

# HumanEval+ benchmark (harder test cases with edge cases)
poetry run koderz benchmark --start 0 --end 10 \
  --local-model "gpt-4o-mini" --dataset humaneval+

# BigCodeBench-Hard (148 multi-step library tasks)
poetry run koderz benchmark --start 0 --end 148 \
  --dataset bigcodebench-hard --local-model "gpt-oss:20b"

# SWE-bench Verified (real-world GitHub issues, requires repo setup)
poetry run koderz download-data --dataset swebench-verified
poetry run koderz setup-repos --dataset swebench-verified
poetry run koderz run --problem-id "django__django-16379" \
  --dataset swebench-verified --local-model "qwen3-coder:latest" \
  --mode zero-shot --no-spec
```

Runs experiments on the selected benchmark problems. Results are saved to `benchmark_results/` as JSON.

### Slack Notifications for Long-Running Tasks

Get notified in Slack when long-running benchmarks complete:

**Setup:**
1. Create a Slack webhook URL: https://api.slack.com/messaging/webhooks
2. Add to your `.env` file:
   ```bash
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   ```

**Usage:**
```bash
./notify-on-complete.sh poetry run koderz benchmark --start 0 --end 164 \
  --local-model "gpt-oss:20b"
```

### List Problems

```bash
poetry run koderz list-problems
poetry run koderz list-problems --dataset swebench-verified
```

### Query Experiment Results

```bash
# List all experiment results
poetry run koderz results

# Filter by problem
poetry run koderz results --problem "HumanEval/0"

# Show only successful experiments
poetry run koderz results --success-only
```

### Analyze Experiment

```bash
poetry run koderz analyze exp_abc12345

# Include code from each iteration
poetry run koderz analyze exp_abc12345 --show-code
```

Query cortex for experiment data. For full details, use Claude Code:

```bash
claude
> /recall query:exp_abc12345
```

### Speed Test Models

```bash
# Benchmark a single model
poetry run koderz speed-test qwen2.5-coder:32b

# Compare multiple models
poetry run koderz speed-test qwen2.5-coder:32b codellama:70b llama3.3:70b

# Export results to JSON
poetry run koderz speed-test qwen2.5-coder:32b --export speed_results.json
```

**Sample Results** (Ollama server with 2x NVIDIA RTX 3090 GPUs, 96GB RAM):

| Model | Params | Avg tok/s | Essay | Coding | Brain Teaser | Total Time |
|---|---|---|---|---|---|---|
| qwen3-coder:latest | 32B | **139.9** | 138.3 | 140.1 | 141.2 | 11.2s |
| gpt-oss:20b | 20B | **137.5** | 138.8 | 136.8 | 137.0 | 17.1s |
| qwen3:30b-a3b | 30B | **112.5** | 116.6 | 109.5 | 111.4 | 35.2s |
| qwen2.5-coder:14b | 14B | **76.4** | 76.9 | 76.0 | 76.4 | 18.1s |
| qwen2.5-coder:32b | 32B | **38.0** | 38.0 | 37.9 | 37.9 | 35.3s |
| gemma3:27b | 27B | **36.2** | 41.0 | 26.9 | 40.7 | 55.7s |
| codellama:70b | 70B | **20.5** | 20.4 | 20.6 | 20.6 | 68.2s |
| mixtral:8x7b | 8x7B | **10.8** | 10.7 | 10.7 | 11.0 | 107.1s |
| llama4:16x17b | 16x17B | **5.4** | 5.4 | 5.2 | 5.4 | 234.2s |
| llama3.3:70b | 70B | **3.9** | 4.0 | 3.8 | 3.9 | 321.7s |
| nemotron:70b | 70B | **3.8** | 3.9 | 3.9 | 3.7 | 337.5s |
| deepseek-r1:70b | 70B | **3.8** | 3.8 | 3.7 | 3.8 | 972.2s |
| qwen2.5:72b | 72B | **2.8** | 2.8 | 2.8 | 2.8 | 453.3s |

## Example Output

```
============================================================
Starting Experiment: exp_a1b2c3d4
Problem: HumanEval/0
============================================================

Phase 1: Generating spec with gpt-oss:20b...
  Spec generated (cost: $0.00)
  Stored in cortex

Phase 2: Iterative execution with codellama:70b...
  Iteration 1/50...
    [INFO] Code extracted from markdown/text wrapper
    ✗ Failed: IndexError: list index out of range
  Iteration 2/50...
    ✗ Failed: Expected True, got False
  Iteration 3/50...
    [INFO] Code extracted from markdown/text wrapper
    ✗ Failed: AssertionError
  Iteration 4/50...
    ✗ Failed: Expected True, got False
  Iteration 5/50...
    ✗ Failed: IndexError

  Checkpoint 1...
    Guidance received from claude-sonnet-4-5

  Iteration 6/50...
    [INFO] Code extracted from markdown/text wrapper
    ✗ Failed: Expected True, got False
  Iteration 7/50...
    ✗ Failed: AssertionError
  Iteration 8/50...
    ✓ SUCCESS! All tests passed.

============================================================
Experiment Complete: exp_a1b2c3d4
============================================================
Success: True
Iterations: 8

Cost Analysis:
  Actual Total: $0.0023
    - Full Frontier: $0.0023 (checkpoint)
    - Small Frontier: $0.0000 (0 calls)
    - Local: $0.0000 (spec + 8 iterations - free)

  Frontier-Only Estimate: $0.1368
  Savings: $0.1345 (98.3%)
```

## Project Structure

```
koderz/
├── pyproject.toml          # Poetry dependencies
├── README.md               # This file
├── .env.example            # Environment template
├── koderz/
│   ├── __init__.py
│   ├── cli.py              # CLI entry point
│   ├── orchestrator.py     # Experiment orchestration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── local.py        # Ollama client (uses /api/chat)
│   │   ├── frontier.py     # Anthropic API client
│   │   ├── openai_client.py # OpenAI API client (GPT-4o, GPT-4o-mini)
│   │   ├── registry.py     # Model metadata and tier definitions
│   │   └── factory.py      # Client factory pattern
│   ├── cortex/
│   │   └── client.py       # MCP client for cortex-core
│   ├── benchmarks/
│   │   ├── humaneval.py    # HumanEval loader & executor
│   │   ├── bigcodebench.py # BigCodeBench loader & executor
│   │   ├── swebench.py     # SWE-bench loader & evaluator
│   │   ├── repo_manager.py # Git repo/worktree management for SWE-bench
│   │   └── speed_test.py   # Model inference speed benchmarking
│   ├── analysis/
│   │   └── cost.py         # Cost analysis with tier tracking
│   ├── utils/
│   │   ├── code_extraction.py       # Code extraction from markdown/text
│   │   ├── multi_file_extraction.py # Multi-file extraction from model output
│   │   └── retry.py                 # Retry with exponential backoff
│   └── data/
│       └── HumanEval.jsonl # Sample problems
├── tests/
│   ├── test_orchestrator.py           # Core orchestrator unit tests
│   ├── test_spec_validation_gptoss.py # gpt-oss:20b validation benchmark
│   ├── test_spec_comparison.py        # Spec model comparison benchmark
│   ├── test_spec_comparison_3way.py   # 3-way spec comparison benchmark
│   └── test_spec_qwen_vs_gptoss.py   # qwen vs gpt-oss benchmark
└── docs/                   # Feature documentation
    ├── orchestrator/       # Core feature docs
    │   ├── spec_generation/
    │   ├── checkpoints/
    │   ├── benchmarks/
    │   ├── test_metrics/
    │   ├── zero-shot/
    │   └── ollama/
    ├── reasoning/          # Chain-of-thought analysis
    └── speed_test/         # Speed testing docs
```

## Testing & Verification

```bash
# Test all components
poetry run python -c "
from koderz.models.factory import ModelFactory
from koderz.cortex.client import CortexClient
import os
print('✓ All imports successful')
"

# List available problems
poetry run koderz list-problems

# Test code execution
poetry run python -c "
from koderz.benchmarks.humaneval import execute_solution
result = execute_solution('def f(): return 42', 'assert f() == 42')
print(f'✓ Code execution: {result[\"success\"]}')
"
```

## Cost Analysis

Default configuration (gpt-oss:20b spec + local iterations) achieves 96-100% cost savings vs frontier-only baselines on simple tasks like HumanEval/HumanEval+. Per-tier pricing is listed under [Model Tiers](#model-tiers). See [SPEC_REUSE_FEATURE.md](docs/orchestrator/spec_generation/SPEC_REUSE_FEATURE.md) for detailed cost comparisons and [ORCHESTRATION_STUDY_RESULTS.md](docs/ORCHESTRATION_STUDY_RESULTS.md) for benchmark study results.

## Documentation

### Getting Started
- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute setup guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical deep dive

### Study Results
- **[ORCHESTRATION_STUDY_RESULTS.md](docs/ORCHESTRATION_STUDY_RESULTS.md)** - Multi-benchmark study results (HumanEval, BCB-Hard, hierarchical)
- **[FRONTIER_GUIDANCE_STUDY.md](docs/FRONTIER_GUIDANCE_STUDY.md)** - Local models + frontier checkpoints vs frontier zero-shot
- **[ITERATION_ATTRIBUTION_ANALYSIS.md](docs/ITERATION_ATTRIBUTION_ANALYSIS.md)** - Checkpoint guidance vs self-recovery attribution
- **[HIERARCHICAL_ORCHESTRATION_RESULTS.md](docs/HIERARCHICAL_ORCHESTRATION_RESULTS.md)** - Opus-orchestrated multi-file project experiment

### Development History Reference

#### Spec Generation
- **[SPEC_VALIDATION_GPTOSS.md](docs/orchestrator/spec_generation/SPEC_VALIDATION_GPTOSS.md)** - Validation results: 100% first-try success with gpt-oss:20b
- **[SPEC_REUSE_FEATURE.md](docs/orchestrator/spec_generation/SPEC_REUSE_FEATURE.md)** - Spec reuse with cost savings examples

#### Checkpoint Guidance
- **[CHECKPOINT_GUIDANCE_UPGRADE.md](docs/orchestrator/checkpoints/CHECKPOINT_GUIDANCE_UPGRADE.md)** - Test-aware checkpoint system with plateau detection
- **[PROGRESSIVE_SPEC_DISCLOSURE.md](docs/orchestrator/checkpoints/PROGRESSIVE_SPEC_DISCLOSURE.md)** - Progressive spec disclosure (experimental)

#### Benchmarking
- **[BENCHMARK_RUN_TRACKING.md](docs/orchestrator/benchmarks/BENCHMARK_RUN_TRACKING.md)** - Benchmark run tracking and Cortex storage
- **[PERFORMANCE_OPTIMIZATION.md](docs/PERFORMANCE_OPTIMIZATION.md)** - Persistent Cortex, timing instrumentation, parallel execution

#### Test Metrics
- **[TEST_METRICS_IMPLEMENTATION.md](docs/orchestrator/test_metrics/TEST_METRICS_IMPLEMENTATION.md)** - Granular test pass tracking
- **[TEST_CASE_METRICS_ANALYSIS.md](docs/orchestrator/test_metrics/TEST_CASE_METRICS_ANALYSIS.md)** - Test case metrics analysis

#### Evaluation Modes
- **[EVALUATION_MODE_ANALYSIS.md](docs/orchestrator/zero-shot/EVALUATION_MODE_ANALYSIS.md)** - Zero-shot vs iterative analysis

#### Reasoning & Chain-of-Thought
- **[COT_TCOT_ANALYSIS.md](docs/reasoning/COT_TCOT_ANALYSIS.md)** - CoT vs TCoT comparison
- **[POT_EVALUATION.md](docs/reasoning/POT_EVALUATION.md)** - Program-of-thought evaluation

#### Model Speed Testing
- **[MODEL_SPEED_TESTING.md](docs/speed_test/MODEL_SPEED_TESTING.md)** - Model speed testing guide (includes warmup feature)

#### Ollama Configuration
- **[OLLAMA_CONFIGURATION.md](docs/orchestrator/ollama/OLLAMA_CONFIGURATION.md)** - Ollama setup and configuration
- **[CONTEXT_WINDOW_MANAGEMENT.md](docs/orchestrator/ollama/CONTEXT_WINDOW_MANAGEMENT.md)** - Context window tuning (5K default, data-driven)
- **[RETRY_AND_QUEUE_MANAGEMENT.md](docs/orchestrator/ollama/RETRY_AND_QUEUE_MANAGEMENT.md)** - Retry logic and queue management

## Future Enhancements

See [ARCHITECTURE.md](ARCHITECTURE.md#future-architecture) for detailed plans including multi-agent swarm, beam search, MCTS, and meta-learning.

## Contributing

Contributions welcome! This is an experimental research framework.

## Citation

If you use Koderz in research, please cite:

```bibtex
@software{koderz2026,
  title={Koderz: Multi-Model Swarm Experiment Framework},
  author={Koderz Contributors},
  year={2026},
  url={https://github.com/koderz/koderz}
}
```
