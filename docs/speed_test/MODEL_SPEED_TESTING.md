# Model Speed Testing

## Overview

The `koderz speed-test` command benchmarks local model inference speed by testing each model with a standardized set of prompts and measuring tokens/second throughput.

## Purpose

When running koderz experiments, different local models have vastly different inference speeds. This tool helps you:

1. **Measure actual performance** - Get real-world tokens/sec for your hardware
2. **Compare models** - See which models are fastest for your use case
3. **Estimate experiment time** - Predict how long benchmarks will take
4. **Make informed choices** - Balance quality vs. speed trade-offs

## Warmup Feature

**Default: Enabled**

When ollama loads a model for the first time, it reads it from disk into memory (GPU/RAM), which can take 5-30+ seconds depending on model size. This loading time contaminates speed measurements.

The warmup feature:
- Runs a quick prompt ("Write a haiku about computers") before each model test
- Loads the model into memory during warmup
- Discards warmup results
- Measures actual inference speed on subsequent prompts

**Why it matters:**
- **Without warmup:** First prompt = loading time + inference (slow, inaccurate)
- **With warmup:** All prompts = pure inference speed (fast, accurate)

Use `--no-warmup` only if you want to measure total time including model loading.

## Usage

### Basic Usage

Test a single model (with warmup enabled by default):
```bash
poetry run koderz speed-test qwen2.5-coder:32b
```

Test multiple models:
```bash
poetry run koderz speed-test qwen2.5-coder:32b deepseek-coder:33b codellama:70b
```

Test without warmup (includes model loading time):
```bash
poetry run koderz speed-test qwen2.5-coder:32b --no-warmup
```

### Export Results

Save results to JSON for later analysis:
```bash
poetry run koderz speed-test qwen2.5-coder:32b --export speed_results.json
```

### Custom Ollama Host

The command uses the `OLLAMA_HOST` environment variable by default. You can override it with `--host`:

```bash
# Uses OLLAMA_HOST env var (or defaults to http://localhost:11434)
poetry run koderz speed-test qwen2.5-coder:32b

# Override with --host flag
poetry run koderz speed-test qwen2.5-coder:32b --host http://192.168.1.100:11434
```

## Test Prompts

Each model is tested with three standardized prompts:

### 1. Historical Essay (200 words)
- **Type:** Long-form text generation
- **Purpose:** Tests sustained generation capability
- **Typical tokens:** 200-300

### 2. Coding Problem
- **Type:** Code generation with comments
- **Purpose:** Tests structured output and code understanding
- **Typical tokens:** 100-200

### 3. Brain Teaser
- **Type:** Logical reasoning
- **Purpose:** Tests reasoning and explanation quality
- **Typical tokens:** 150-250

## Metrics

### Tokens/Second
- **Definition:** Number of output tokens generated per second
- **Calculation:** `tokens_generated / eval_duration`
- **Use:** Primary speed metric - higher is faster

### Total Time
- **Definition:** Wall-clock time for all prompts
- **Use:** Estimate total benchmark runtime

### Relative Speed
- **Definition:** Speed compared to slowest model in the test
- **Use:** Quick comparison - "2.5x faster than X"

## Output

### Summary Table
```
MODEL SPEED BENCHMARK RESULTS
==================================================
Model                          | Avg Tokens/sec | Total Time (s) | Relative Speed
-------------------------------+----------------+----------------+----------------
qwen2.5-coder:32b             |          45.23 |          25.12 |          2.15x
deepseek-coder:33b            |          38.10 |          29.45 |          1.81x
codellama:70b                 |          21.05 |          53.20 |          1.00x
```

### Detailed Breakdown
```
qwen2.5-coder:32b
-------------------------------
Prompt                              | Tokens    | Tokens/sec     | Time (s)
------------------------------------+-----------+----------------+----------
Historical Essay (200 words)        |       245 |          42.15 |     5.81
Coding Problem                      |       187 |          48.32 |     3.87
Brain Teaser                        |       213 |          45.22 |     4.71
```

## JSON Export Format

```json
{
  "timestamp": "2026-01-31 12:34:56",
  "models": [
    {
      "model": "qwen2.5-coder:32b",
      "avg_tokens_per_sec": 45.23,
      "total_time_sec": 25.12,
      "prompts": [
        {
          "name": "Historical Essay (200 words)",
          "tokens_generated": 245,
          "tokens_per_sec": 42.15,
          "total_time_sec": 5.81,
          "eval_duration_ns": 5813245123,
          "prompt_eval_duration_ns": 123456789,
          "total_duration_ns": 5936701912
        }
      ]
    }
  ]
}
```

## Use Cases

### 1. Estimating Benchmark Time

If a model generates 40 tokens/sec and your problems average 150 tokens per solution:

```
Time per problem = 150 tokens / 40 tokens/sec = 3.75 seconds
Time for 164 problems = 164 * 3.75 = 615 seconds ≈ 10 minutes
```

**Note:** This is pure generation time. Add testing time, prompt processing, and iteration overhead.

### 2. Comparing Model Efficiency

Find the best speed/quality trade-off:
```bash
# Test all your models
poetry run koderz speed-test \
    qwen2.5-coder:7b \
    qwen2.5-coder:14b \
    qwen2.5-coder:32b \
    --export comparison.json
```

### 3. Hardware Optimization

Test before/after hardware changes:
```bash
# Before GPU upgrade
poetry run koderz speed-test qwen2.5-coder:32b --export before.json

# After GPU upgrade
poetry run koderz speed-test qwen2.5-coder:32b --export after.json

# Compare
diff <(jq '.models[0].avg_tokens_per_sec' before.json) \
     <(jq '.models[0].avg_tokens_per_sec' after.json)
```

## Implementation Details

### Ollama API Metrics

The speed test uses ollama's built-in timing metrics:

- `eval_count` - Number of tokens generated
- `eval_duration` - Time (nanoseconds) to generate tokens
- `prompt_eval_duration` - Time (nanoseconds) to process prompt
- `total_duration` - Total time (nanoseconds)

### Calculation

```python
tokens_per_sec = (eval_count / eval_duration) * 1e9
```

This gives pure **generation speed**, excluding prompt processing.

## Tips

### Warm Up Models

First run may be slower (model loading):
```bash
# Warm up
poetry run koderz speed-test qwen2.5-coder:32b

# Real test
poetry run koderz speed-test qwen2.5-coder:32b --export results.json
```

### Consistent Environment

For accurate comparisons:
- Close other applications
- Ensure GPU isn't being used elsewhere
- Run tests at similar times (thermal throttling)
- Use same ollama version

### Batch Testing

Test all models at once:
```bash
# List available models
ollama list

# Test all at once
poetry run koderz speed-test \
    $(ollama list | tail -n +2 | awk '{print $1}') \
    --export all_models.json
```

## Integration with Benchmarks

Use speed test results to estimate benchmark duration:

```bash
# 1. Test model speed
poetry run koderz speed-test qwen2.5-coder:32b --export speed.json

# 2. Extract tokens/sec
SPEED=$(jq '.models[0].avg_tokens_per_sec' speed.json)

# 3. Estimate benchmark time
# Assume 200 tokens per solution, 164 problems, avg 3 iterations
echo "Estimated time: $(echo "164 * 3 * 200 / $SPEED / 60" | bc) minutes"

# 4. Run benchmark
poetry run koderz benchmark 0 164 --local-model qwen2.5-coder:32b
```

## Limitations

### Not Included in Timing
- Prompt processing time (separate metric)
- Test execution time
- Cortex memory operations
- Network latency (for remote ollama)

### Prompt Variability
- Real koderz prompts may be longer/shorter
- Complexity affects generation speed
- Standard prompts are representative, not identical

### Hardware Factors
- GPU memory affects batch processing
- CPU/GPU balance varies by model
- Thermal throttling during long runs

## Example Workflow

Complete workflow for model selection:

```bash
# 1. Test all available models
poetry run koderz speed-test \
    qwen2.5-coder:7b \
    qwen2.5-coder:14b \
    qwen2.5-coder:32b \
    deepseek-coder:6.7b \
    deepseek-coder:33b \
    --export model_speeds.json

# 2. Review results
cat model_speeds.json | jq '.models[] | {model: .model, speed: .avg_tokens_per_sec}'

# 3. Run small benchmark with fastest model
FASTEST=$(cat model_speeds.json | jq -r '.models | sort_by(-.avg_tokens_per_sec) | .[0].model')
poetry run koderz benchmark 0 10 --local-model $FASTEST

# 4. Compare quality vs speed
# Choose the best balance for your needs
```

## Summary

The speed test command helps you:
- ✅ Measure real-world model performance
- ✅ Compare models objectively
- ✅ Estimate experiment duration
- ✅ Optimize hardware utilization
- ✅ Make data-driven model choices

Use it before running large benchmarks to understand the time commitment and choose the right model for your needs.
