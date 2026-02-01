# Retry Logic and Queue Management

Koderz now includes automatic retry logic with exponential backoff to handle Ollama server overload and timeout scenarios gracefully.

## Overview

When running multiple concurrent benchmarks or testing large models under heavy load, Ollama may experience:
- Request timeouts (taking longer than expected to respond)
- Server overload (503 errors when queue is full)
- Connection errors (temporary network issues)

The retry system automatically handles these transient failures without crashing your benchmarks.

## How It Works

### Automatic Retry with Exponential Backoff

When a request fails due to timeout or overload:

1. **Initial retry**: Wait 2 seconds, try again
2. **Second retry**: Wait 4 seconds, try again
3. **Third retry**: Wait 8 seconds, try again
4. **Subsequent retries**: Wait up to 60 seconds max between attempts

This exponential backoff gives Ollama time to recover from temporary overload while preventing thundering herd problems.

### Retryable Errors

The system automatically retries on:
- **ReadTimeout**: Request took longer than timeout limit (default: 300s)
- **HTTP 503**: Server overloaded (queue full)
- **HTTP 429**: Too many requests (rate limited)
- **ConnectionError**: Temporary network issues

Non-retryable errors (404, 400, etc.) fail immediately without retry.

## Configuration

### CLI Options

All koderz commands that interact with Ollama support these options:

```bash
--timeout INTEGER        # Request timeout in seconds (default: 300)
--max-retries INTEGER    # Maximum retry attempts (default: 3)
```

### Examples

**Benchmark with custom timeout and retries:**
```bash
koderz benchmark \
  --start 0 --end 164 \
  --local-model qwen2.5-coder:32b \
  --timeout 600 \
  --max-retries 5
```

**Speed test with aggressive retries:**
```bash
koderz speed-test qwen2.5-coder:32b deepseek-coder:33b \
  --timeout 600 \
  --max-retries 10
```

**Single problem run with no retries:**
```bash
koderz run \
  --problem-id HumanEval/0 \
  --local-model codellama:70b \
  --max-retries 0
```

## Best Practices for High-Load Scenarios

### 1. Adjust Timeout Based on Model Size

Larger models need more time:

```bash
# Small models (7B)
--timeout 180

# Medium models (13-34B)
--timeout 300  # default

# Large models (70B+)
--timeout 600
```

### 2. Increase Retries Under Heavy Load

When running multiple benchmarks simultaneously:

```bash
# Conservative (default)
--max-retries 3

# Under moderate load (2-3 concurrent tasks)
--max-retries 5

# Under heavy load (4+ concurrent tasks)
--max-retries 10
```

### 3. Monitor Ollama Queue

Check what's running:
```bash
curl http://llm-server:11434/api/ps
```

Watch in real-time:
```bash
watch -n 2 'curl -s http://llm-server:11434/api/ps'
```

### 4. Optimize Ollama Configuration

For your 2×3090 setup with 96GB RAM:

```bash
# /etc/systemd/system/ollama.service.d/override.conf
[Service]
Environment="OLLAMA_NUM_PARALLEL=4"
Environment="OLLAMA_MAX_LOADED_MODELS=5"
Environment="OLLAMA_MAX_QUEUE=256"
Environment="OLLAMA_KEEP_ALIVE=30m"
Environment="OLLAMA_FLASH_ATTENTION=1"
```

See [Ollama configuration guide](OLLAMA_CONFIGURATION.md) for details.

## Error Handling

### Graceful Degradation

When a benchmark problem fails after all retries:
- **Speed benchmark**: Skips to next model, reports failure at end
- **HumanEval benchmark**: Logs failure, continues to next problem
- **Single run**: Reports failure with details, exits with error code

### Failure Reporting

After benchmark completes, you'll see a summary of failures:

```
⚠ 2 model(s) failed:
  • codellama:70b: Max retries exceeded: ReadTimeout (300s)
  • deepseek-coder:33b: HTTPError: 503 Server Overloaded
```

### Logs

Retry attempts are logged automatically:

```
WARNING: Attempt 1/4 failed for generate: ReadTimeout (300s). Retrying in 2.0s...
WARNING: Attempt 2/4 failed for generate: ReadTimeout (300s). Retrying in 4.0s...
```

Enable debug logging to see full details:
```bash
export LOG_LEVEL=DEBUG
koderz benchmark ...
```

## Programmatic Usage

### Using retry decorator directly

```python
from koderz.utils.retry import retry_with_backoff, MaxRetriesExceeded

@retry_with_backoff(
    max_retries=5,
    initial_delay=2.0,
    backoff_factor=2.0,
    max_delay=60.0
)
def my_ollama_call():
    # Your Ollama API call here
    response = requests.post(...)
    return response.json()

try:
    result = my_ollama_call()
except MaxRetriesExceeded as e:
    print(f"Failed after all retries: {e}")
```

### Checking for overload

```python
from koderz.utils.retry import is_ollama_overloaded

try:
    response = ollama_client.generate(...)
except Exception as e:
    if is_ollama_overloaded(e):
        print("Ollama is overloaded, try again later")
    else:
        print(f"Other error: {e}")
```

### Waiting for capacity

```python
from koderz.utils.retry import wait_for_ollama_capacity

if wait_for_ollama_capacity(host="http://llm-server:11434", timeout=60.0):
    print("Ollama is ready")
else:
    print("Ollama still not ready after 60 seconds")
```

## Implementation Details

### Architecture

```
CLI Command (koderz benchmark/run/speed-test)
    ↓ --timeout, --max-retries
ModelFactory(timeout, max_retries)
    ↓
OllamaClient(timeout, max_retries)
    ↓
generate() with @retry_with_backoff decorator
    ↓ on timeout/503/429
Exponential backoff retry logic
    ↓ success or max retries
Return result or raise MaxRetriesExceeded
```

### Files Modified

- `koderz/utils/retry.py` - Core retry logic
- `koderz/models/local.py` - OllamaClient with retry support
- `koderz/models/factory.py` - Pass timeout/retries to OllamaClient
- `koderz/benchmarks/speed_test.py` - Speed benchmark with retry
- `koderz/cli.py` - CLI options for timeout and max_retries
- `tests/test_retry.py` - Comprehensive test suite

### Testing

Run retry tests:
```bash
pytest tests/test_retry.py -v
```

Test specific scenario:
```bash
pytest tests/test_retry.py::TestRetryWithBackoff::test_exponential_backoff_timing -v
```

## Troubleshooting

### Still Getting Timeouts After Retries

**Possible causes:**
1. Model is too large for available VRAM
2. Ollama is genuinely stuck (check logs: `journalctl -u ollama -f`)
3. Timeout too short for model size
4. System resources exhausted (check `nvidia-smi`, `htop`)

**Solutions:**
- Increase `--timeout` to 600 or 900 seconds
- Reduce concurrent load (don't run multiple benchmarks)
- Check Ollama logs for errors
- Restart Ollama: `sudo systemctl restart ollama`

### Retries Taking Too Long

If exponential backoff makes benchmarks too slow:

```bash
# Faster retries with shorter delays
# (Warning: may overload Ollama more)
```

Currently, backoff parameters are hardcoded (2s initial, 2× factor, 60s max). Future enhancement could make these configurable.

### Queue Always Full (503 errors)

If you consistently hit 503 errors even with retries:

```bash
# Increase Ollama queue size
Environment="OLLAMA_MAX_QUEUE=512"  # or higher

# Reduce concurrent requests
Environment="OLLAMA_NUM_PARALLEL=2"  # fewer parallel requests per model
```

## Future Enhancements

Potential improvements:
- [ ] Configurable backoff parameters (initial delay, factor, max delay)
- [ ] Request queueing at application level (prevent hammering Ollama)
- [ ] Circuit breaker pattern (stop retrying if Ollama is persistently down)
- [ ] Automatic timeout adjustment based on model size
- [ ] Retry statistics in benchmark reports
- [ ] Parallel request limiting (max N concurrent to Ollama)

## Related Documentation

- [Ollama Configuration Guide](OLLAMA_CONFIGURATION.md) - Optimal Ollama settings
- [Speed Test Guide](SPEED_TEST_QUICK_REF.md) - Model speed benchmarking
- [Benchmark Tracking](BENCHMARK_TRACKING.md) - Run tracking system

## Support

If you encounter issues with retry logic:
1. Check Ollama logs: `journalctl -u ollama -f`
2. Monitor resources: `nvidia-smi`, `htop`
3. Test Ollama directly: `curl http://llm-server:11434/api/tags`
4. File an issue with full error logs and configuration
