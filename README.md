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

Koderz is a Python CLI tool that orchestrates coding experiments using a swarm of local models (70B) supervised by frontier models (Claude Sonnet/Opus), with all experimental data tracked via the `claude-cortex-core` MCP server.

## Core Research Question

Can we achieve comparable results to expensive frontier models by giving cheaper local models unlimited time and iterative refinement?

## Architecture

```
┌──────────────────────────────────┐
│  koderz (Python CLI)             │
│  - Experiment orchestration      │
│  - Ollama local model client     │
│  - Anthropic API (frontier)      │
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

## Workflow

### Phase 1: Spec Generation (Frontier Model)
1. Load problem from HumanEval benchmark
2. Frontier model (Opus/Sonnet) generates detailed implementation spec
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

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-...
OLLAMA_BASE_URL=http://localhost:11434
CORTEX_PATH=/path/to/claude-cortex-core/dist/index.js
```

### Build Cortex Core

```bash
cd ../claude-cortex-core
npm install
npm run build
```

## Usage

### Run Single Experiment

```bash
koderz run --problem-id "HumanEval/0"
```

Options:
- `--local-model` - Local model to use (default: `codellama:70b`)
- `--frontier-spec-model` - Frontier for spec (default: `claude-opus-4-5`)
- `--frontier-checkpoint-model` - Frontier for checkpoints (default: `claude-sonnet-4-5`)
- `--max-iterations` - Max iterations (default: 50)
- `--checkpoint-interval` - Checkpoint every N iterations (default: 5)

### Run Benchmark

```bash
koderz benchmark --start 0 --end 10
```

Runs experiments on HumanEval problems 0-9.

### List Problems

```bash
koderz list-problems
```

### Analyze Experiment

```bash
koderz analyze exp_abc12345
```

Query cortex for experiment data. For full details, use Claude Code:

```bash
claude
> /recall query:exp_abc12345
```

## Example Output

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
  Iteration 3/50...
    ✗ Failed: AssertionError
  Iteration 4/50...
    ✗ Failed: Expected True, got False
  Iteration 5/50...
    ✗ Failed: IndexError

  Checkpoint 1...
    Guidance received from claude-sonnet-4-5

  Iteration 6/50...
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
  Actual Total: $0.0463
    - Frontier: $0.0463 (2 calls)
    - Local: $0.0000 (8 calls)

  Frontier-Only Estimate: $0.1368
  Savings: $0.0905 (66.2%)

  Total Iterations: 8
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
│   │   ├── local.py        # Ollama client
│   │   └── frontier.py     # Anthropic API client
│   ├── cortex/
│   │   └── client.py       # MCP client for cortex-core
│   ├── benchmarks/
│   │   └── humaneval.py    # HumanEval loader & executor
│   ├── analysis/
│   │   └── cost.py         # Cost analysis
│   └── data/
│       └── HumanEval.jsonl # Place dataset here
└── tests/
    └── test_orchestrator.py
```

## Verification Tests

### Test 1: MCP Connection

```bash
python -c "
from koderz.cortex.client import CortexClient
import asyncio
import os

async def test():
    cortex = CortexClient(os.getenv('CORTEX_PATH'))
    result = await cortex.remember(
        title='Test memory',
        content='Testing MCP connection',
        category='note'
    )
    print(f'Memory created: {result}')

asyncio.run(test())
"
```

### Test 2: Ollama Integration

```bash
python -c "
from koderz.models.local import OllamaClient

client = OllamaClient()
response = client.generate('Write a function that adds two numbers', model='codellama:70b')
print(response)
"
```

### Test 3: Frontier API

```bash
python -c "
from koderz.models.frontier import FrontierClient
import os

client = FrontierClient(os.getenv('ANTHROPIC_API_KEY'))
result = client.generate_spec('Write a function that checks if a number is prime')
print(f'Spec: {result[\"spec\"][:200]}...')
print(f'Cost: \${result[\"cost\"]:.4f}')
"
```

### Test 4: HumanEval Execution

```bash
python -c "
from koderz.benchmarks.humaneval import execute_solution

solution = '''
def has_close_elements(numbers, threshold):
    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            if abs(numbers[i] - numbers[j]) < threshold:
                return True
    return False
'''

test = '''
def check(candidate):
    assert candidate([1.0, 2.0, 3.9, 4.0], 0.3) == True
    assert candidate([1.0, 2.0, 3.9, 4.0], 0.05) == False
    assert candidate([1.0, 2.0, 5.9, 4.0], 0.95) == True

check(has_close_elements)
'''

result = execute_solution(solution, test)
print(f'Tests passed: {result[\"success\"]}')
"
```

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

The framework tracks:
- **Frontier costs**: API calls to Claude Opus/Sonnet
- **Local costs**: $0 (electricity only, not tracked)
- **Estimated frontier-only cost**: What it would cost if frontier did all work
- **Savings**: Difference between actual and frontier-only cost

Example from successful experiment:
- Actual cost: $0.05 (spec + 1 checkpoint)
- Frontier-only estimate: $0.15 (3 iterations × $0.05)
- **Savings: 66%**

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
