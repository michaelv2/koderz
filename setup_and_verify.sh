#!/bin/bash

# Koderz Setup and Verification Script

set -e

echo "=========================================="
echo "Koderz Setup and Verification"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.10"
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
    echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"
else
    echo -e "${RED}✗${NC} Python 3.10+ required, found $PYTHON_VERSION"
    exit 1
fi

# Check Node.js
echo "Checking Node.js version..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -ge 18 ]; then
        echo -e "${GREEN}✓${NC} Node.js $(node --version) found"
    else
        echo -e "${YELLOW}⚠${NC} Node.js 18+ recommended, found v$NODE_VERSION"
    fi
else
    echo -e "${RED}✗${NC} Node.js not found (required for cortex-core)"
    exit 1
fi

# Check Ollama
echo "Checking Ollama..."
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓${NC} Ollama found"

    # Check if ollama service is running
    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        echo -e "${GREEN}✓${NC} Ollama service is running"

        # List available models
        MODELS=$(curl -s http://localhost:11434/api/tags | python3 -c "import sys, json; data = json.load(sys.stdin); print(','.join([m['name'] for m in data.get('models', [])]))")
        if [ -z "$MODELS" ]; then
            echo -e "${YELLOW}⚠${NC} No models installed. Run: ollama pull codellama:70b"
        else
            echo -e "${GREEN}✓${NC} Available models: $MODELS"
            if [[ "$MODELS" == *"codellama"* ]]; then
                echo -e "${GREEN}✓${NC} CodeLlama model found"
            else
                echo -e "${YELLOW}⚠${NC} CodeLlama not found. Run: ollama pull codellama:70b"
            fi
        fi
    else
        echo -e "${YELLOW}⚠${NC} Ollama not running. Start with: ollama serve"
    fi
else
    echo -e "${RED}✗${NC} Ollama not installed"
    echo "  Install: curl -fsSL https://ollama.com/install.sh | sh"
    exit 1
fi

# Check .env file
echo "Checking environment configuration..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env file exists"

    # Check required vars
    source .env
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        echo -e "${YELLOW}⚠${NC} ANTHROPIC_API_KEY not set in .env"
    else
        echo -e "${GREEN}✓${NC} ANTHROPIC_API_KEY set"
    fi

    if [ -z "$CORTEX_PATH" ]; then
        echo -e "${YELLOW}⚠${NC} CORTEX_PATH not set in .env"
    else
        if [ -f "$CORTEX_PATH" ]; then
            echo -e "${GREEN}✓${NC} CORTEX_PATH points to: $CORTEX_PATH"
        else
            echo -e "${RED}✗${NC} CORTEX_PATH file not found: $CORTEX_PATH"
        fi
    fi
else
    echo -e "${YELLOW}⚠${NC} .env file not found"
    echo "  Copy .env.example to .env and configure"
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
if command -v poetry &> /dev/null; then
    echo "Using Poetry..."
    poetry install
else
    echo "Using pip..."
    pip install -e .
fi

echo ""
echo "=========================================="
echo "Running Verification Tests"
echo "=========================================="
echo ""

# Test 1: Import test
echo "Test 1: Testing imports..."
python3 -c "
from koderz.models.local import OllamaClient
from koderz.models.frontier import FrontierClient
from koderz.cortex.client import CortexClient
from koderz.benchmarks.humaneval import HumanEval, execute_solution
from koderz.orchestrator import ExperimentOrchestrator
print('✓ All imports successful')
" && echo -e "${GREEN}✓${NC} Imports OK" || echo -e "${RED}✗${NC} Import failed"

# Test 2: HumanEval loading
echo ""
echo "Test 2: Testing HumanEval dataset..."
python3 -c "
from koderz.benchmarks.humaneval import HumanEval
humaneval = HumanEval()
count = humaneval.count()
print(f'✓ Loaded {count} HumanEval problems')
if count > 0:
    problem = humaneval.get_problem('HumanEval/0')
    print(f'✓ Sample problem: {problem[\"task_id\"]}')
" && echo -e "${GREEN}✓${NC} HumanEval OK" || echo -e "${YELLOW}⚠${NC} HumanEval dataset not fully loaded"

# Test 3: Code execution
echo ""
echo "Test 3: Testing code execution..."
python3 -c "
from koderz.benchmarks.humaneval import execute_solution

code = '''
def add(a, b):
    return a + b
'''

test = '''
assert add(2, 3) == 5
assert add(0, 0) == 0
'''

result = execute_solution(code, test)
if result['success']:
    print('✓ Code execution successful')
else:
    print('✗ Code execution failed:', result)
" && echo -e "${GREEN}✓${NC} Execution OK" || echo -e "${RED}✗${NC} Execution failed"

# Test 4: Ollama connectivity (if running)
echo ""
echo "Test 4: Testing Ollama connectivity..."
if curl -s http://localhost:11434/api/tags &> /dev/null; then
    python3 -c "
from koderz.models.local import OllamaClient

client = OllamaClient()
models = client.list_models()
print(f'✓ Connected to Ollama ({len(models)} models available)')
" && echo -e "${GREEN}✓${NC} Ollama OK" || echo -e "${YELLOW}⚠${NC} Ollama connection failed"
else
    echo -e "${YELLOW}⚠${NC} Ollama not running (skipped)"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Ensure cortex-core is built:"
echo "   cd ../claude-cortex-core && npm run build"
echo ""
echo "2. Start Ollama (if not running):"
echo "   ollama serve"
echo ""
echo "3. Pull a model (if needed):"
echo "   ollama pull codellama:70b"
echo ""
echo "4. Configure .env with your API key"
echo ""
echo "5. Run your first experiment:"
echo "   koderz run --problem-id HumanEval/0"
echo ""
echo "For help:"
echo "   koderz --help"
echo ""
