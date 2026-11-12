#!/usr/bin/env python3
"""Zero-config descriptive audit of included VeriRoute CSVs (pandas required)."""
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/"datasets_and_eval"
base=pd.read_csv(DATA/"stage2_baseline_250_eval.csv"); hold=pd.read_csv(DATA/"stage3_holdout_150_audit.csv")
assert len(base)==250, f"Expected 250 baseline queries, got {len(base)}"
assert len(hold)==150, f"Expected 150 holdout audit rows, got {len(hold)}"
assert hold["ticket_id"].is_unique and hold["blended_score"].notna().all()
print("VERIROUTE STAGE 3 — REPRODUCIBLE ARTIFACT AUDIT")
print(f"Baseline labeled queries: {len(base)} | by query_type: {base['query_type'].value_counts().sort_index().to_dict()}")
print(f"Holdout execution rows:   {len(hold)} | by query_type: {hold['query_type'].value_counts().sort_index().to_dict()}")
print("\nObserved route counts (execution CSV)")
print(hold.groupby("routing_tier",dropna=False).agg(n=("ticket_id","size"),score_min=("blended_score","min"),score_mean=("blended_score","mean"),score_max=("blended_score","max")).round(4).to_string())
print("\nHoldout cohorts (labeled workbook + execution log)")
print(hold.groupby("cohort",dropna=False).agg(n=("ticket_id","size"),score_min=("blended_score","min"),score_mean=("blended_score","mean"),score_max=("blended_score","max")).round(4).to_string())
# Match title proxy: compare normalized final segment of expected document ID to reranked title.
def norm(s): return "".join(ch.lower() for ch in str(s) if ch.isalnum())
def expected_title(doc): return str(doc).rsplit("-",1)[-1]
expected=hold["primary_expected_doc_id"].map(lambda x:norm(expected_title(x)))
observed=hold["s2_top_1_title"].map(norm)
valid=hold["s2_top_1_title"].notna() & hold["primary_expected_doc_id"].notna()
exact=(expected==observed)&valid
print("\nConservative exact normalized title match proxy (not canonical-ID accuracy)")
print(f"Matched title / valid rows: {int(exact.sum())}/{int(valid.sum())} = {exact.sum()/valid.sum():.4%}")
print("This is title equality only; source export IDs are opaque hashes and cannot be directly equated to workbook policy IDs.")
print("\nSource-reported headline claims (article 11; not recomputed from available row identifiers)")
print("semantic holdout Top-1 80.0%; Tier 1 precision 92.1% (elsewhere article says overall Tier 1 precision 88.9%); lexical baseline 97.6% → holdout 56.7%; Tier 1 coverage 81.6% → 26.7%.")
print("Discrepancy note: headline values are source-reported; this CSV supports route counts and descriptive scores, but lacks a canonical hash→policy mapping for direct verification. See README.")
