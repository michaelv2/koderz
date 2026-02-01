# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Koderz is a multi-model swarm experiment framework that orchestrates coding experiments using local models (via Ollama) or small frontier models for iterations, supervised by frontier models (Claude Sonnet/Opus) for checkpoints. All experimental data is tracked via the `claude-cortex-core` MCP server.

**Core Research Question**: Can cheaper local/small frontier models achieve comparable results to expensive frontier models when given unlimited time and iterative refinement?

## Development Commands

### Environment Setup

```bash
# Install dependencies
poetry install

# Configure environment variables (or use .env file)
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-proj-...  # Optional, for GPT-4o/GPT-4o-mini
export OLLAMA_HOST=http://localhost:11434
export CORTEX_PATH=/path/to/claude-cortex-core/dist/index.js
```

### Running Experiments

```bash
# Single experiment (default: gpt-oss:20b spec, local iterations)
poetry run koderz run --problem-id "HumanEval/0"

# With specific models
poetry run koderz run --problem-id "HumanEval/0" \
  --frontier-spec-model "gpt-oss:20b" \
  --local-model "qwen2.5-coder:32b" \
  --frontier-checkpoint-model "claude-sonnet-4-5"

# Run benchmark suite
poetry run koderz benchmark --start 0 --end 10 --local-model "gpt-4o-mini"

# Enable debug mode (saves all outputs)
poetry run koderz run --problem-id "HumanEval/0" --debug --debug-dir ./debug_output
```

### Testing

```bash
# Run specific tests
poetry run python -m pytest tests/test_orchestrator.py -v
poetry run python -m pytest tests/test_spec_validation_gptoss.py -v

# Quick verification
poetry run python -c "
from koderz.models.factory import ModelFactory
from koderz.cortex.client import CortexClient
print('✓ All imports successful')
"

# List available problems
poetry run koderz list-problems
```

### Long-Running Tasks with Slack Notifications

```bash
# Setup: Add SLACK_WEBHOOK_URL to .env
# Run benchmark with notifications
./notify-on-complete.sh poetry run koderz benchmark --start 0 --end 164
```

## Architecture

### High-Level Flow

1. **Spec Generation** (Phase 1): Frontier model (default: gpt-oss:20b) generates detailed implementation spec
2. **Iterative Execution** (Phase 2): Local/small frontier model attempts solution, tests against HumanEval, retries on failure
3. **Checkpoints** (Phase 3): Every N iterations, frontier model reviews attempts and provides guidance
4. **Completion** (Phase 4): Cost analysis comparing actual vs frontier-only baseline

### Key Components

**ExperimentOrchestrator** (`koderz/orchestrator.py`):
- Main workflow coordination for all 4 phases
- Manages debug output when enabled
- Coordinates between model clients and Cortex MCP server
- Handles spec reuse logic and cost tracking
- Implements zero-shot vs iterative evaluation modes

**ModelFactory** (`koderz/models/factory.py`):
- Factory pattern for creating appropriate model clients
- Caches client instances (Ollama, Anthropic, OpenAI)
- Routes to correct provider based on model name
- Manages context window settings (default: 5120 tokens, tuned from checkpoint data)

**Model Clients**:
- `OllamaClient` (`koderz/models/local.py`): Local models via Ollama API (gpt-oss:20b, codellama:70b, qwen2.5-coder:32b, llama3.3:70b)
- `FrontierClient` (`koderz/models/frontier.py`): Anthropic API for Claude models
- `OpenAIClient` (`koderz/models/openai_client.py`): OpenAI API for GPT-4o/GPT-4o-mini

**Model Registry** (`koderz/models/registry.py`):
- Centralized model metadata: provider, tier (local/small_frontier/full_frontier), pricing
- Used by cost analyzer and factory for routing

**CortexClient** (`koderz/cortex/client.py`):
- MCP client for `claude-cortex-core` server
- Stores specs, iterations, checkpoints, results in semantic memory
- Methods: `remember()`, `recall()`, `export_memories()`, `start_session()`, `end_session()`
- Each method creates ephemeral stdio connection to cortex subprocess

**HumanEval** (`koderz/benchmarks/humaneval.py`):
- Loads problems from JSONL
- `execute_solution()`: Runs code in isolated subprocess with timeout
- `verify_solution()`: Validates solution format and test assertions
- Returns detailed error messages for debugging

**CostAnalyzer** (`koderz/analysis/cost.py`):
- Tracks costs by tier (local=free, small_frontier, full_frontier)
- Calculates savings vs frontier-only baseline
- Aggregates costs across benchmark runs

**Code Extraction** (`koderz/utils/code_extraction.py`):
- Extracts Python code from markdown fenced blocks or plain text
- Validates syntax using AST before execution
- Critical for handling model outputs wrapped in markdown

### Three-Tier Model System

1. **Local** (Free): Ollama models - gpt-oss:20b, codellama:70b, llama3.3:70b, qwen2.5-coder:32b
2. **Small Frontier** (Cheap): GPT-4o-mini ($0.15/$0.60 per 1M), Claude Haiku ($0.80/$4.00 per 1M)
3. **Full Frontier** (Expensive): Claude Opus ($15/$75 per 1M), Claude Sonnet ($3/$15 per 1M), GPT-4o ($2.50/$10 per 1M)

### Spec Reuse Feature

Use `--reuse-spec` to retrieve existing spec from Cortex instead of regenerating:
- Queries Cortex for memories tagged with `["spec", problem_id]`
- Saves 60-75% on costs for multi-model comparisons
- Falls back to generation if no spec found

### Debug Mode

When `--debug` is enabled:
- Saves raw model outputs: `{exp_id}_iter{N}_raw.txt`
- Saves extracted code: `{exp_id}_iter{N}_code.py`
- Saves test results: `{exp_id}_iter{N}_result.txt`
- Saves checkpoint guidance files
- Adds detailed INFO/DEBUG/WARNING log messages

## Important Patterns

### Model Selection

**Default (Recommended)**: gpt-oss:20b for specs (validated 100% first-try success, 37% faster than Sonnet, zero cost)

When adding new model support:
1. Add model metadata to `koderz/models/registry.py` (provider, tier, pricing)
2. Factory pattern (`ModelFactory.get_client()`) will automatically route to correct client
3. Update CLI help text in `koderz/cli.py` if model is recommended default

### Cost Tracking

All model calls must report cost:
```python
# In model clients
result = {
    "spec": generated_spec,
    "cost": calculate_cost(input_tokens, output_tokens),
    "model": model_name
}

# In orchestrator
self.cost_analyzer.add_cost(
    amount=result["cost"],
    model=model_name,
    phase="spec_generation"  # or "iteration", "checkpoint"
)
```

### Cortex Memory Structure

**Specs**: `category="architecture"`, `tags=["spec", problem_id]`, metadata includes model, cost
**Iterations**: `category="note"`, `tags=["iteration", exp_id]`, metadata includes iteration_number, success, error
**Checkpoints**: `category="learning"`, `tags=["checkpoint", exp_id]`, metadata includes iteration_range
**Results**: `category="note"`, `tags=["result", exp_id]`, metadata includes full cost breakdown

### Async Context Managers

CortexClient does NOT use async context manager pattern. Each method call creates ephemeral stdio connection:
```python
# Correct usage
cortex = CortexClient(cortex_path)
await cortex.remember(...)
await cortex.recall(...)

# NOT supported
async with CortexClient(cortex_path) as cortex:  # Won't work
```

## Validation & Quality Standards

- **gpt-oss:20b default for specs**: Validated 100% first-try success on 20 HumanEval problems (see `docs/orchestrator/spec_generation/SPEC_VALIDATION_GPTOSS.md`)
- **Context window**: 5120 tokens default (tuned from checkpoint guidance max 902 tokens, see `docs/CONTEXT_WINDOW_MANAGEMENT.md`)
- **Checkpoint guidance**: Now includes test-aware analysis (recent vs historical failures, systematic debugging steps)
- **Code extraction**: Always validate with AST before execution

## Key Design Principles

1. **Model-agnostic workflow**: Any model can be used for any phase (spec/iterations/checkpoints)
2. **Cost transparency**: Track and report costs by tier, compare to frontier-only baseline
3. **Iterative refinement**: Give cheaper models unlimited attempts with guidance
4. **Memory persistence**: All experiment data stored in Cortex for analysis
5. **Progressive disclosure**: Start with minimal spec, expand if needed (experimental feature)

## Recent Changes

- Adopted gpt-oss:20b as default spec model (100% success rate validated)
- Optimized context window from 8K→5K based on real checkpoint data
- Enhanced checkpoint guidance with test-aware analysis
- Added progressive spec disclosure (minimal initial specs)
- Integrated Slack notifications for long-running tasks
