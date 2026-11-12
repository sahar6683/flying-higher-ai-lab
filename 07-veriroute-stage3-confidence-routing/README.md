# VeriRoute AI — Stage 3: Confidence-Gated Routing

[![Stage](https://img.shields.io/badge/Stage-3%20Confidence%20Routing-7C3AED)]() [![Workflow](https://img.shields.io/badge/n8n-sanitized%20export-FF6D5A?logo=n8n)](./workflows/veriroute_stage3_n8n.json) [![Evaluation](https://img.shields.io/badge/holdout-150%20queries-147D64)](./datasets_and_eval/stage3_holdout_150_audit.csv)

> **A retrieval result is not permission to answer.** Stage 3 applies explicit confidence gates, independent verification and human escalation so weak, stale or malformed evidence does not silently become a customer-facing reply.

## Architecture

```mermaid
flowchart LR
  A[Customer query] --> B[Stage 1 · Qdrant dense + BM25 hybrid RRF]
  B --> C[Stage 2 · Jina cross-encoder rerank]
  C --> D[Blend + finite-score validation]
  D -->|score ≥ 0.45| E[Tier 1 draft · temp 0.1]
  E --> F[Verifier · temp 0.0 · temporal audit]
  F -->|strict JSON true| G[Verified response · customer send]
  F -->|error / reject| H[Tier 2 hold · one-way downgrade]
  D -->|0.22 ≤ score < 0.45| I[Tier 2 · top-3 copilot brief]
  D -->|0 ≤ score < 0.22| J[Tier 3 · no-LLM escalation]
  D -->|invalid / missing| K[ROUTING_ERROR_FALLBACK]
  G --> L[Unified telemetry + audit persistence]
  H --> L; I --> L; J --> L; K --> L
```

![Verifier fail-closed circuit breaker](assets/verifier_circuit_breaker_pink_hero.png)

## Executive summary

Stage 1 combines semantic dense search and exact-token BM25 using Qdrant hybrid Reciprocal Rank Fusion. Stage 2 reranks candidates with Jina. Stage 3 uses half-open score intervals, drafts only for high-confidence candidates, and requires an independent, strict-JSON verifier before any customer send. A verifier failure is held for Tier 2 review; low-confidence queries go directly to human handling; invalid routing state has a distinct loud fallback. Every terminal outcome is intended to be auditable with route, queue, SLA and estimated cost.

The included source export and audit are artifacts from a simulated workflow. This package does **not** claim live API execution or independent reproduction of every headline metric. See [evidence boundaries](#evidence-and-reproducibility) before treating any result as a production guarantee.

## SLA and operating model

| Route | Gate / event | Action and queue | Target SLA | Illustrative unit cost |
|---|---|---|---:|---:|
| Tier 1 | `score ≥ 0.45`, then verifier must pass | Auto-dispatch customer response | `< 5 sec` | `$0.003` |
| Tier 2 | `0.22 ≤ score < 0.45`, or Tier 1 verifier fails | Agent Copilot review hold | `< 15 min` | `$1.50` |
| Tier 3 | `0 ≤ score < 0.22` | Senior specialist escalation; no LLM draft | `< 4 hours` target roadmap (source log says `< 2 hours`) | `$6.00` |
| Fallback | null/NaN/invalid score, candidate, or routing state | `ROUTING_ERROR_FALLBACK` dead-letter / engineering-visible senior queue | `< 30 min` in source code | `$6.00` estimate |

Costs and SLAs are source-note estimates/configuration targets, not measured guarantees. The source article and execution log differ on Tier 3 SLA: article says `<4 hours`, log says `<2 hours`; reconcile one published contract before deployment.

## Benchmark results

### Source-reported holdout headlines (article 11)

| Cohort / measure | Source-reported result |
|---|---:|
| 60 unseen semantic-intent tickets · Top-1 accuracy | `80.0%` |
| Same cohort · Tier 1 precision (article section) | `92.1%` |
| 60 harder lexical tickets · baseline → holdout Top-1 | `97.6% → 56.7%` (`−40.9 pp`) |
| Tier 1 auto-send coverage · baseline → holdout | `81.6% → 26.7%` |
| Tier 1 precision (article executive result) | `88.9%` |
| Observed execution log route totals | `65 Tier 1 / 71 Tier 2 / 14 Tier 3` |

The article itself gives two different precision figures (92.1% for the semantic cohort; 88.9% as overall Tier 1 precision). The postmortem separately calls out an illustrative 250-ticket route split of 160 Tier 1 / 86 Tier 2 / 4 Tier 3, which does not match the article’s 81.6% Tier 1 coverage; cohort/protocol definitions need reconciliation. The 150-row workflow CSV has only hashed policy IDs and does not include a canonical hash→policy mapping, so the headline correctness/precision values cannot be independently recomputed from the supplied execution log. `scripts/veriroute_quant_audit.py` recomputes record counts, cohorts and score summaries and prints a conservative title-match proxy; it labels what is and is not reproducible.

### Benchmarks visualized

![Semantic generalization](assets/chart1_semantic_generalization.png)
![Sibling lexical drop](assets/chart2_sibling_lexical_drop.png)
![Confidence gating](assets/chart3_confidence_gating.png)

The charts reproduce article-reported aggregates, not metrics calculated from raw query-level canonical relevance labels.

## Fault-injection design

`datasets_and_eval/fault_injection_payloads.json` contains five representative payloads: `0.4499` boundary, NaN/null fallback, substring spoof, truncated JSON, and an expired-2024 policy with verifier timeout. Expected outcomes are fail-closed: Tier 2 hold, Tier 3, or explicit fallback; never optimistic parsing or send. The article reports an 11-scenario family with zero false auto-sends, but the supplied row-level CSV is the 150-ticket audit—not a complete isolated fault-run log. Treat that pass rate as article-reported, not independently rerun here.

## Stage 4 roadmap

1. **Close artifact gaps:** correct and test request-body JSON mode; reconcile documented score formula with actual code; rejoin parallel branch results by `ticket_id`; validate all required candidate fields.
2. **Policy lifecycle:** require structured approval state and `effective_from` / `effective_to`; reject absent, draft, superseded or expired authority.
3. **Canonical evaluation IDs:** supply policy hash mapping and rerun the 250 baseline + 150 unseen holdout with per-cohort precision/coverage, confidence intervals, abstention, false Tier 1 rate and failure-mode recall.
4. **Operational hardening:** idempotent writes, bounded retries/timeouts, rate limits, redacted telemetry, alerting, and measured queue/cost SLAs.
5. **Shadow release:** replay isolated fixtures with all customer-send side effects disabled; compare routes and require approval before staged production rollout.

## Evidence and reproducibility

- **Baseline inputs:** `stage2_baseline_250_eval.csv` is the labeled 250-ticket query set copied from the prior Project 06 artifacts; it is not a retrieval result log.
- **Holdout:** `stage3_holdout_150_audit.csv` joins the 150-row `Import_150` workbook and `Audit_Metadata` to the uploaded `output Stage3_VeriRoute_Audit.csv` by `ticket_id`.
- **Workbook:** original supplied 150-ticket benchmark is retained alongside the joined CSV.
- **Historical claims:** article 11 and the technical postmortem describe intended/claimed behavior. The postmortem explicitly warns that the workflow export had implementation defects and that it did not independently execute the workflow.
- **Inspected export issues:** source calculations used raw Stage 1 score instead of the documented normalized RRF associated with the Jina winner; the export had implicit paired-item lookups; the Tier 2 node contained an expression/body-mode concern. This sanitized copy only scrubs identities/secrets and aligns generation temps; it does not resolve those architectural/runtime questions. Release remains blocked pending corrective implementation and isolated tests.
- **Secret safety:** all actual API tokens, Qdrant endpoint, Google WebApp URL, n8n resource IDs and source node UUIDs have been removed/replaced. The placeholders are not working credentials.

## Run locally

```bash
python scripts/veriroute_quant_audit.py
python scripts/generate_charts.py
```

Dependencies: Python 3.10+, pandas, matplotlib. No network calls are made.

## Repository map

- `workflows/` — sanitized, inactive n8n export
- `prompts/` — source prompts with role/temperature headers
- `guardrails_and_parsers/` — fail-closed parser, boundary rules, and calibrated Hybrid RRF summary Code-node example (`hybrid_rrf_summary.js`)
- `datasets_and_eval/` — labeled input, joined audit, workbook and fault fixtures
- `scripts/` — descriptive audit and article-chart regeneration
- `assets/` — source workflow/circuit images and three figures

## License and safety

The upstream portfolio indicates MIT; no license file was provided in this Stage 3 upload, so this package makes no standalone license assertion. Use only in an isolated test environment until the Stage 4 release gates above are met.
