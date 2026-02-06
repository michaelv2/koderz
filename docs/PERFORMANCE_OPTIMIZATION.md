# Performance Optimization Report

This document describes the performance optimizations implemented for koderz benchmark execution.

## Summary

Three key optimizations were implemented to reduce benchmark execution time:

| Optimization | Impact | Status |
|--------------|--------|--------|
| Persistent Cortex connection | ~80% reduction in Cortex overhead | Implemented |
| Timing instrumentation | Enables measurement | Implemented |
| Parallel problem execution | Configurable concurrency | Implemented |

## Optimizations

### 1. Persistent Cortex Connection

**Problem**: Each Cortex operation (remember, recall, export_memories, etc.) was spawning a new Node.js subprocess, initializing the MCP connection, and then closing it. This overhead was significant - each operation took ~1-2 seconds.

**Solution**: Added async context manager support to `CortexClient` that maintains a single persistent MCP connection across all operations within a benchmark run.

**Usage**:
```bash
# Enabled by default
koderz benchmark --start 0 --end 10 --local-model gpt-4o-mini

# Disable for debugging
koderz benchmark --start 0 --end 10 --no-persistent-cortex
```

**Implementation**:
- Added `__aenter__` and `__aexit__` methods to `CortexClient`
- Added `_call_tool()` helper that uses persistent session when available
- Refactored all methods to use `_call_tool()`
- Updated CLI benchmark command to use `async with` for persistent connection

### 2. Timing Instrumentation

**Problem**: No visibility into where time was being spent during benchmark execution.

**Solution**: Created `BenchmarkTimer` class that tracks per-phase timing with context manager pattern.

**Usage**:
```bash
# Print timing breakdown at end
koderz benchmark --start 0 --end 10 --timing-report

# Export to JSON file
koderz benchmark --start 0 --end 10 --timing-export timing.json

# Both
koderz benchmark --start 0 --end 10 --timing-report --timing-export results/timing.json
```

**Categories tracked**:
- `cortex_*`: All Cortex MCP operations
- `iteration_generate`: Model generation time
- `iteration_test`: Test execution time
- `spec_generation`: Specification generation
- `checkpoint_review`: Checkpoint model reviews

**Example output**:
```
============================================================
TIMING BREAKDOWN
============================================================
Total Duration: 45.23s
Tracked Time:   42.15s
Overhead:       3.08s

By Category:
----------------------------------------
  cortex           8.45s  (18.7%)
  iteration       28.32s  (62.6%)
  spec             5.12s  (11.3%)
  checkpoint       0.26s  ( 0.6%)
  other            0.00s  ( 0.0%)

Top 5 Phase Types:
----------------------------------------
  iteration_generate      25.12s  (55.5%)
  cortex_remember          5.23s  (11.6%)
  spec_generation          5.12s  (11.3%)
  iteration_test           3.20s  ( 7.1%)
  cortex_start_session     1.85s  ( 4.1%)
============================================================
```

### 3. Parallel Problem Execution

**Problem**: Problems were executed sequentially, limiting throughput.

**Solution**: Added `--concurrency N` flag that uses `asyncio.Semaphore` to limit concurrent problem execution.

**Usage**:
```bash
# Sequential (default)
koderz benchmark --start 0 --end 20

# 2 concurrent problems
koderz benchmark --start 0 --end 20 --concurrency 2

# 4 concurrent problems
koderz benchmark --start 0 --end 20 --concurrency 4
```

**Constraints**:
- SQLite (Cortex database) has write locking - high concurrency may cause contention
- Ollama queues requests on a single GPU - concurrency helps with API models more than local models
- Start with `--concurrency 2` for testing, increase based on system resources

**Implementation**:
- Uses `asyncio.Semaphore(N)` to limit concurrent tasks
- Uses `asyncio.gather()` for parallel execution
- Results maintain original order despite parallel execution

## New CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `--timing-report` | off | Print timing breakdown at end |
| `--timing-export FILE` | none | Export timing data to JSON |
| `--persistent-cortex/--no-persistent-cortex` | on | Use persistent MCP connection |
| `--concurrency N` | 1 | Number of parallel problems |

## Files Changed

| File | Changes |
|------|---------|
| `koderz/analysis/timing.py` | New file: BenchmarkTimer class |
| `koderz/analysis/__init__.py` | Export timing utilities |
| `koderz/cortex/client.py` | Added async context manager support |
| `koderz/orchestrator.py` | Added timer parameter and instrumentation |
| `koderz/cli.py` | Added new CLI options, async benchmark runner |
| `tests/test_timing.py` | New file: timing tests |
| `tests/test_cortex_persistent.py` | New file: persistent connection tests |
| `tests/test_parallel_benchmark.py` | New file: parallel execution tests |

## Expected Improvements

Based on implementation analysis:

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Cortex overhead per operation | ~1-2s | ~0.1s | ~90% |
| Cortex total (20 problems) | ~5+ min | ~30s | ~80%+ |
| Overall benchmark (20 problems) | varies | varies | ~20%+ |

Actual improvements will depend on:
- Number of problems
- Evaluation mode (zero-shot vs iterative)
- Model response times
- System resources

## Verification

Run the timing report to verify improvements:

```bash
# Baseline measurement
poetry run koderz benchmark --start 0 --end 5 --local-model gpt-4o-mini \
  --mode zero-shot --no-spec --timing-report

# Compare with different settings
poetry run koderz benchmark --start 0 --end 5 --local-model gpt-4o-mini \
  --mode zero-shot --no-spec --timing-report --concurrency 2
```

## Recommendations for Further Optimization

1. **Connection pooling for API models**: If using multiple API providers, consider connection pooling
2. **Result caching**: Cache successful solutions to skip on re-runs
3. **Lazy embedding**: Defer embedding generation for non-search scenarios
4. **Batched operations**: Combine multiple Cortex remember calls into single batch
