# Project 06 — Hybrid RAG Retrieval Benchmark

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Evaluation set](https://img.shields.io/badge/evaluation-250%20tickets-147D64)](#benchmark-design) [![Corpus](https://img.shields.io/badge/corpus-100%20policies-315B8A)](#benchmark-design) [![Status](https://img.shields.io/badge/status-research%20benchmark-8A5CF6)]()

> **Question:** When an enterprise RAG system scales its policy corpus tenfold, can retrieval reliably distinguish a truly missing rule from one that exists but was never retrieved?

This project isolates and benchmarks retrieval for a customer-operations policy corpus. It evolves from a BM25 baseline to dense retrieval, hybrid score fusion, and two-stage cross-encoder reranking. On a 250-ticket evaluation set, the strongest reported MiniLM residual blend attained **81.2% Recall@1, 94.4% Recall@5, 94.8% Recall@10, and 0.8662 MRR@10**. A separate BGE-Reranker-v2-m3 run reports **83.2% Recall@1 and 0.8782 MRR@10** on a stage-one pool whose Recall@10 is reported as 93.2%; the run is kept distinct because its candidate/evaluation protocol differs from the 94.8%-ceiling residual experiment.

**Reproducibility note:** this package includes all 713 full-text chunks in `data/chunks.csv`, the 250 labeled tickets, and `src/phase1_ingest.py`. The BM25 baseline can run from the included CSVs without the raw PDFs. The PDFs, dense embedding/checkpoint matrices, and reranker weights are not included, so historical dense/hybrid/reranking score tables are reported results rather than fully regenerated outputs. See [what is and is not included](#reproduction-and-artifact-boundaries).

## At a glance

| Benchmark element | Setup |
|---|---|
| Corpus inventory | 100 policy PDFs; seven category folders (six groups of 15, one group of 10) |
| Chunking | Section-aware extraction with document/category/title/section breadcrumbs; 713 chunks in the source run |
| Evaluation set | 250 labeled tickets; 125 `semantic_intent` + 125 `lexical_keyword` |
| Dense models | BAAI BGE-base-en-v1.5, Google EmbeddingGemma 2, OpenAI `text-embedding-3-small`; 768 dimensions |
| Stage 1 | BM25, cosine dense retrieval, Reciprocal Rank Fusion (RRF), or min-max weighted linear fusion |
| Stage 2 | Cross-encoder reranking; `cross-encoder/ms-marco-MiniLM-L-6-v2` (22M) and `BAAI/bge-reranker-v2-m3` (568M) |
| Main outcome | Retrieval quality is a pipeline property: a reranker cannot recover a target excluded from its candidate pool |

## Contents

- [Benchmark design](#benchmark-design)
- [Methodology and fusion math](#methodology-and-fusion-math)
- [Results](#results)
- [Failure modes and interpretation](#failure-modes-and-interpretation)
- [Reproduction and artifact boundaries](#reproduction-and-artifact-boundaries)
- [Repository map](#repository-map)

## Benchmark design

### Corpus and ingestion

The manifest describes **100 PDFs** across seven categories: returns/refunds, shipping/delivery, ordering/payment/billing, warranty/repairs, account security/privacy, customer care/escalations, and B2B/corporate trade. It records a filename and lexical anchors / semantic focus for each policy. The article describes removal of recurring boilerplate followed by section-boundary chunking and a standardized breadcrumb at the start of each chunk, for example `Doc: <code> | Category: <category> | Title: <title> | Section: <section>`.

The Colab outputs report **713 chunks** over 100 documents (mean 7.13/document; chunk character-count median 208, mean 293.8), with a validation report showing 100/100 source PDFs extracted and no extraction failures. One intermediate Phase 1 cleanup cell filters 299 heading-only micro-chunks, leaving 414 substantive chunks. Later dense/hybrid score arrays and benchmark runs are described as 250 queries × 713 chunks. The source run therefore includes multiple corpus representations; compare results only within the stated run/protocol. The included 713-row `data/chunks.csv` is the full-text source for the new reproducible BM25 baseline.

> **Why the title breadcrumb matters for retrieval:** Section chunking can create “orphan” chunks, so ingestion carries the parent policy identity into every chunk. The included `phase1_ingest.py` resolves a document title from PDF metadata, falling back to the earliest plausible heading when metadata is blank/unhelpful; it detects the policy code from the filename first (then document text). It prepends `[Doc: {doc_code or source_file} | Category: {category} | Title: {title}]` to each chunk, followed by the section body. The packaged `chunks.csv` confirms this directly: its `title` column is also present inside each chunk’s `text`.
>
> This breadcrumb gives lexical retrieval and neural retrievers/rerankers an explicit policy name/code, category, and parent identity alongside the section text—helpful when a customer uses a policy name, code, or topic term and when neural models need chunk context. The article describes it as an identity tag so a chunk retains its parent context. **Important nuance:** the article’s standalone BM25 figures do not show a measured gain from adding the breadcrumb: context-enriched chunks scored 55.6% Recall@1 versus 58.4% for raw/cleaned full PDFs, and the article notes shared category words can dilute lexical specificity. There is no isolated title-only ablation here, so treat title context as a corpus/retrieval design rationale, not a separately quantified accuracy lift.

### Evaluation set

The provided `data/expanded_tickets` files contain 250 ticket records, the primary expected policy and chunk labels, optional secondary policy labels, query type, category, customer wording, and retrieval rationale. Counts are balanced by query style (125 each) and distributed across categories as supplied in the source workbook. Ground truth is primarily evaluated at the **policy-document** level, after chunk-to-document mapping and deduplication. The benchmark asks whether the expected policy appears in the first K unique documents, not whether the exact expected chunk is at rank K.

### Metrics

For query set size \(N\), one primary relevant document per query, and the rank \(r_i\) of the expected document:

\[
\mathrm{Recall@K}=\frac{1}{N}\sum_{i=1}^{N}\mathbf{1}[r_i\le K],\qquad
\mathrm{MRR@K}=\frac{1}{N}\sum_{i=1}^{N}\frac{\mathbf{1}[r_i\le K]}{r_i}.
\]

A miss within K contributes zero reciprocal rank. The notebook describes chunk predictions being deduplicated into canonical policy IDs before measurement.

## Methodology and fusion math

### 1. BM25 lexical retrieval

The first baseline compares raw full PDFs, boilerplate-cleaned full PDFs, and context-enriched section chunks. BM25 uses term-frequency saturation and inverse document frequency; words common to most documents have low IDF. This makes lexical matching excellent when a query contains an exact form number or policy code, but fragile under natural-language paraphrase.

### 2. Dense retrieval

BGE-base-en-v1.5, EmbeddingGemma 2, and OpenAI `text-embedding-3-small` are compared at 768 dimensions. Similarity is cosine similarity (implemented as dot product over normalized vectors in the source workflow). The notebook describes Gemma's asymmetric retrieval text format and OpenAI's 768-dimensional Matryoshka truncation. Model and prompt formatting are part of the experimental setup, not interchangeable implementation details.

### 3. Reciprocal Rank Fusion (RRF)

For a candidate document \(d\), two rankers with ranks \(r_j(d)\), weights \(w_j\), and smoothing constant \(c\):

\[
\mathrm{RRF}(d)=\sum_j\frac{w_j}{c+r_j(d)}.
\]

RRF combines **rank positions**, not the raw score scales. The reported baseline is a 50/50 BM25 + dense RRF. The code names RRF weights, but the notebook's tested variants and result table should be consulted rather than assuming rank fusion is equivalent to score-weighted fusion.

### 4. Min-Max Linear Fusion

For each query, normalize each score vector over the candidate/chunk universe:

\[
\hat{s}(x)=\frac{s(x)-\min(s)}{\max(s)-\min(s)+\epsilon},\qquad
S_{hybrid}(d)=\alpha\hat{s}_{dense}(d)+(1-\alpha)\hat{s}_{BM25}(d).
\]

The source benchmark tests 85/15 and 70/30 dense/sparse weights. The 70/30 EmbeddingGemma 2 + BM25 setting delivered a reported Recall@10 of 94.8% while preserving 79.2% Recall@1 and reaching 0.8434 MRR@10. Min-max normalization is query-local and sensitive to outliers / score distributions; it is not probability calibration.

### 5. Two-stage reranking and residual fusion

Stage 1 produces a candidate set; Stage 2 cross-encodes the query against each candidate chunk. A standard overwrite sorts candidates by Stage 2 score alone. The residual variant preserves Stage 1 ordering information by min-max normalizing both score arrays **within the candidate set**:

\[
S_{res}(d)=\lambda\,\hat{s}_{Stage1}(d)+(1-\lambda)\,\hat{s}_{reranker}(d).
\]

The best MiniLM result in Table 6 uses \(\lambda=0.70\). Residual reranking can only reorder retrieved candidates; it cannot recall an absent policy. The BGE-Reranker-v2-m3 validation is a separate top-15 run and is reported separately below.

## Results

Metrics are transcribed from the uploaded article, notebook outputs, and table images. Percentages are percentage points; MRR is a 0–1 value. All rows use 250 tickets unless otherwise indicated by the source. The source has exploratory cells with incorrect mappings and earlier failed/zero-score attempts; only the final, aligned score outputs cited in each table are used here.

### Table 1 — Overall BM25 benchmark and query-type split

| Pipeline | Recall@1 | Recall@3 | Recall@5 | MRR@5 |
|---|---:|---:|---:|---:|
| BM25 — raw uncleaned PDFs | 58.4% | 71.2% | 74.8% | 0.6491 |
| BM25 — boilerplate-cleaned PDFs | 58.4% | 71.2% | 74.8% | 0.6491 |
| BM25 — context-enriched chunks | 55.6% | 67.6% | 74.4% | 0.6238 |

| Query type (125 each) | Recall@1 | Recall@3 | Recall@5 | MRR@5 |
|---|---:|---:|---:|---:|
| `lexical_keyword` | 82.4% | 85.6% | 89.6% | 0.8496 |
| `semantic_intent` | 28.8% | 49.6% | 59.2% | 0.3980 |

The article's prose cites semantic Recall@3 = 49.6%; the table image includes Recall@3 = 49.6%. BM25 raw and cleaned scores are identical in this reported final table.

### Table 2 — Standalone sparse and dense retrieval (768d)

| Method | Recall@1 | Recall@3 | Recall@5 | Recall@10 | MRR@10 |
|---|---:|---:|---:|---:|---:|
| BM25 sparse keyword | 16.00% | 30.00% | 37.20% | 47.60% | 0.2514 |
| BAAI BGE-base-en-v1.5 | 56.80% | 72.00% | 78.40% | 86.00% | 0.6616 |
| EmbeddingGemma 2 | **80.00%** | 82.80% | 84.00% | 87.60% | **0.8207** |
| OpenAI `text-embedding-3-small` | 74.00% | 81.60% | 82.40% | 84.00% | 0.7788 |

### Table 3 — Standalone vs. hybrid retrieval

| Method | Recall@1 | Recall@3 | Recall@5 | Recall@10 | MRR@10 |
|---|---:|---:|---:|---:|---:|
| BM25 only | 16.00% | 30.00% | 37.20% | 47.60% | 0.2514 |
| BGE-base only | 56.80% | 72.00% | 78.40% | 86.00% | 0.6616 |
| OpenAI only | 74.00% | 81.60% | 82.40% | 84.00% | 0.7788 |
| EmbeddingGemma 2 only | 80.00% | 82.80% | 84.00% | 87.60% | 0.8207 |
| RRF 50/50 — BM25 + BGE | 43.60% | 61.20% | 67.20% | 77.20% | 0.5441 |
| RRF 50/50 — BM25 + OpenAI | 52.80% | 74.00% | 80.00% | 90.80% | 0.6527 |
| RRF 50/50 — BM25 + Gemma 2 | 55.60% | 76.00% | 85.60% | **94.80%** | 0.6823 |
| Linear 85/15 — BM25 + BGE | 57.20% | 71.60% | 78.40% | 87.20% | 0.6645 |
| Linear 85/15 — BM25 + OpenAI | 76.00% | 82.40% | 83.20% | 86.00% | 0.7953 |
| Linear 85/15 — BM25 + Gemma 2 | 79.60% | 83.60% | 86.40% | 89.20% | 0.8261 |

Linear weights are dense/sparse as specified in the prose and notebook. RRF provides a high-recall candidate set, but is not the strongest top-slot ranker in this table.

### Table 4 — Fusion weight sweep (Gemma 2 + BM25)

| Method | Recall@1 | Recall@3 | Recall@5 | Recall@10 | MRR@10 |
|---|---:|---:|---:|---:|---:|
| Gemma 2 only (100% dense) | 80.00% | 82.80% | 84.00% | 87.60% | 0.8207 |
| RRF 50% dense / 50% BM25 | 55.60% | 76.00% | 85.60% | 94.80% | 0.6823 |
| RRF 65% dense / 35% BM25 | 67.20% | 84.00% | 86.40% | 90.80% | 0.7622 |
| RRF 75% dense / 25% BM25 | 72.80% | 83.20% | 85.20% | 88.80% | 0.7883 |
| Linear 70% dense / 30% BM25 | 79.20% | **88.80%** | **90.40%** | **94.80%** | **0.8434** |
| Linear 85% dense / 15% BM25 | 79.60% | 83.60% | 86.40% | 89.20% | 0.8261 |

### Table 5 — Stage 1 vs. naive Stage 2 overwrite (MiniLM)

| Method | Recall@1 | Recall@3 | Recall@5 | Recall@10 | MRR@10 |
|---|---:|---:|---:|---:|---:|
| Stage 1 — Gemma 2 dense | 80.00% | 82.80% | 84.00% | 87.60% | 0.8207 |
| Stage 1 — RRF 50/50 | 55.60% | 76.00% | 85.60% | 94.80% | 0.6823 |
| Stage 1 — linear 70/30 | 79.20% | 88.80% | 90.40% | 94.80% | 0.8434 |
| Stage 2 — Gemma 2 + MiniLM rerank | 52.40% | 69.60% | 77.20% | 87.60% | 0.6315 |
| Stage 2 — RRF 50/50 + MiniLM rerank | 57.20% | 75.60% | 81.20% | 94.80% | 0.6854 |
| Stage 2 — linear 70/30 + MiniLM overwrite | 61.60% | 78.00% | 83.60% | 94.80% | 0.7182 |

The 22M cross-encoder improves the RRF top-1 only modestly but degrades the tuned linear hybrid's Recall@1 by 17.6 points (79.2 → 61.6). Recall@10 remains at the Stage 1 candidate ceiling for hybrid rows.

### Table 6 — Residual reranking (MiniLM)

| Method | Recall@1 | Recall@3 | Recall@5 | Recall@10 | MRR@10 |
|---|---:|---:|---:|---:|---:|
| Stage 1 linear 70/30 baseline | 79.20% | 88.80% | 90.40% | 94.80% | 0.8434 |
| Stage 2 overwrite (0% Stage 1 / 100% MiniLM) | 61.60% | 78.00% | 83.60% | 94.80% | 0.7182 |
| Residual 70% Stage 1 / 30% MiniLM | **81.20%** | **92.80%** | **94.40%** | 94.80% | **0.8662** |
| Residual 80% Stage 1 / 20% MiniLM | **81.20%** | 90.40% | 94.00% | 94.80% | 0.8625 |
| Residual 90% Stage 1 / 10% MiniLM | 80.00% | 89.20% | 91.60% | 94.80% | 0.8515 |

### Checking with a Larger Reranker (BGE-Reranker-v2-m3)

| Pipeline Stage | R@1 | R@3 | R@5 | R@10 | MRR@10 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Stage 1 Baseline (Gemma2 + BM25) | 79.2% | 88.8% | 90.4% | 93.2% | 0.8414 |
| **Stage 2 BGE-Reranker-v2-m3 (568M)** | **83.2%** | **92.4%** | **92.8%** | **93.2%** | **0.8782** |

The degradation from naively replacing Stage 1's ranking with `ms-marco-MiniLM-L-6-v2` (22M parameters) points to a capacity inversion: this lightweight cross-encoder has less semantic capacity than the 308M-parameter EmbeddingGemma Stage 1 retriever. Without stabilization through Residual Reranking, the smaller model can weaken nuanced policy rankings.

Testing the hypothesis with the higher-capacity `BAAI/bge-reranker-v2-m3` (568M parameters) shows that scaling reranker capacity above the Stage 1 bi-encoder helps resolve nuanced policy distinctions directly. Recall@1 rises from **79.2% to 83.2%** (+4.0 percentage points), Recall@5 from **90.4% to 92.8%**, and MRR@10 from **0.8414 to 0.8782**.

The architectural trade-off is clear: **Residual Reranking with MiniLM (22M)** delivers ~99% of the gains at ultra-low CPU latency, while **BGE-Reranker-v2-m3 (568M)** provides the highest absolute ceiling (**83.2% R@1 / 0.8782 MRR@10**) when GPU compute budgets allow.
### Summary of all phases

The uploaded `table 7.jpg` summary figure is partly cropped/illegible. Rather than infer obscured cells, this summary table consolidates only fully legible reported rows above. “Not reported” means that specific value is unavailable for that exact protocol.

| Pipeline stage | Recall@1 | Recall@3 | Recall@5 | Recall@10 | MRR |
|---|---:|---:|---:|---:|---:|
| Phase 1 — context-enriched BM25 | 55.6% | 67.6% | 74.4% | Not reported | MRR@5 0.6238 |
| Phase 2 — EmbeddingGemma 2 dense | 80.0% | 82.8% | 84.0% | 87.6% | MRR@10 0.8207 |
| Phase 3 — hybrid linear 70/30 | 79.2% | 88.8% | 90.4% | 94.8% | MRR@10 0.8434 |
| Phase 3 — MiniLM overwrite | 61.6% | 78.0% | 83.6% | 94.8% | MRR@10 0.7182 |
| Phase 3 — residual 70/30 | 81.2% | 92.8% | 94.4% | 94.8% | MRR@10 0.8662 |
| Separate validation — BGE-Reranker-v2-m3 | 83.2% | 92.4% | 92.8% | 93.2% | MRR@10 0.8782 |

## Failure modes and interpretation

1. **Lexical/semantic asymmetry.** BM25's 82.4% Recall@1 on exact-anchor queries falls to 28.8% on semantic-intent queries. Exact codes, fees, and form IDs favor sparse retrieval; casual customer language favors dense retrieval.
2. **More candidates does not mean a better answer at rank 1.** RRF 50/50 lifts Gemma's Recall@10 from 87.6% to 94.8%, while Recall@1 falls from 80.0% to 55.6%. A high-recall candidate set still needs a ranker that preserves ordering quality.
3. **Naive reranking can be destructive.** The small MiniLM model reorders from scratch and damages the tuned Stage 1 scores. Cross-encoder size/quality, candidate construction, chunk text, and evaluation alignment all matter.
4. **Residual blending is a tested mitigation, not a universal theorem.** Preserving 70% of the tuned hybrid score and adding 30% reranker score beats the Stage 1 baseline in the reported MiniLM experiment. The blend is candidate-local and min-max scale sensitive.
5. **Retrieval miss can masquerade as policy gap.** A grounded answer/audit can still be wrong if the controlling policy never enters Top-K. Production policy-gap claims should be gated on retrieval coverage and validated corpus ingestion.
6. **Corpus representation changes scores.** Chunk size/content, boilerplate, headings, context headers, canonical IDs, and duplicate chunks influence candidate ranks. The 414 substantive chunk view and 713-chunk scored view should not be conflated.
7. **Benchmark artifact/metric caveats.** The original notebook includes duplicated cells, API-prompt output, failed cells, changing column mappings, and a visible zero-recall artifact caused by mismatched IDs. Several outputs have corrected runs later. Metric tables here are grounded in the final aligned result outputs and article figures; independently recompute from the raw predictions before production claims.

## Reproduction and artifact boundaries

### Included

- `data/chunks.csv`: full-text corpus of all 713 chunks across 100 policies (not a preview).
- `data/expanded_tickets.csv`, `.json`, `.xlsx`: 250 labeled evaluation tickets.
- `src/phase1_ingest.py`: reusable PDF extraction, boilerplate-cleaning, and chunking module.
- `data/corpus_metadata.csv`, `data/corpus_manifest.{csv,json,xlsx}`: policy metadata, filenames, and anchors.
- `assets/`: supplied benchmark figures and category-folder illustration.
- `notebooks/hybrid_rag_benchmark.ipynb`: clean end-to-end BM25 baseline against the packaged chunks/tickets.
- `notebooks/reproduction_guide.ipynb`: data validation, evaluation contract, and run guidance.
- `notebooks/source_notebook_sanitized.ipynb`: compatibility filename for the clean notebook; it no longer carries the exploratory source-cell sequence or outputs.

### Not included

- 100 source policy PDFs. They are not needed for the packaged-corpus notebook; `phase1_ingest.py` can be used if those PDFs are separately available.
- BM25/dense score checkpoints, dense embedding arrays, reranker weights, and per-query historical rankings. Dense/reranker stages require model downloads, compute, and any applicable API credentials.
- The benchmark figure for “Summary of All Phases” is incomplete/cropped; numeric summary cells were not reconstructed where illegible.

### Steps after restoring missing source artifacts

1. Install Python dependencies: `pandas`, `numpy`, `rank-bm25`, `sentence-transformers`, plus PyMuPDF for PDF extraction. Use a GPU for practical embedding/reranker throughput; model downloads require network access.
2. For the included BM25 baseline, open `notebooks/hybrid_rag_benchmark.ipynb`; it reads `data/chunks.csv` and `data/expanded_tickets.csv` directly. If regenerating ingestion instead, supply the original category-organized PDFs to `src/phase1_ingest.py`.
3. Confirm all 250 `primary_expected_doc_id` values map to the chunk source-file stems; use `customer_query` as query text, not `key_retrieval_anchor_or_rationale`.
4. Generate or restore 768d document/query vectors. OpenAI-compatible API calls need a key through Colab Secrets/environment variable; never paste or commit secrets. The source notebook accidentally displayed a credential in an interactive output: **revoke/rotate that credential if it is real**.
5. Score BM25 + cosine, evaluate document-level rankings; run fusion weight sweeps, then rerank fixed Stage 1 candidate lists. Save model revisions, configs, hardware, query-level output, and alignment checks alongside aggregate scores.
6. Compare results to the tables with the same candidate count and scoring protocol. Avoid mixing the separate BGE top-15 run with the MiniLM residual run.

## Repository map

```text
06-hybrid-rag-retrieval-benchmark/
├── README.md
├── assets/
│   ├── table1_bm25_benchmark.png
│   ├── table2_dense_retrieval_comparison.png
│   ├── table3_standalone_vs_hybrid.png
│   ├── table4_fusion_weight_optimization.png
│   ├── table5_stage1_vs_reranking.jpg
│   ├── table6_residual_reranking.jpg
│   ├── table7_summary_all_phases_original.jpg
│   ├── bge_reranker_v2_m3_validation.png
│   └── corpus_category_folders.png
├── data/
│   ├── expanded_tickets.{csv,json,xlsx}
│   ├── chunks.csv  (713 full-text chunks)
│   ├── corpus_manifest.{csv,json,xlsx}
│   └── corpus_metadata.csv
├── src/
│   └── phase1_ingest.py
└── notebooks/
    ├── hybrid_rag_benchmark.ipynb
    ├── reproduction_guide.ipynb
    └── source_notebook_sanitized.ipynb  (clean compatibility copy)
```

## Sources and scope

Project results were transcribed from the uploaded article, `EmbeddingGemma2 project 2.ipynb`, spreadsheet data, and accompanying table images. The notebook is experimental research material, not a production RAG service. No customer-facing decisions are made here. Validate data rights, benchmark labels, retrieval coverage, and model behavior before using this design in a live policy workflow.

---

## Read the companion article

**[Scaling Enterprise RAG: What Breaks, What Fails Silently, and How to Fix It ↗](https://flyinghigherai.substack.com/p/scaling-enterprise-rag-what-breaks)** — the article behind this benchmark, covering corpus ingestion, retrieval stages, hybrid fusion, and reranking.
