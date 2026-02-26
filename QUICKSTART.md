# Koderz Quick Start Guide

Get up and running with Koderz in 5 minutes.

## Prerequisites

- Python 3.10+ with Poetry
- Node.js 18+
- Anthropic API key (required for checkpoints)
- OpenAI API key (optional, for GPT-4o-mini)

## 1. Install Dependencies

```bash
cd koderz
poetry install
```

## 2. Install Ollama (recommended — enables zero-cost experiments)

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
ollama pull gpt-oss:20b        # Spec generation (validated 100% success)
ollama pull qwen2.5-coder:32b  # Code iterations
```

Skip this step if you prefer API-only models (GPT-4o-mini, Claude Haiku).

## 3. Build Cortex Core

```bash
cd ../claude-cortex-core
npm install && npm run build
cd ../koderz
```

## 4. Configure Environment

```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
export OPENAI_API_KEY=sk-proj-your-key-here       # Optional
export OLLAMA_HOST=http://localhost:11434
export CORTEX_PATH=/full/path/to/claude-cortex-core/dist/index.js
```

Add these to `~/.bashrc` or `~/.zshrc` to persist, or use `cp .env.example .env` and edit the file.

## 5. Run Your First Experiment

```bash
poetry run koderz run --problem-id "HumanEval/0"
```

This uses gpt-oss:20b for specs (free), codellama:70b for iterations (free), and claude-sonnet-4-5 for checkpoints (paid). You should see iterative attempts followed by a cost analysis summary.

For a completely free run (no API calls):

```bash
poetry run koderz run --problem-id "HumanEval/0" \
  --frontier-spec-model "gpt-oss:20b" \
  --local-model "qwen2.5-coder:32b" \
  --frontier-checkpoint-model "gpt-oss:20b"
```

## 6. Run a Small Benchmark

```bash
poetry run koderz benchmark --start 0 --end 5 --local-model "gpt-4o-mini"
```

Results are saved to `benchmark_results/` as JSON.

## Troubleshooting

**"Ollama not running"** — Start it with `ollama serve &` and verify with `curl http://localhost:11434/api/tags`.

**"Model not found"** — Pull the model first: `ollama pull codellama:70b`

**"ANTHROPIC_API_KEY not set"** — Export it or add it to your `.env` file.

**"Cortex path not found"** — Rebuild with `cd ../claude-cortex-core && npm run build`, then set `CORTEX_PATH` to the full path of `dist/index.js`.

**Python / Poetry issues** — If using pyenv, run `pyenv local 3.11.10` in the koderz directory, then `poetry install`.

## Next Steps

- `koderz list-problems` — Browse available problems
- `koderz --help` — See all commands and options
- [README.md](README.md) — Full usage guide, all CLI options, benchmark examples, speed test results
- [ARCHITECTURE.md](ARCHITECTURE.md) — Technical deep dive into components and data flow
