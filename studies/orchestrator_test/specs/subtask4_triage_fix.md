# Fix: triage_category field in DomainClassifier.classify

In `agentmon/llm/classifier.py`, the `classify` method has a bug in the escalation flow.

When escalation happens (triage result is "suspicious"), the `triage_category` field must be set to the TRIAGE result's category string (i.e. "suspicious"), NOT the escalation result's category.

The flow should be:
1. Call triage model → get triage_result (category="suspicious", confidence=0.6)
2. Since category is "suspicious", call escalation model → get escalation_result (category="likely_malicious", confidence=0.85)
3. Build ClassificationResult using:
   - `category` = from escalation_result (LIKELY_MALICIOUS)
   - `confidence` = from escalation_result (0.85)
   - `triage_category` = from TRIAGE result ("suspicious") — NOT the escalation category
   - `escalated` = True

The bug is that `triage_category` is being set to the escalation result's category instead of the triage result's category. Save the triage category string before doing the escalation call, then use it when building the final ClassificationResult.

Rewrite the entire file. Put `# agentmon/llm/classifier.py` as the first line in the code block.
