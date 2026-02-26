# Fix: DomainClassifier.classify() method

Fix the `classify` method in `agentmon/llm/classifier.py`. Rewrite the entire file.

Put `# agentmon/llm/classifier.py` as the first line in the code block.

## Issues to fix

1. **JSON response not parsed correctly**: `_call_ollama` returns `{"message": {"content": "<json_string>"}}`. You must do `json.loads(response["message"]["content"])` to get the category, confidence, reasoning.

2. **Category mapping broken**: After parsing JSON, map the `"category"` string to DomainCategory enum. Use case-insensitive matching. "suspicious" → DomainCategory.SUSPICIOUS, "likely_malicious" → DomainCategory.LIKELY_MALICIOUS, etc.

3. **Escalation logic wrong**: Only escalate if triage category is "suspicious" or triage confidence < escalation_threshold (default 0.7). "benign" with confidence 0.95 should NOT escalate.

4. **Caching not working**: Before any _call_ollama, check if domain is in self._cache dict. If yes, return cached result. After classify completes, store result in self._cache[domain].

## classify(self, domain: str) -> ClassificationResult

```
Step 1: if domain in self._cache, return self._cache[domain]
Step 2: response = await self._call_ollama(model=config.triage_model, ...)
Step 3: parsed = json.loads(response["message"]["content"])
Step 4: triage_cat_str = parsed["category"]
Step 5: triage_confidence = parsed["confidence"]
Step 6: triage_reasoning = parsed["reasoning"]
Step 7: Map triage_cat_str to DomainCategory enum
Step 8: If triage_cat_str == "suspicious" or triage_confidence < config.escalation_threshold:
          escalation_response = await self._call_ollama(model=config.escalation_model, ...)
          esc_parsed = json.loads(escalation_response["message"]["content"])
          Map esc_parsed category to DomainCategory
          result = ClassificationResult(domain=domain, category=esc_category, confidence=esc_parsed["confidence"], reasoning=esc_parsed["reasoning"], escalated=True, triage_category=triage_cat_str)
        else:
          result = ClassificationResult(domain=domain, category=triage_category, confidence=triage_confidence, reasoning=triage_reasoning, escalated=False, triage_category=None)
Step 9: self._cache[domain] = result
Step 10: return result
```

Keep all other classes unchanged: DomainCategory enum, ClassificationResult dataclass, LLMConfig dataclass, sanitize_domain_for_prompt function.
