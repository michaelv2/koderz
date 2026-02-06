Research Design Critique

  1. Baseline Methodology is Synthetic, Not Empirical

  The "frontier-only" baseline cost used in savings calculations (_complete_experiment) is a synthetic estimate — it
   multiplies estimated token counts by frontier pricing. You never actually run the frontier model on the same
  problems to get ground-truth success rates and costs. This means:

  - You can't claim "X% cost savings" without knowing whether the frontier model would have succeeded in fewer
  iterations (or at all).
  - The baseline assumes the frontier model would need the same number of iterations, which is almost certainly
  false.
  - A valid comparison requires running the frontier model under identical conditions (same prompts, same iteration
  count cap, same test harness).

  Recommendation: Run actual frontier-only experiments as a control group on a representative subset (e.g., 30-50
  problems). Compare success rate, iteration count, and real cost.

  5. Checkpoint Guidance Creates a Hidden Frontier Dependency

  Checkpoints use a full frontier model (e.g., Claude Sonnet) to review iterations and provide guidance. This
  guidance includes detailed algorithmic suggestions ("try using a dictionary approach," "handle the edge case
  where..."). The iteration model then follows these suggestions.

  This means the system isn't testing whether cheaper models can solve problems independently — it's testing whether
   they can follow instructions from a frontier model. That's a valid research question, but it's different from the
   stated one.

  Recommendation: Clearly distinguish these research questions. Run conditions with checkpoints disabled to measure
  the iteration model's independent capability. Report results separately.

  7. Cost Model Assumptions

  - Local models are priced at $0.00, but they have real costs (electricity, GPU amortization, opportunity cost of
  GPU time). For research claims about "cost savings," acknowledging this matters.
  - The cost comparison assumes a specific usage pattern (sequential single-user). In practice, a frontier API call
  that returns in 2 seconds may be cheaper than a local model that takes 60 seconds when you factor in developer
  time.

  Recommendation: Report wall-clock time alongside cost. Consider adding a "time-adjusted cost" metric.

  9. Success Metric is Binary

  A solution either passes all tests or fails. There's no partial credit for:

  - Solutions that pass some tests but not all
  - Solutions that are syntactically correct but logically wrong
  - Solutions that are close but have off-by-one errors

  This makes it hard to measure whether iterations are actually improving the solution or just randomly sampling.

  Recommendation: Track pass@k metrics (standard in code generation research). Log the number of test cases passed
  per iteration to measure convergence. Consider using pass@1, pass@5, pass@10 as standard metrics.

  10. No Ablation Study Design

  The system has many interacting components (spec generation, iteration prompts, checkpoint guidance, progressive
  disclosure, temperature settings, context window size). Without systematic ablation, you can't determine which
  components contribute to success.

  Recommendation: Design ablation experiments that toggle components individually:
  - With/without spec
  - With/without checkpoints
  - With/without previous error in prompt
  - Different checkpoint intervals
  - Different temperature values