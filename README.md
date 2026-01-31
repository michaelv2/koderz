```
╔════════════════════════════════════════════════════════════════════════╗
║                                                                        ║
║   ██╗  ██╗ ██████╗ ██████╗ ███████╗██████╗ ███████╗                    ║
║   ██║ ██╔╝██╔═══██╗██╔══██╗██╔════╝██╔══██╗╚══███╔╝                    ║
║   █████╔╝ ██║   ██║██║  ██║█████╗  ██████╔╝  ███╔╝                     ║
║   ██╔═██╗ ██║   ██║██║  ██║██╔══╝  ██╔══██╗ ███╔╝                      ║
║   ██║  ██╗╚██████╔╝██████╔╝███████╗██║  ██║███████╗                    ║
║   ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝                    ║
║                                                                        ║
║              Multi-Model Swarm Experiment Framework                    ║
║                                                                        ║
╚════════════════════════════════════════════════════════════════════════╝
```

Koderz is a **multi-model swarm experiment framework** that orchestrates coding experiments using local models (CodeLlama 70B, gpt-oss:20b) or small frontier models (GPT-4o-mini, Claude Haiku) for iterations, supervised by frontier models (Claude Sonnet/Opus) for checkpoints, with all experimental data tracked via the `claude-cortex-core` MCP server.

**What's New:**
- 🎯 **gpt-oss:20b default spec model**: Validated 100% first-try success rate, 37% faster than Sonnet, zero cost
- ✅ **Three-tier model system**: Local (free), Small Frontier (cheap), Full Frontier (expensive)
- ✅ **Spec reuse feature**: Save 60-75% on costs by reusing specifications across experiments
- ✅ **Code extraction utilities**: Automatically extract Python code from markdown/text wrappers
- ✅ **Debug mode**: Save all iteration outputs, extracted code, and test results for analysis
- ✅ **Flexible model selection**: Use any model for any phase (spec, iterations, checkpoints)

## Core Research Question

Can we achieve comparable results to expensive frontier models by giving cheaper local or small frontier models unlimited time and iterative refinement?

## Architecture

```
┌──────────────────────────────────┐
│  koderz (Python CLI)             │
│  - Experiment orchestration      │
│  - Model clients:                │
│    • Ollama (local)              │
│    • Anthropic API (frontier)    │
│    • OpenAI API (small frontier) │
│  - HumanEval benchmark harness   │
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

1. **Local** (Free) - Ollama models (gpt-oss:20b, CodeLlama 70B, Llama 3.3, qwen2.5-coder:32b)
2. **Small Frontier** (Cheap) - GPT-4o-mini ($0.15/$0.60 per 1M tokens), Claude Haiku ($0.80/$4.00 per 1M tokens)
3. **Full Frontier** (Expensive) - Claude Opus ($15/$75 per 1M tokens), Claude Sonnet ($3/$15 per 1M tokens), GPT-4o ($2.50/$10 per 1M tokens)

### Recommended Model Configuration 🎯

**Default (Validated for Best Results):**
```bash
--frontier-spec-model "gpt-oss:20b"              # Spec generation (FREE)
--local-model "qwen2.5-coder:32b"                # Implementation (FREE)
--frontier-checkpoint-model "claude-sonnet-4-5"  # Checkpoints (paid)
```

**Why gpt-oss:20b for specs?**
- ✅ **100% first-try success** validated on 20 HumanEval problems
- ✅ **37% faster** than Claude Sonnet 4.5 (16.4s vs 26.5s avg)
- ✅ **30% more detailed** specs (6,625 chars vs 5,077 chars)
- ✅ **Zero cost** vs $0.024 per spec with Sonnet
- ✅ **Production-quality formatting**: markdown tables, code examples, comprehensive edge cases

See [SPEC_VALIDATION_GPTOSS.md](SPEC_VALIDATION_GPTOSS.md) for full validation results and analysis.

**Alternative Configurations:**

*For maximum quality (paid):*
```bash
--frontier-spec-model "claude-opus-4-5"          # Most comprehensive specs
--local-model "gpt-4o-mini"                      # Fast, cheap iterations
--frontier-checkpoint-model "claude-sonnet-4-5"  # Strong guidance
```

*For maximum speed (free):*
```bash
--frontier-spec-model "gpt-oss:20b"              # Fast, detailed specs
--local-model "codellama:70b"                    # Fast local model
--frontier-checkpoint-model "claude-haiku-4-5"   # Cheap checkpoints
```

## Workflow

### Phase 1: Spec Generation
1. Load problem from HumanEval benchmark
2. Spec model (default: gpt-oss:20b) generates detailed implementation spec
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
4. **HumanEval dataset**
   ```bash
   # Download from https://github.com/openai/human-eval
   # Place HumanEval.jsonl in koderz/data/
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

**Debug mode (save all outputs for analysis):**
```bash
poetry run koderz run --problem-id "HumanEval/0" \
  --debug \
  --debug-dir ./debug_output
```

### Options

- `--local-model` - Model for iterations (default: `codellama:70b`)
  - Local: `gpt-oss:20b` (recommended for speed), `qwen2.5-coder:32b`, `codellama:70b`, `llama3.3:70b`
  - Small frontier: `gpt-4o-mini`, `claude-haiku-4-5`
  - Full frontier: `claude-sonnet-4-5`, `gpt-4o`
- `--frontier-spec-model` - Model for spec generation (default: `gpt-oss:20b`)
  - Recommended: `gpt-oss:20b` (validated 100% first-try success, free)
  - Alternative: `claude-sonnet-4-5`, `claude-opus-4-5`, `qwen2.5-coder:32b`
- `--frontier-checkpoint-model` - Model for checkpoints (default: `claude-sonnet-4-5`)
- `--max-iterations` - Max iterations (default: 50)
- `--checkpoint-interval` - Checkpoint every N iterations (default: 5)
- `--reuse-spec` - Reuse existing spec from Cortex instead of regenerating (recommended for benchmarks)
- `--debug` - Enable debug mode: saves raw outputs, extracted code, and test results
- `--debug-dir` - Directory for debug outputs (default: `./debug`)

### Run Benchmark

```bash
poetry run koderz benchmark --start 0 --end 10 \
  --local-model "gpt-4o-mini"
```

Runs experiments on HumanEval problems 0-9.

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

The script will:
- Run your command and show all output in real-time
- Send a Slack notification when complete with:
  - ✅/❌ Success/failure status
  - Total runtime
  - Last 5 lines of output
  - Timestamp and hostname

Perfect for running overnight benchmarks or when you want to step away from the terminal.

### List Problems

```bash
poetry run koderz list-problems
```

### Analyze Experiment

```bash
poetry run koderz analyze exp_abc12345
```

Query cortex for experiment data. For full details, use Claude Code:

```bash
claude
> /recall query:exp_abc12345
```

## Example Output

**Example 1: Default approach (spec=gpt-oss:20b, iterations=CodeLlama, checkpoint=Sonnet)**

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

**Example 2: Spec reuse (second run on same problem)**

```
Phase 1: Looking for existing spec for HumanEval/0...
  Found existing spec (generated by claude-sonnet-4-5)
  Reusing spec (cost: $0.00 - saved!)

Phase 2: Iterative execution with gpt-4o-mini...
  [...]
```

**Example 3: Debug mode output**

```
Phase 2: Iterative execution with codellama:70b...
  Iteration 1/50...
    [DEBUG] Raw output saved to debug/exp_a1b2c3d4_iter001_raw.txt
    [INFO] Code extracted from markdown/text wrapper
    [DEBUG] Extracted code saved to debug/exp_a1b2c3d4_iter001_code.py
    [DEBUG] Code preview: def has_close_elements(numbers: List[float], threshold...
    [DEBUG] Test result saved to debug/exp_a1b2c3d4_iter001_result.txt
    ✗ Failed: IndexError: list index out of range
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
│   │   ├── local.py        # Ollama client
│   │   ├── frontier.py     # Anthropic API client
│   │   ├── openai_client.py # OpenAI API client (GPT-4o, GPT-4o-mini)
│   │   ├── registry.py     # Model metadata and tier definitions
│   │   └── factory.py      # Client factory pattern
│   ├── cortex/
│   │   └── client.py       # MCP client for cortex-core
│   ├── benchmarks/
│   │   └── humaneval.py    # HumanEval loader & executor
│   ├── analysis/
│   │   └── cost.py         # Cost analysis with tier tracking
│   ├── utils/
│   │   └── code_extraction.py # Code extraction from markdown/text
│   └── data/
│       └── HumanEval.jsonl # Sample problems
└── tests/
    └── test_orchestrator.py
```

## Testing & Verification

### Quick Verification

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

### Individual Component Tests

**Test OpenAI client:**
```bash
poetry run python -c "
from koderz.models.openai_client import OpenAIClient
import os
client = OpenAIClient(os.getenv('OPENAI_API_KEY'))
result = client.generate_spec('Write a function that adds two numbers', model='gpt-4o-mini')
print(f'Spec: {result[\"spec\"][:100]}...')
print(f'Cost: \${result[\"cost\"]:.6f}')
"
```

**Test model factory:**
```bash
poetry run python -c "
from koderz.models.factory import ModelFactory
import os
factory = ModelFactory(
    anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
    openai_api_key=os.getenv('OPENAI_API_KEY')
)
print(f'✓ Anthropic client: {type(factory.get_client(\"claude-opus-4-5\"))}')
print(f'✓ OpenAI client: {type(factory.get_client(\"gpt-4o-mini\"))}')
print(f'✓ Ollama client: {type(factory.get_client(\"codellama:70b\"))}')
"
```

**Test MCP connection:**
```bash
poetry run python -c "
from koderz.cortex.client import CortexClient
import asyncio, os

async def test():
    cortex = CortexClient(os.getenv('CORTEX_PATH'))
    result = await cortex.remember(
        title='Test', content='Testing', category='note'
    )
    print(f'✓ Memory created: {result}')

asyncio.run(test())
"
```

## Key Features

### ✅ Three-Tier Model System
- **Local models** (free) - CodeLlama, Llama 3.3 via Ollama
- **Small frontier models** (cheap) - GPT-4o-mini, Claude Haiku
- **Full frontier models** (expensive) - Claude Opus/Sonnet, GPT-4o
- Mix and match models for different phases (spec, iterations, checkpoints)

### ✅ Spec Reuse
- Save specifications in Cortex for reuse across experiments
- 60-75% cost savings on multi-model comparisons
- Zero-cost spec retrieval from memory
- Consistent baseline across experiments

### ✅ Memory Persistence
All experiment data stored in Cortex:
- Specifications with cost metadata
- Each iteration attempt with test results
- Checkpoint reviews and guidance
- Final results and cost analysis

Query via Claude Code:
```bash
claude
> Examine failures from experiment exp_a1b2c3d4
```

### ✅ Cost Tracking by Tier
- Separate tracking for local, small frontier, and full frontier costs
- Detailed breakdown in experiment results
- Savings calculation vs frontier-only baseline
- Model usage statistics

### ✅ Code Extraction
- Automatically extracts Python code from markdown fenced blocks (` ```python `)
- Handles generic code blocks and plain text responses
- Validates syntax before execution using AST parsing
- Fallback strategies for various output formats

### ✅ Debug Mode
- Save all raw model outputs (`*_raw.txt`)
- Save extracted Python code (`*_code.py`)
- Save test results (`*_result.txt`)
- Save checkpoint guidance files
- Helpful INFO/DEBUG/WARNING messages during execution

### ✅ Flexible Workflow
- Configurable checkpoint interval
- Max iteration limits
- Custom model selection per phase
- Async architecture ready for parallelization

## Documentation

### Getting Started
- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute setup guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical deep dive
- **[TODO.md](TODO.md)** - Future roadmap

### Spec Generation (Recommended Reading)
- **[docs/orchestrator/spec_generation/SPEC_VALIDATION_GPTOSS.md](docs/orchestrator/spec_generation/SPEC_VALIDATION_GPTOSS.md)** - ⭐ Validation results: 100% first-try success with gpt-oss:20b
- **[docs/orchestrator/spec_generation/SPEC_REUSE_FEATURE.md](docs/orchestrator/spec_generation/SPEC_REUSE_FEATURE.md)** - Guide to spec reuse with cost savings examples
- **[docs/orchestrator/spec_generation/INTEGRATION_SUMMARY.md](docs/orchestrator/spec_generation/INTEGRATION_SUMMARY.md)** - gpt-oss:20b integration summary
- **[docs/orchestrator/spec_generation/SPEC_QWEN_VS_GPTOSS_ANALYSIS.md](docs/orchestrator/spec_generation/SPEC_QWEN_VS_GPTOSS_ANALYSIS.md)** - Comparison: gpt-oss:20b vs qwen2.5-coder:32b
- **[docs/orchestrator/spec_generation/SPEC_3WAY_ANALYSIS.md](docs/orchestrator/spec_generation/SPEC_3WAY_ANALYSIS.md)** - Three-way: Sonnet vs llama3.3:70b vs qwen2.5-coder:32b
- **[docs/orchestrator/spec_generation/SPEC_MODEL_COMPARISON.md](docs/orchestrator/spec_generation/SPEC_MODEL_COMPARISON.md)** - Initial model comparison analysis

### Context Window & Performance
- **[docs/CONTEXT_WINDOW_MANAGEMENT.md](docs/CONTEXT_WINDOW_MANAGEMENT.md)** - ⭐ Context window tuning guide (5K default, data-driven)
- **[CONTEXT_WINDOW_UPDATE.md](CONTEXT_WINDOW_UPDATE.md)** - Summary of 8K→5K optimization
- **[CONTEXT_ANALYSIS_REVISED.md](CONTEXT_ANALYSIS_REVISED.md)** - Revised token usage analysis

### Checkpoint Guidance
- **[docs/orchestrator/checkpoints/CHECKPOINT_GUIDANCE_QUICK_REF.md](docs/orchestrator/checkpoints/CHECKPOINT_GUIDANCE_QUICK_REF.md)** - Quick reference for checkpoint system
- **[docs/orchestrator/checkpoints/CHECKPOINT_GUIDANCE_UPGRADE.md](docs/orchestrator/checkpoints/CHECKPOINT_GUIDANCE_UPGRADE.md)** - Enhanced checkpoint implementation
- **[docs/orchestrator/checkpoints/IMPLEMENTATION_SUMMARY_CHECKPOINT.md](docs/orchestrator/checkpoints/IMPLEMENTATION_SUMMARY_CHECKPOINT.md)** - Implementation details

### Benchmarking
- **[docs/orchestrator/benchmarks/BENCHMARK_RUN_TRACKING.md](docs/orchestrator/benchmarks/BENCHMARK_RUN_TRACKING.md)** - Benchmark tracking system
- **[docs/orchestrator/benchmarks/BENCHMARK_RUN_TRACKING_QUICK_REF.md](docs/orchestrator/benchmarks/BENCHMARK_RUN_TRACKING_QUICK_REF.md)** - Quick reference
- **[docs/orchestrator/benchmarks/IMPLEMENTATION_SUMMARY_BENCHMARK_TRACKING.md](docs/orchestrator/benchmarks/IMPLEMENTATION_SUMMARY_BENCHMARK_TRACKING.md)** - Implementation details

### Test Metrics
- **[docs/orchestrator/test_metrics/TEST_METRICS_QUICK_REF.md](docs/orchestrator/test_metrics/TEST_METRICS_QUICK_REF.md)** - Quick reference for test metrics
- **[docs/orchestrator/test_metrics/TEST_METRICS_IMPLEMENTATION.md](docs/orchestrator/test_metrics/TEST_METRICS_IMPLEMENTATION.md)** - Granular test pass tracking
- **[docs/orchestrator/test_metrics/TEST_CASE_METRICS_ANALYSIS.md](docs/orchestrator/test_metrics/TEST_CASE_METRICS_ANALYSIS.md)** - Test case metrics analysis
- **[docs/orchestrator/test_metrics/METRICS_CLARIFICATION.md](docs/orchestrator/test_metrics/METRICS_CLARIFICATION.md)** - Metrics clarification guide

### Evaluation Modes
- **[docs/orchestrator/zero-shot/EVALUATION_MODE_ANALYSIS.md](docs/orchestrator/zero-shot/EVALUATION_MODE_ANALYSIS.md)** - Zero-shot vs iterative analysis
- **[docs/orchestrator/zero-shot/IMPLEMENTATION_SUMMARY.md](docs/orchestrator/zero-shot/IMPLEMENTATION_SUMMARY.md)** - Zero-shot implementation details

### Reasoning & Chain-of-Thought
- **[docs/reasoning/COT_QUICK_REFERENCE.md](docs/reasoning/COT_QUICK_REFERENCE.md)** - Chain-of-thought quick reference
- **[docs/reasoning/COT_TCOT_ANALYSIS.md](docs/reasoning/COT_TCOT_ANALYSIS.md)** - CoT vs TCoT comparison
- **[docs/reasoning/POT_EVALUATION.md](docs/reasoning/POT_EVALUATION.md)** - Program-of-thought evaluation

### Model Speed Testing
- **[docs/speed_test/SPEED_TEST_QUICK_REF.md](docs/speed_test/SPEED_TEST_QUICK_REF.md)** - Quick reference for speed testing
- **[docs/speed_test/MODEL_SPEED_TESTING.md](docs/speed_test/MODEL_SPEED_TESTING.md)** - Model speed testing guide
- **[docs/speed_test/WARMUP_FEATURE_IMPLEMENTATION.md](docs/speed_test/WARMUP_FEATURE_IMPLEMENTATION.md)** - Warmup feature details
- **[docs/speed_test/IMPLEMENTATION_SUMMARY_SPEED_TEST.md](docs/speed_test/IMPLEMENTATION_SUMMARY_SPEED_TEST.md)** - Speed test implementation

### Ollama Configuration
- **[docs/orchestrator/ollama/OLLAMA_CONFIGURATION.md](docs/orchestrator/ollama/OLLAMA_CONFIGURATION.md)** - Ollama setup and configuration
- **[docs/orchestrator/ollama/OLLAMA_HOST_FIX.md](docs/orchestrator/ollama/OLLAMA_HOST_FIX.md)** - Ollama host configuration fixes
- **[docs/orchestrator/ollama/RETRY_AND_QUEUE_MANAGEMENT.md](docs/orchestrator/ollama/RETRY_AND_QUEUE_MANAGEMENT.md)** - Retry logic and queue management

## Future Enhancements

### Phase 2 (Post-MVP)
- Multi-agent swarm (generator, critic, tester roles)
- Beam search (try N solutions in parallel)
- Quality-based checkpointing
- Support for MBPP, SWE-bench benchmarks

### Phase 3 (Research)
- Tree search with MCTS
- Meta-learning from past experiments
- Cost prediction models
- Comparative analysis dashboards

## Cost Analysis

The framework tracks costs across three tiers:
- **Full Frontier**: Claude Opus/Sonnet, GPT-4o ($2.50-$75 per 1M tokens)
- **Small Frontier**: GPT-4o-mini, Claude Haiku ($0.15-$4.00 per 1M tokens)
- **Local**: $0 (electricity only, not tracked)
- **Estimated frontier-only cost**: What it would cost if full frontier did all work
- **Savings**: Difference between actual and frontier-only baseline

### Cost Projections

**Per Experiment (various configurations):**
- Full frontier only: $0.10-0.15 (baseline)
- **Default (gpt-oss:20b spec + local iterations): $0.00-0.005** (96-100% savings) ✨
- Hybrid (Sonnet checkpoints): $0.002-0.01 (90-98% savings)
- Hybrid (Opus spec + small frontier iterations): $0.04-0.06 (60-70% savings)
- All small frontier: $0.01-0.02 (85-90% savings)

**Benchmark (164 problems):**
- Full frontier only: $16-25
- **Default (gpt-oss:20b + local): $0.00** (100% savings on specs) ✨
- Hybrid (gpt-oss:20b spec + Sonnet checkpoints): $0.50-1.50 (90-95% savings)
- Traditional hybrid (Sonnet spec + local): $3-5 (75-85% savings)

**Spec Generation Comparison (164 problems):**
- Claude Sonnet 4.5: $3.94 (72 minutes)
- **gpt-oss:20b: $0.00 (45 minutes)** - **37% faster, zero cost** ✨
- Savings: $3.94 + 27 minutes per benchmark

See [SPEC_REUSE_FEATURE.md](SPEC_REUSE_FEATURE.md) for detailed examples.

## License

MIT

## Contributing

Contributions welcome! This is an experimental research framework.

## Citation

If you use Koderz in research, please cite:

```bibtex
@software{koderz2025,
  title={Koderz: Multi-Model Swarm Experiment Framework},
  author={Your Name},
  year={2025},
  url={https://github.com/yourusername/koderz}
}
```
