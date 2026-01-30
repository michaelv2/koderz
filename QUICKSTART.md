# Koderz Quick Start Guide

Get up and running with Koderz in 5 minutes.

## Prerequisites

- Python 3.10+
- Node.js 18+
- Anthropic API key

## Installation

### 1. Install Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve &

# Pull CodeLlama model (this may take a while, ~38GB)
ollama pull codellama:70b

# Or use a smaller model for testing
ollama pull codellama:7b
```

### 2. Build Cortex Core

```bash
cd ../claude-cortex-core
npm install
npm run build
cd ../koderz
```

### 3. Install Koderz

```bash
# Run automated setup
./setup_and_verify.sh

# Or manually:
pip install -e .
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
OLLAMA_BASE_URL=http://localhost:11434
CORTEX_PATH=/full/path/to/claude-cortex-core/dist/index.js
```

## Your First Experiment

### Run a Single Problem

```bash
koderz run --problem-id "HumanEval/0"
```

This will:
1. Load problem HumanEval/0 (checking if two numbers are close)
2. Generate a spec using Claude Opus
3. Iteratively try solutions with CodeLlama
4. Checkpoint with Claude Sonnet every 5 iterations
5. Show cost analysis when complete

### Example Output

```
============================================================
Starting Experiment: exp_a1b2c3d4
Problem: HumanEval/0
============================================================

Phase 1: Generating spec with claude-opus-4-5...
  Spec generated (cost: $0.0342)
  Stored in cortex

Phase 2: Iterative execution with codellama:70b...
  Iteration 1/50...
    ✗ Failed: IndexError: list index out of range
  Iteration 2/50...
    ✗ Failed: Expected True, got False
  ...
  Iteration 8/50...
    ✓ SUCCESS! All tests passed.

============================================================
Experiment Complete: exp_a1b2c3d4
============================================================
Success: True
Iterations: 8

Cost Analysis:
  Actual Total: $0.0463
    - Frontier: $0.0463 (2 calls)
    - Local: $0.0000 (8 calls)

  Frontier-Only Estimate: $0.1368
  Savings: $0.0905 (66.2%)
```

## Common Commands

### List Available Problems

```bash
koderz list-problems
```

### Run with Different Models

```bash
# Use smaller local model for testing
koderz run --problem-id "HumanEval/0" --local-model "codellama:7b"

# Use Sonnet for spec (cheaper)
koderz run --problem-id "HumanEval/0" --frontier-spec-model "claude-sonnet-4-5"

# Adjust checkpoint frequency
koderz run --problem-id "HumanEval/0" --checkpoint-interval 10
```

### Run a Benchmark

```bash
# Test on first 5 problems
koderz benchmark --start 0 --end 5
```

### Analyze an Experiment

```bash
# Get experiment ID from run output
koderz analyze exp_a1b2c3d4

# Or view in Claude Code with cortex loaded
claude
> /recall query:exp_a1b2c3d4
```

## Troubleshooting

### "Ollama not running"

```bash
# Start Ollama
ollama serve
```

### "Model not found"

```bash
# Check available models
ollama list

# Pull missing model
ollama pull codellama:70b
```

### "ANTHROPIC_API_KEY not set"

```bash
# Edit .env file
nano .env

# Add your key
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### "Cortex path not found"

```bash
# Build cortex-core first
cd ../claude-cortex-core
npm run build

# Update .env with correct path
CORTEX_PATH=/full/path/to/claude-cortex-core/dist/index.js
```

### Python import errors

```bash
# Reinstall dependencies
pip install -e .

# Or with Poetry
poetry install
```

## Understanding the Output

### Cost Analysis

- **Actual Total**: What you actually paid (frontier calls only)
- **Frontier Cost**: Cost of Claude API calls (spec + checkpoints)
- **Local Cost**: $0 (local models are free)
- **Frontier-Only Estimate**: What it would cost if Claude did all iterations
- **Savings**: Money saved by using hybrid approach

### Iterations

- Each iteration = 1 attempt by local model
- Checkpoints occur every N iterations (default 5)
- Experiments end when:
  - Tests pass (success!)
  - Max iterations reached (failure)

## Next Steps

1. **Try different problems**: `koderz list-problems`
2. **Experiment with models**: Try different local/frontier combinations
3. **Run benchmarks**: Test on multiple problems
4. **Analyze in Claude Code**: Use cortex to explore experiment data

## Getting Help

```bash
# General help
koderz --help

# Command-specific help
koderz run --help
koderz benchmark --help
```

## Advanced Usage

### Custom Checkpoint Logic

Edit `koderz/orchestrator.py`:

```python
# Change checkpoint interval dynamically
if iteration > 20:
    self.checkpoint_interval = 3  # More frequent after iteration 20
```

### Custom Prompts

Edit `_build_iteration_prompt()` in `orchestrator.py` to customize how problems are presented to the local model.

### Add More Benchmarks

Extend `koderz/benchmarks/` with new benchmark loaders (MBPP, SWE-bench, etc.).

## Tips for Best Results

1. **Start small**: Use `codellama:7b` for testing, `codellama:70b` for real experiments
2. **Adjust checkpoints**: More frequent = more guidance but higher cost
3. **Monitor costs**: Check cost analysis after each run
4. **Use cortex**: All experiment data is in cortex - query it for insights
5. **Iterate on prompts**: Tweak iteration prompts for better local model performance

Happy experimenting! 🚀
