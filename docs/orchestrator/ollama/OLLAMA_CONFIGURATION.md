# Ollama Configuration Guide

Optimal Ollama configuration for your hardware setup: 2×RTX 3090 GPUs (48GB VRAM) + 96GB DDR5 RAM.

## Quick Start

For your specific hardware running:
- Open WebUI (2 users)
- Koderz benchmarks
- DNS classification (pi-hole)

```bash
sudo systemctl edit ollama.service
```

Add:
```ini
[Service]
Environment="OLLAMA_NUM_PARALLEL=4"
Environment="OLLAMA_MAX_LOADED_MODELS=5"
Environment="OLLAMA_MAX_QUEUE=256"
Environment="OLLAMA_KEEP_ALIVE=30m"
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_GPU_OVERHEAD=2147483648"
```

Apply:
```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

## Environment Variable Reference

### OLLAMA_NUM_PARALLEL
**Default:** Auto (1-4 based on memory)
**Recommended:** `4`

Max parallel requests each model processes simultaneously. With 2 GPUs and mixed workload, 4 allows batch processing for koderz while keeping interactive users responsive.

### OLLAMA_MAX_LOADED_MODELS
**Default:** 3 × GPUs (6 for your setup)
**Recommended:** `5`

Max models loaded in VRAM concurrently. Conservative value prevents VRAM thrashing with variable model sizes (DNS classifier: 3B, chat: 7-13B, koderz tests: up to 32B).

### OLLAMA_MAX_QUEUE
**Default:** `512`
**Recommended:** `256`

Max queued requests before rejecting with 503. Lower value provides faster fail-fast behavior. Increase to 512-1024 for heavy benchmark loads.

### OLLAMA_KEEP_ALIVE
**Default:** `5m`
**Recommended:** `30m`

How long to keep models in memory when idle. 30 minutes keeps DNS classifier and common chat models loaded, while allowing koderz benchmark models to unload after testing.

### OLLAMA_FLASH_ATTENTION
**Default:** `0` (disabled)
**Recommended:** `1` (enabled)

Enable Flash Attention 2.0 for reduced VRAM usage (30-40% less KV cache). Critical for running larger contexts efficiently.

### OLLAMA_GPU_OVERHEAD
**Default:** `0`
**Recommended:** `2147483648` (2GB per GPU)

Reserve VRAM per GPU for CUDA operations. Prevents OOM crashes during peak load.

### Optional: OLLAMA_SCHED_SPREAD
**Default:** `0` (disabled)
**Recommended:** Leave disabled

When enabled, spreads model layers across both GPUs. Your NVLink 3.0 setup could benefit, but default packing is usually optimal.

## Hardware-Specific Notes

### RTX 3090 Advantages
- 24GB VRAM per card (48GB total via NVLink)
- NVLink 3.0 @ 112.5 GB/s bidirectional
- Can run 70B models (Q4) across both GPUs
- Can run multiple 7-13B models simultaneously

### Typical Model Footprints
```
Model Size    VRAM (Q4)    VRAM (Q8)    Fits On
---------------------------------------------------------
3B            ~2-3GB       ~3-4GB       Single 3090
7B            ~4-5GB       ~7-8GB       Single 3090
13B           ~8-9GB       ~13-14GB     Single 3090
32B           ~19-20GB     ~32-34GB     Single 3090
70B           ~38-40GB     ~70-75GB     Both 3090s (NVLink)
```

### Workload Capacity Estimate

With your configuration:
- **Open WebUI (2 users):** 1-2 models (7-13B each) = ~10-20GB VRAM
- **DNS classifier:** 1 small model (3B) = ~3GB VRAM
- **Koderz benchmark:** 1 active test model (7-32B) = ~5-20GB VRAM
- **Total concurrent:** ~18-43GB VRAM used

This leaves 5-30GB headroom, which is healthy.

## Monitoring

### Check Loaded Models
```bash
curl http://llm-server:11434/api/ps
```

### Watch VRAM Usage
```bash
watch -n 1 nvidia-smi
```

### Monitor Ollama Logs
```bash
journalctl -u ollama -f
```

## Tuning for Different Scenarios

### Heavy Koderz Benchmarking
When running large benchmark batches:
```ini
Environment="OLLAMA_MAX_QUEUE=512"        # Higher queue
Environment="OLLAMA_MAX_LOADED_MODELS=4"  # Fewer models (less thrashing)
Environment="OLLAMA_KEEP_ALIVE=15m"       # Shorter retention
```

### Interactive-Only (No Benchmarks)
Optimize for Open WebUI responsiveness:
```ini
Environment="OLLAMA_NUM_PARALLEL=6"       # More parallel
Environment="OLLAMA_MAX_LOADED_MODELS=8"  # More models
Environment="OLLAMA_KEEP_ALIVE=60m"       # Keep longer
```

### Mixed Load (Current Setup)
Balanced configuration (recommended above).

## Troubleshooting

### Models Timing Out
- Increase `OLLAMA_KEEP_ALIVE` so models don't unload
- Reduce `OLLAMA_MAX_LOADED_MODELS` to prevent unloading active models
- Check if VRAM is full: `nvidia-smi`

### 503 Server Overloaded Errors
- Increase `OLLAMA_MAX_QUEUE` to 512 or 1024
- Reduce concurrent load (pause some benchmarks)
- Reduce `OLLAMA_NUM_PARALLEL` to limit concurrent processing

### VRAM Exhaustion (OOM)
- Reduce `OLLAMA_MAX_LOADED_MODELS`
- Use smaller quantization (Q4 instead of Q8)
- Enable `OLLAMA_FLASH_ATTENTION=1`
- Increase `OLLAMA_GPU_OVERHEAD` to 4GB
- Check what's loaded: `curl http://llm-server:11434/api/ps`

### Slow First Request (Model Loading)
- Increase `OLLAMA_KEEP_ALIVE` to keep models resident longer
- Use koderz `--warmup` flag for speed tests
- Pre-load models before benchmarks

## Platform-Specific Configuration

### Linux (systemd) - Your Setup
```bash
sudo systemctl edit ollama.service
# Add [Service] and Environment lines
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### macOS
```bash
launchctl setenv OLLAMA_NUM_PARALLEL 4
launchctl setenv OLLAMA_MAX_LOADED_MODELS 5
# Restart Ollama app
```

### Docker
```bash
docker run -d \
  -e OLLAMA_NUM_PARALLEL=4 \
  -e OLLAMA_MAX_LOADED_MODELS=5 \
  -e OLLAMA_MAX_QUEUE=256 \
  -e OLLAMA_KEEP_ALIVE=30m \
  -e OLLAMA_FLASH_ATTENTION=1 \
  -e OLLAMA_GPU_OVERHEAD=2147483648 \
  -p 11434:11434 \
  --gpus all \
  ollama/ollama
```

## Related Documentation

- [Retry and Queue Management](RETRY_AND_QUEUE_MANAGEMENT.md) - Koderz retry logic
- [Ollama Official Docs](https://docs.ollama.com/faq) - Full environment variable reference
- [Speed Test Guide](SPEED_TEST_QUICK_REF.md) - Benchmarking model speed

## Sources

- [Ollama FAQ](https://docs.ollama.com/faq)
- [How Ollama Handles Parallel Requests](https://www.glukhov.org/post/2025/05/how-ollama-handles-parallel-requests/)
- [Ollama VRAM Requirements Guide](https://localllm.in/blog/ollama-vram-requirements-for-local-llms)
- [Memory Management and GPU Allocation](https://deepwiki.com/ollama/ollama/5.4-memory-management-and-gpu-allocation)
