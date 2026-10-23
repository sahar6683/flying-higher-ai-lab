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
| 03 | RAG Knowledge Assistant | Python · embeddings · vector store · n8n bridge | 🟡 planned | Same engineering discipline applied to retrieval — eval set, chunking strategy, observability. |
| 04 | Agentic Workflow Orchestrator | Python · tool-use · planning loop · n8n hit-points | 🟡 planned | The next leap: bounded agents with explicit tool contracts, deterministic checkpoints and audit trails. |
| 05 | … | — | ⚪ backlog | Tell me what business problem you'd like to see solved next. |

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
│   ├── README.md                          ← deep-dive: v1 → v2 evolution
│   ├── diagrams/
│   │   ├── architecture-v2.mmd
│   │   └── routing-overview.mmd
│   └── workflows/
│       ├── AIEmailIntelligenceRouting.v1.sanitized.json
│       └── AIEmailIntelligenceRouting.v2.sanitized.json
│
└── articles/
    ├── 01-i-thought-ai-could-build-the-automation-for-me.md
    └── 02-i-thought-llms-could-handle-yesno-decisions.md
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

- **[01 — I Thought AI Could Build the Automation for Me. Then I Had to Learn How to Think Like an Engineer](https://flyinghigherai.substack.com/p/i-thought-ai-could-build-the-automation)**  
  The honest journey from *"GPT, build me an automation"* to *"GPT, help me build **my** automation."* Covers the failure modes of blindly following AI architecture suggestions, handling API rate limits and item multiplication, replacing fragile LLM aggregation with deterministic code, and when to use n8n at all.

- **[02 — I Thought LLMs Could Handle "Yes/No" Decisions. Here's What I Learned.](https://flyinghigherai.substack.com/p/i-thought-llms-could-handle-yesno)**  
  A live case study of building a binary `YES/NO` review gate for incoming business documents. Explores why standard LLMs over-escalate, how bidirectional negative-boundary prompting and `temperature: 0` change behavior across Gemini and DeepSeek, and why an evaluation dataset is non-negotiable before scaling.

- **[03 — How Integrating JEV Made My Email Routing Faster and More Accurate](https://flyinghigherai.substack.com/p/how-integrating-jev-made-my-email)**  
  Why free-form generative LLMs are overkill for operational triage. Walks through replacing fragile JSON prompt parsing with TypeSafe's `jev` System-1 decision model to get low-latency, schema-guaranteed classifications, epistemic confidence scores, and automated human-in-the-loop escalation.

- **[04 — I Used All Three JEV Primitives in One Workflow. Here’s What I Learned.](https://flyinghigherai.substack.com/p/i-used-all-three-jev-primitives-in)**  
  An architectural deep-dive into combining all three structured decision primitives—**Choice** (categorical routing), **Score** (continuous urgency/priority evaluation), and **Check/Boolean** (policy and threshold verification)—inside a single multi-stage n8n workflow.

- **[05 — Building a RAG Knowledge Base in n8n with Qdrant and JEV Nodes](https://flyinghigherai.substack.com/p/building-a-rag-knowledge-base-in)**  
  Combining Retrieval-Augmented Generation (RAG) with deterministic decision gating. Covers vector ingestion and semantic search in **Qdrant**, coupled with **JEV** decision nodes to evaluate retrieval quality, gate hallucinations, and route customer or internal queries reliably.

- **[06 — Jev Can See: TypeSafe's New Release Brings Images to the System One Model](https://flyinghigherai.substack.com/p/jev-can-see-typesafes-new-release)**  
  Extending structured System-1 decision models from text to vision. Exploring multimodal classification, visual inspection, and fast, typed decision-making directly over image inputs without the latency or formatting fragility of large vision-language models.

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
