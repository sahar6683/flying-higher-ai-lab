# 🛫 Flying Higher AI Lab

[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![Maintained](https://img.shields.io/badge/maintained-yes-blue.svg)]()
[![n8n](https://img.shields.io/badge/n8n-workflows-ff6d5b?logo=n8n&logoColor=white)](https://n8n.io)
[![Python](https://img.shields.io/badge/python-ready-3776ab?logo=python&logoColor=white)]()
[![RAG](https://img.shields.io/badge/RAG-planned-orange)]()
[![Agentic](https://img.shields.io/badge/agentic-planned-purple)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()
[![PRs](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)]()
 

> **An open lab for real, observable, deterministic-by-default AI business systems.**
> Built on **n8n + Python**, designed to grow into **RAG** and **agentic** systems without throwing the foundation away.

This is the master monorepo (`flying-higher-ai-lab`) for everything I build at [Flying Higher AI](https://github.com/flyinghigherai). Every project here ships:

- ✅ **Sanitized n8n workflow JSONs** (drop-in imports)
- ✅ **A deep-dive README** with architecture diagrams, prompt breakdowns and setup steps
- ✅ **Engineering notes** on what broke, why, and what I changed
- ✅ **Eval/eval-set guidance** so you can validate any new model swap

---

## 🧭 Engineering philosophy

> *“Learning enough to question the AI, understand the workflow, and make my own decisions is what made the project useful.”*

Six rules govern every project in this lab:

1. **Diagnose the business problem before opening the platform.** Tech serves the problem.
2. **The workflow is the product.** Good nodes ≠ good design.
3. **AI is one component.** Quotas, rate limits, output formats, and failure modes are first-class architecture.
4. **Don't ask the LLM to be deterministic.** Use typed outputs, criteria, eval sets, and Code nodes for anything that has to be exact.
5. **Test before you scale.** One document → two → five → many. Know how many times each node fires.
6. **Humans still own the decision.** Automation removes repetitive work; judgment stays with humans.

---

## 🗂️ Architecture index

| # | Project | Stack | Status | What it proves |
|---|---------|-------|--------|----------------|
| 01 | [Document Intelligence Pipeline](./01-Document-Intelligence-Pipeline) | n8n · Gemini · OpenRouter · PDF.co · Drive · Gmail | ✅ V2 · V3 · V4 shipped | Why naive AI automation breaks at scale; structured output parsing vs deterministic Code-node aggregation; LLM eval set as a first-class artifact. |
| 02 | [AI Email Intelligence & Routing (Jev)](./02-AI-Email-Intelligence-Routing-JEV) | n8n · OpenRouter · Jev · Gmail · Slack · Sheets | ✅ v1 · v2 shipped | Why LLMs are bad at deterministic yes/no; replace LLM adjudication with a typed decision model; confidence + urgency gating; human escalation vs automated multi-channel routing. |
| 03 | [AI Purchase Request Approval & Routing System](./03-ai-purchase-request-routing-jev) | n8n · OpenRouter · JEV (noul + score + choice) · Gmail · Gemini · Slack | ✅ Live | All three JEV primitives in one workflow: `noul` for missing-info gate, `score` for risk gate, `choice` for department routing — plus Gemini-drafted Slack messages. |
| 04 | [Northstar Support RAG Knowledge Base (Qdrant + JEV)](./04-rag-knowledge-base-qdrant-jev) | n8n · Qdrant · OpenAI embeddings · Gemini 2.5 Pro · OpenRouter · JEV · Sheets · Slack | ✅ Live | Three-stage evolution: Drive→Qdrant ingestion, baseline RAG, and production RAG with **JEV grounding gate** + Slack escalation. Zero hallucinated answers shipped to users. |
| 05 | [Intelligent Customer Operations (Multimodal RAG)](./05-intelligent-customer-ops-multimodal-rag) | n8n · Qdrant · OpenAI embeddings · OpenAI Vision (gpt-5-mini) · Gemini · Sheets · Data Tables | ✅ Live | End-to-end auditable multimodal RAG: photo inspection **before** policy eval, structured 4-bucket triage, full audit trail in Sheets + Data Tables. Companion Matryoshka benchmark (OpenAI vs EmbeddingGemma 2 at 768/512/256/128d) justifies the production `top-k=4, dimensions=768` choice. |
---

## 📁 Repository layout

```
flying-higher-ai-lab/
├── README.md                              ← you are here
├── PROFILE_README.md                      ← drop-in copy for github.com/<you>/<you>
├── LICENSE
├── .gitignore
├── assets/                                ← logos, badges, screenshots
│
├── 01-Document-Intelligence-Pipeline/
│   ├── README.md                          ← deep-dive: V2 → V3 → V4 evolution
│   ├── diagrams/
│   │   ├── architecture-v4.mmd
│   │   └── pipeline-overview.mmd
│   └── workflows/
│       ├── DocumentAnalysisV2.sanitized.json
│       ├── DocumentAnalysisV3.sanitized.json
│       └── DocumentAnalysisV4.sanitized.json
│
├── 02-AI-Email-Intelligence-Routing-JEV/
│   ├── README.md
│   ├── diagrams/
│   │   ├── architecture-v2.mmd
│   │   └── routing-overview.mmd
│   ├── assets/
│   │   ├── workflow-v1.png
│   │   └── workflow-v2.png
│   └── workflows/
│       ├── AIEmailIntelligenceRouting.v1.sanitized.json
│       └── AIEmailIntelligenceRouting.v2.sanitized.json
│
├── 03-ai-purchase-request-routing-jev/
│   ├── README.md
│   ├── diagrams/
│   │   └── architecture.mmd
│   ├── workflows/
│   │   └── workflow.sanitized.json
│   └── screenshots/
│       ├── workflow-overview.png
│       ├── gmail-trigger-inbox.png
│       ├── get-many-messages-redacted.png       ← personal emails redacted
│       ├── jev-noul-check-missing-info.png
│       ├── jev-noul-output-1.png … 4.png
│       ├── jev-score-risk-assessment.png
│       └── slack-channel-output.png
│
├── 04-rag-knowledge-base-qdrant-jev/
│   ├── README.md
│   ├── diagrams/
│   │   └── architecture.mmd
│   ├── workflows/
│   │   ├── workflow-a-ingestion.sanitized.json   ← Drive → Qdrant
│   │   ├── workflow-b-rag-baseline.sanitized.json ← Baseline RAG (no JEV)
│   │   └── workflow-b-v2-rag-with-jev.sanitized.json ← Production RAG with JEV grounding gate
│   └── screenshots/
│       ├── workflow-b-rag-baseline.png
│       ├── workflow-b-v2-with-jev.png
│       ├── support-question-sample-1.png
│       └── support-question-sample-2.png
│
└── 05-intelligent-customer-ops-multimodal-rag/
    ├── README.md                          ← deep-dive: multimodal RAG + Matryoshka benchmark
    ├── diagrams/
    │   └── architecture.mmd
    ├── workflows/
    │   ├── intake-of-queries.sanitized.json           ← WordPress → webhook → Drive → Sheets
    │   └── processing-multimodal-rag.sanitized.json   ← Qdrant retrieve → Vision inspect → LLM eval → structured output
    ├── data/
    │   ├── northstar-cases-sample.csv
    │   └── northstar-retrieval-test-dataset.csv
    ├── eval/
    │   └── (Hit@K + latency tables live here)
    └── screenshots/
        ├── 01-intake-webhook-wordpress.png
        ├── 02-intake-get-from-webhook.png
        ├── 03-processing-workflow-overview.png
        ├── 04-processing-qdrant-retrieval.png
        ├── 05-processing-vision-image-inspection.png
        ├── 06-processing-llm-chain-structured-output.png
        ├── 07-processing-update-sheet-and-datatable.png
        ├── 08-benchmark-cosine-similarity-inspection.png
        ├── 09-benchmark-topk-hits-comparison.png
        ├── 10-benchmark-matryoshka-truncation.png
        ├── 11-benchmark-dimension-vs-accuracy.png
        ├── 12-matryoshka-dolls-concept.png
        ├── 13-benchmark-summary-table.png
        ├── 14-benchmark-table-upscaled.png
        └── 15-processing-workflow-walkthrough.mp4

```

---

## 🚀 Quick start

```bash
# 1. Clone
git clone https://github.com/flyinghigherai/flying-higher-ai-lab.git
cd flying-higher-ai-lab

# 2. Pick a project
cd 01-Document-Intelligence-Pipeline

# 3. Import the sanitized workflow(s) into your n8n instance
#    n8n UI  →  Workflows  →  Import from File  →  pick *.sanitized.json

# 4. Re-create the credentials listed in the project README
#    (PDF.co, Gmail OAuth2, Google Drive, Google Sheets, OpenRouter, Slack, …)

# 5. Run with a small fixture first, then scale.
```

> **Heads-up on sanitization:** every JSON in `workflows/` has been scrubbed of:
> - credential references (replaced with `YOUR_*_CREDENTIAL` placeholders)
> - real Google Drive / Sheets IDs and URLs
> - hardcoded email recipients
> - Slack channel IDs
> - cached UI selections and execution metadata
>
> You **must** create the credentials on your n8n instance and pick your own Drive folder / Sheet / Slack channels. The original workflows were test exports; the sanitized versions are importable into a fresh n8n instance without leaking anything.

---

## 🧪 The eval-set discipline

Every project ships an **eval set** — a small set of inputs with known expected outputs. Before swapping any model, prompt, or temperature, the workflow is re-run against this set. If accuracy drops, the swap doesn't ship.

This is the single biggest change that took my systems from "looks promising in staging" to "actually safe to point at real mailboxes." The article [Why LLMs are not deterministic decision engines](./articles/02-i-thought-llms-could-handle-yesno-decisions.md) walks through the failure mode.

---

## 📚 Published Articles (Flying Higher AI on Substack)

Every system in this repository is paired with a deep-dive engineering case study documenting the architectural trade-offs, failure modes, and benchmark results behind the build:
*Tip: Hold `Ctrl` (Windows) or `Cmd` (Mac) while clicking to open articles in a new tab!*

- **<a href="https://flyinghigherai.substack.com/p/i-thought-ai-could-build-the-automation" target="_blank" rel="noopener noreferrer">01 — I Thought AI Could Build the Automation for Me. Then I Had to Learn How to Think Like an Engineer ↗</a>**  
  The honest journey from *"GPT, build me an automation"* to *"GPT, help me build **my** automation."* Covers the failure modes of blindly following AI architecture suggestions, handling API rate limits and item multiplication, replacing fragile LLM aggregation with deterministic code, and when to use n8n at all.

- **<a href="https://flyinghigherai.substack.com/p/i-thought-llms-could-handle-yesno" target="_blank" rel="noopener noreferrer">02 — I Thought LLMs Could Handle "Yes/No" Decisions. Here's What I Learned ↗</a>**  
  A live case study of building a YES/NO review classifier for incoming business documents. Explores how temperature, prompt phrasing, and model choice change the result, why raw LLMs drift on binary classification, and why an evaluation set is non-negotiable.

- **<a href="https://flyinghigherai.substack.com/p/how-integrating-jev-made-my-email" target="_blank" rel="noopener noreferrer">03 — How Integrating JEV Made My Email Routing Faster and More Accurate ↗</a>**  
  Replacing brittle multi-branch prompt chains with a structured System-1 decision model (`jev`). How typed classification criteria and confidence scores transformed a noisy inbox router into a fast, deterministic triage pipeline.

- **<a href="https://flyinghigherai.substack.com/p/i-used-all-three-jev-primitives-in" target="_blank" rel="noopener noreferrer">04 — I Used All Three JEV Primitives in One Workflow. Here’s What I Learned ↗</a>**  
  Combining binary gates, multi-class routing, and structured scoring inside a single end-to-end n8n automation—and how to design clean handoffs between decision primitives and downstream actions.

- **<a href="https://flyinghigherai.substack.com/p/building-a-rag-knowledge-base-in" target="_blank" rel="noopener noreferrer">05 — Building a RAG Knowledge Base in n8n with Qdrant and JEV Nodes ↗</a>**  
  Architecting a production Retrieval-Augmented Generation (RAG) system using n8n, Qdrant Cloud vector storage, and `jev` decision gates to filter retrieval quality and prevent hallucinated answers.

- **<a href="https://flyinghigherai.substack.com/p/jev-can-see-typesafes-new-release" target="_blank" rel="noopener noreferrer">06 — Jev Can See: TypeSafe's New Release Brings Images to the System One Model ↗</a>**  
  Testing multimodal System-1 decision-making: passing visual inputs and images directly into `jev` nodes for fast, typed visual classification and routing inside automated workflows.

- **<a href="https://flyinghigherai.substack.com/p/what-i-learned-benchmarking-embeddinggemma" target="_blank" rel="noopener noreferrer">07 — What I Learned Benchmarking EmbeddingGemma Against OpenAI ↗</a>**  
  Head-to-head retrieval benchmark of Google’s open-weight EmbeddingGemma 2 vs OpenAI’s `text-embedding-3-small` over a 50-query customer-ops test set in Google Colab. Documents how Matryoshka truncation (768 / 512 / 256 / 128 dimensions) holds accuracy while cutting storage by up to two-thirds — and why retrieval misses are usually a chunking problem, not a model problem.

- **<a href="https://flyinghigherai.substack.com/p/beyond-the-vector-space-building" target="_blank" rel="noopener noreferrer">08 — Beyond the Vector Space: Building an Auditable, Multimodal Customer Ops Pipeline in n8n ↗</a>**  
 How I bridged dense retrieval, Vision models, and structured business rules to triage 50 real-world customer tickets

- **<a href="https://flyinghigherai.substack.com/p/scaling-enterprise-rag-what-breaks" target="_blank" rel="noopener noreferrer">09 — Scaling Enterprise RAG: What Breaks, What Fails Silently, and How to Fix It ↗</a>**  
 HMoving from 10 to 100 documents: how we diagnosed broken retrieval stages and pushed recall to 94.8%.

👉 **Subscribe & read the full publication:** **[flyinghigherai.substack.com](https://flyinghigherai.substack.com/)**
---
## 🧰 Tech & Tools

| Layer | Stack & Tooling |
|---|---|
| **Orchestration** | n8n (self-hosted), Webhooks, Event-Driven Pipelines |
| **LLMs (System-2)** | OpenAI (GPT), Anthropic (Claude), Google Gemini, DeepSeek (via OpenRouter) |
| **Decision Models (System-1)** | TypeSafe **JEV** (Typed Primitives: Choice, Score, Check, Multimodal/Vision, Confidence Gating) |
| **Vector DB & RAG** | **Qdrant Cloud**, Embeddings, Semantic Chunking & Retrieval Pipelines |
| **Document Intelligence** | PDF.co (OCR & PDF-to-Text), Multimodal Vision Extraction |
| **Web & App Integrations** | WordPress (Webhooks & REST API), Gmail, Google Drive, Google Sheets |
| **Ops & Alerting** | Slack (Human-in-the-Loop Escalation & Audit Channels) |
| **Data & Glue Code** | JavaScript & Python (n8n Code Nodes), SQL, REST/HTTP APIs, JSON Schema |



---

## 📜 License

[MIT](./LICENSE) — use it, fork it, build on it.

---

> *I don’t see automation as a way to eliminate people. I see it as a way to remove some of the repetitive work that consumes people’s time and attention.*
