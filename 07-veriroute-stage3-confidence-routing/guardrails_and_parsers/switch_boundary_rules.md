# Switch boundaries and scoring notes

Use finite numeric values after rejecting null, empty strings, NaN, and Infinity. Compare the unrounded numeric value; do not use string matching for scores.

| Condition | Route | Interval |
|---|---|---|
| `Number.isFinite(score) && score >= 0.45` | Tier 1 candidate (verifier mandatory) | `[0.45, 1.00]` |
| `score >= 0.22 && score < 0.45` | Tier 2 Copilot / human review | `[0.22, 0.45)` |
| `score >= 0 && score < 0.22` | Tier 3 senior human escalation; no LLM | `[0.00, 0.22)` |
| null / NaN / ±Infinity / negative / missing candidates / unknown state | loud dead-letter / senior queue | `ROUTING_ERROR_FALLBACK` |

Exact edges: `0.4500 → Tier 1`, `0.4499 → Tier 2`, `0.2200 → Tier 2`, `0.2199 → Tier 3`. Always check finite validity before comparisons.

## Score formula caveat
The postmortem documents `0.80 × Jina relevance + 0.20 × min(RRF / 0.50, 1.0)`, using the RRF score attached to the Jina-selected winner. The uploaded n8n summary node as provided uses the Stage-1 top-ranked candidate's raw score and does not show this normalization. Its formula must therefore be reconciled and isolated-tested before production use; do not treat the export as validated calibration.
