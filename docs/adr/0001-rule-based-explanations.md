## Title

0001: Rule-based alert explanations

## Status

Accepted

## Context

Alert explanations must be instant and free, work offline in CI, and be
deterministic so that the same alert always produces the same explanation and
tests do not depend on variable LLM output.

## Decision

`generate_explanation()` in `services/explainer.py` builds explanations from
fixed rules based on the alert's severity, metric value, and threshold instead
of calling an external LLM API.

## Consequences

- Explanations are instant and free.
- Explanation generation works offline in CI.
- The same alert produces the same explanation, so tests do not depend on
  variable LLM output.
- Explanations are more generic and cannot handle alert patterns that the rules
  do not anticipate.