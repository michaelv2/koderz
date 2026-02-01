# Koderz TODO List

Tasks and enhancements for future development.

## Immediate (Pre-Launch)

### Testing & Validation
- [ ] Run `setup_and_verify.sh` on fresh system
- [ ] Test with real Ollama + CodeLlama
- [ ] Test with real Anthropic API
- [ ] Test full HumanEval problem end-to-end
- [ ] Verify cortex integration works
- [ ] Test error handling (no Ollama, no API key, etc.)
- [ ] Test on Windows/Mac/Linux

### Documentation
- [ ] Add screenshots to README
- [ ] Create video walkthrough
- [ ] Document common errors + solutions
- [x] Add API key signup instructions
- [ ] Create troubleshooting guide

### Fixes
- [ ] Handle MCP connection errors gracefully
- [ ] Improve MCP performance and resolve persistence issues with asynchronous calls
- [ ] Add retry logic for Ollama timeouts
- [ ] Improve error messages
- [ ] Add progress bars for long operations
- [ ] Validate environment before starting

## Short Term (v0.2)

### Core Features
- [ ] **Context Window**: Pass previous attempts to local model
  - Query cortex for last N iterations
  - Include in prompt
  - Measure impact on success rate

- [ ] **Adaptive Checkpointing**: Trigger based on error patterns
  - Track error rate
  - Checkpoint when stuck
  - Skip when improving

- [ ] **Experiment Resumption**: Resume failed experiments
  - `koderz resume exp_a1b2c3d4`
  - Load state from cortex
  - Continue from last iteration

- [x] **Batch Mode**: Run multiple problems
  - `koderz benchmark --start 0 --end 100`
  - Sequential execution (parallel TBD)
  - Aggregate statistics
  - Comparative mode (zero-shot vs iterative)

### Improvements
- [ ] Better prompt engineering
  - Few-shot examples
  - Chain-of-thought prompting
  - Self-reflection prompts

- [x] Cost optimization (partially complete)
  - [x] Prompt caching (Anthropic) - via spec reuse feature
  - [x] Smaller models for simple problems - three-tier system implemented
  - [ ] Early stopping (high confidence)

- [x] Results export (debug mode implemented)
  - [ ] CSV export
  - [ ] JSON export
  - [ ] Markdown reports

## Medium Term (v0.3)

### Beam Search
- [ ] Parallel solution generation
  - Generate N solutions
  - Score with frontier
  - Pick best

- [ ] Implementation:
  ```python
  koderz run --problem-id "HumanEval/0" --beam-width 5
  ```

### Multi-Agent Swarm
- [ ] Agent roles:
  - **Generator**: Creates solutions
  - **Critic**: Reviews code
  - **Tester**: Writes test cases
  - **Refiner**: Improves solutions

- [ ] Agent communication:
  - Shared cortex
  - Message passing
  - Consensus protocol

### Additional Benchmarks
- [ ] MBPP support
  - Loader
  - Executor
  - CLI integration

- [ ] SWE-bench (GitHub issues)
  - Problem loader
  - Multi-file editing
  - Git integration

### Web UI
- [ ] Dashboard
  - Live experiment monitoring
  - Cost tracking
  - Success metrics

- [ ] Visualization
  - Iteration timeline
  - Cost breakdown
  - Success rate charts

- [ ] Tech stack:
  - FastAPI backend
  - React frontend
  - WebSocket updates

## Long Term (Research)

### Reinforcement Learning
- [ ] Learn optimal policies
  - Checkpoint frequency
  - Model selection
  - Resource allocation

- [ ] Reward function:
  ```python
  reward = success - (cost * cost_weight) - (iterations * time_weight)
  ```

- [ ] Policy network:
  - Input: problem features, current state
  - Output: action (checkpoint/continue/switch_model)

### Meta-Learning
- [ ] Transfer learning
  - Learn from past experiments
  - Problem embeddings
  - Solution patterns

- [ ] Automatic prompt optimization
  - A/B testing prompts
  - Evolutionary algorithms
  - Gradient-free optimization

### Advanced Features
- [ ] Tree search (MCTS)
  - Explore solution space
  - Backpropagation
  - UCB selection

- [ ] Mixture of Experts
  - Route problems to best model
  - Ensemble predictions
  - Confidence estimation

- [ ] Active learning
  - Request human feedback
  - Uncertainty sampling
  - Query strategy

## Infrastructure

### Performance
- [ ] Distributed execution
  - Multiple Ollama servers
  - Load balancing
  - Fault tolerance

- [ ] Caching
  - Solution cache (deduplication)
  - Prompt cache
  - Result cache

### Monitoring
- [ ] Observability
  - OpenTelemetry integration
  - Grafana dashboards
  - Prometheus metrics

- [ ] Alerting
  - Cost thresholds
  - Error rate spikes
  - Performance degradation

### Security
- [ ] Sandboxing
  - Docker containers
  - Resource limits (CPU, memory, network)
  - Security scanning

- [ ] Audit logging
  - All API calls
  - Costs incurred
  - Solutions generated

## Research Questions

### Experiments to Run
- [ ] **Cost vs Quality**: How does checkpoint frequency affect success/cost?
- [ ] **Model Comparison**: Which local models work best?
- [ ] **Prompt Engineering**: What prompts maximize success rate?
- [ ] **Scaling Laws**: How does success scale with model size/iterations?
- [ ] **Transfer Learning**: Do experiments on easy problems help hard ones?

### Papers to Write
- [ ] "Hybrid Swarm Architecture for Code Generation"
- [ ] "Cost-Effective Code Synthesis via Frontier Supervision"
- [ ] "Meta-Learning for Adaptive Model Orchestration"

## Community

### Open Source
- [ ] GitHub repository
  - CI/CD pipeline
  - Issue templates
  - Contributing guide

- [ ] Package distribution
  - PyPI release
  - Docker images
  - Homebrew formula

### Ecosystem
- [ ] Plugin system
  - Custom benchmarks
  - Custom models
  - Custom checkpointing

- [ ] Integrations
  - VSCode extension
  - GitHub Actions
  - Discord bot

## Documentation

### Tutorials
- [ ] Beginner tutorial (first experiment)
- [ ] Advanced tutorial (custom models)
- [ ] Video series
- [ ] Blog posts

### API Reference
- [ ] Sphinx docs
- [ ] Type stubs
- [ ] Example gallery

### Research
- [ ] Benchmark results
- [ ] Ablation studies
- [ ] Case studies

## Testing

### Coverage
- [ ] Unit tests (80% coverage)
- [ ] Integration tests
- [ ] End-to-end tests
- [ ] Performance benchmarks

### CI/CD
- [ ] GitHub Actions
  - Lint (black, flake8, mypy)
  - Test (pytest)
  - Build (poetry)

- [ ] Pre-commit hooks
  - Format code
  - Run tests
  - Check types

## Bugs & Issues

### Known Issues
- [ ] MCP recall returns raw text (need better parsing)
- [ ] No context passed to local model
- [ ] Checkpoint guidance not fully integrated
- [ ] No retry on transient failures

### Edge Cases
- [ ] Empty HumanEval dataset
- [ ] Cortex server crash mid-experiment
- [ ] Ollama model not found
- [ ] API rate limiting
- [ ] Disk full

## Optimizations

### Code Quality
- [ ] Type hints everywhere
- [ ] Docstrings for all functions
- [ ] Better error messages
- [ ] Logging levels

### Performance
- [ ] Profile bottlenecks
- [ ] Optimize MCP calls
- [ ] Reduce memory usage
- [ ] Faster test execution

### UX
- [ ] Better progress indicators
- [ ] Colored output
- [ ] Interactive mode
- [ ] Configuration wizard

## Version Roadmap

### v0.1 (MVP) ✅
- Basic workflow
- HumanEval support
- Cost analysis
- CLI interface
- Three-tier model system (local/small frontier/full frontier)
- Model factory and registry
- OpenAI API integration (GPT-4o-mini)
- Code extraction utilities
- Debug mode with output saving
- Spec reuse feature for cost optimization

### v0.2 (Context & Polish)
- Context window
- Experiment resumption
- Better prompts
- More tests

### v0.3 (Advanced Features)
- Beam search
- Multi-agent swarm
- MBPP support
- Web UI

### v0.4 (Research Features)
- RL policies
- Meta-learning
- Tree search
- Distributed execution

### v1.0 (Production Ready)
- Full test coverage
- Comprehensive docs
- Performance optimized
- Security hardened

## Ideas (Brainstorm)

- [ ] Genetic algorithms for prompt evolution
- [ ] Few-shot learning from successful experiments
- [ ] Solution explanation generation
- [ ] Automated test case generation
- [ ] Multi-language support (not just Python)
- [ ] Code review as a service
- [ ] Competitive programming mode
- [ ] Educational mode (hints, not solutions)
- [ ] Pair programming with AI
- [ ] Code golf optimizer

---

**Priority Legend**:
- 🔴 Critical (blocking)
- 🟡 High (important)
- 🟢 Medium (nice to have)
- ⚪ Low (future)

**Status**:
- ✅ Done
- 🚧 In Progress
- ⏸️ Blocked
- ❌ Won't Do
