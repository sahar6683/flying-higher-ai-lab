 [README.md](https://github.com/user-attachments/files/33912373/README.md)
# Project 04 — Northstar Support RAG Knowledge Base (Qdrant + JEV)

> **A three-stage n8n system that ingests Northstar's support documents into Qdrant, runs a baseline RAG over a Google Sheets queue, and finally gates every generated reply with a JEV grounding check before it is ever shipped to a user.**

This is the **RAG evolution**: a Drive → Qdrant ingestion pipeline (Workflow A), a baseline RAG (Workflow B), and a production RAG with a JEV grounding gate and Slack escalation (Workflow B v2). The big idea: **stop letting the LLM ship answers it can't justify from the retrieved chunks.** Every reply is either *grounded* (writes back to the Sheets queue as `status=answered`) or *escalated* (paged to Slack `#human-review` with the retrieved chunks attached).

---

## 🎯 The business problem

Northstar Office Supplies Ltd. has a growing library of support documents (FAQs, policies, account / how-to guides). Support reps want a **searchable, always-on knowledge base** they can query in natural language and get a draft reply from. The risks:

1. **Hallucination.** A generic RAG will happily invent a refund policy that doesn't exist.
2. **Silent failure.** If the chunks don't actually answer the question, the LLM should not be allowed to "fill in the gaps."
3. **Queue plumbing.** Questions come in via a Google Sheets queue (rows with `status=pending`); replies need to write back with `status=answered` *or* be flagged for human review.

Goal: a system that, for each pending question:

1. Retrieves the top-k chunks from Qdrant.
2. Asks Gemini 2.5 Pro to draft a reply **only from those chunks**.
3. Runs a JEV grounding gate: is the draft actually supported by the chunks?
4. Writes back to Sheets *or* escalates to Slack — never silently ships an unsupported answer.

---

## 🧬 Why a generic RAG isn't safe enough

The full reasoning lives in [Article 02](../../articles/02-i-thought-llms-could-handle-yesno-decisions.md). The condensed version, applied to RAG:

- An LLM is **probabilistic**, not deterministic.
- A prompt that says "answer using only the context" is *not* a contract — the model can still paraphrase a chunk it half-remembers, or merge two chunks into a non-existent policy.
- "Use temperature 0" helps but is not a guarantee across backbones.
- Different models give different answers on the same retrieved chunks.

### What I changed

Instead of trusting the LLM to "be careful," I now ask a **decision model** (JEV via OpenRouter) a typed grounding question and **gate on the result**:

```jsonc
{
  "grounding": {
    "type": "noul",
    "instructions": "Is the drafted reply fully supported by the retrieved chunks?",
    "criteria": { "yes": "Every claim in the reply is present in the chunks.", "no": "At least one claim is not in the chunks." }
  }
}
```

JEV returns a structured `{ choice, confidence }`. The workflow then **gates deterministically**: `choice = yes` → write back to Sheets; `choice = no` → Slack `#human-review` with the chunks attached. The shipping decision is *never* an LLM string match.

A second gate (`JEV Score` → `score >= 7`) is layered in as a defence-in-depth check on overall reply quality.

---

## 🏗️ Architecture

### Workflow A — Drive → Qdrant ingestion

```mermaid
flowchart TD
    A(["Schedule Trigger<br/>or Manual"]) --> B["Google Drive<br/>Search files and folders<br/>folder: Northstar/Support"]
    B --> C["Google Drive<br/>Download file"]
    C --> D["Default Data Loader<br/>parse to documents"]
    D --> E["Embeddings OpenAI<br/>text-embedding-3-small"]
    E --> F["Qdrant Vector Store<br/>upsert chunks<br/>collection: northstar-support"]
```

### Workflow B — baseline RAG (no JEV)

```mermaid
flowchart TD
    A(["Manual Trigger"]) --> B["Get row(s) in sheet<br/>Google Sheets queue"]
    B --> C["Qdrant retrieve<br/>top-k=5"]
    C --> D["Gemini 2.5 Pro<br/>draft reply from chunks"]
    D --> E["Update row in sheet<br/>status=answered"]
```

### Workflow B v2 — production RAG with JEV grounding gate (final shipped version)

```mermaid
flowchart TD
    A(["Manual Trigger"]) --> B["Get row(s) in sheet<br/>status=pending"]
    B --> C{{"HTTP - JEV Choice<br/>classify question type"}}
    C -->|"account / policy / how_to"| P1["Qdrant retrieve<br/>top-k=5"]
    C -->|"other"| Z["Slack #human-review<br/>question type unclear"]
    P1 --> D["Gemini 2.5 Pro<br/>draft reply from chunks"]
    D --> E{{"HTTP - JEV Score<br/>grounding 0-10"}}
    D --> F{{"HTTP - JEV Noul<br/>is answer grounded in chunks?"}}
    E -->|"score >= 7"| G["Update row in sheet<br/>status=answered"]
    E -->|"score < 7"| H["Slack #human-review<br/>+ retrieved chunks attached"]
    F -->|"choice = yes"| G
    F -->|"choice = no"| H
```

### A → B → B v2 — what changed

| Area | Workflow A | Workflow B (baseline) | Workflow B v2 (production) |
|---|---|---|---|
| **Goal** | Ingest support docs into Qdrant | Answer a pending question | Answer *and* verify the answer is grounded |
| **Trigger** | Schedule or Manual | Manual | Manual |
| **Source** | Google Drive folder `Northstar/Support` | Google Sheets queue (`status=pending`) | Google Sheets queue (`status=pending`) |
| **Retrieval** | n/a | Qdrant retrieve `top-k=5` | Qdrant retrieve `top-k=5` (only when question type is account / policy / how_to) |
| **Generation** | n/a | Gemini 2.5 Pro drafts reply from chunks | Gemini 2.5 Pro drafts reply from chunks |
| **Grounding gate** | n/a | None — reply shipped as-is | **JEV `noul`** (is reply grounded?) + **JEV `score`** (overall quality) |
| **Question-type gate** | n/a | None | **JEV `choice`** (account / policy / how_to / other) |
| **Write-back** | Qdrant upsert | Sheets: `status=answered` | Sheets: `status=answered` *only when JEV says yes* |
| **Escalation** | n/a | n/a | Slack `#human-review` with retrieved chunks attached |
| **Risk if it fails** | Stale Qdrant index | Hallucinated answer reaches the user | Hallucinated answer **never reaches the user** |

---

## 🧠 The JEV calls

All three JEV calls go to the OpenRouter **alpha/decisions** endpoint:

```
POST https://openrouter.ai/api/alpha/decisions
Authorization: Bearer YOUR_OPENROUTER_API_KEY
Content-Type: application/json
```

### B v2 — `question_type` (choice) — first gate

```json
{
  "model": "typesafe/jev-1.13",
  "state": {
    "question": "...",
    "subject": "..."
  },
  "questions": {
    "question_type": {
      "type": "choice",
      "instructions": "Classify the type of support question. Only answer 'account / policy / how_to' when the question is genuinely about a Northstar account, a Northstar policy, or a how-to for using a Northstar product. If the question is vague, off-topic, or unrelated, classify it as 'other'.",
      "criteria": {
        "account":  "Question is about a Northstar customer account (login, billing, plan, etc.).",
        "policy":   "Question is about a Northstar policy (returns, refunds, shipping, warranty).",
        "how_to":   "Question is a how-to for using a Northstar product or service.",
        "other":    "Vague, off-topic, or unrelated to Northstar."
      }
    }
  }
}
```

### B v2 — `grounding` (noul) — second gate

```json
{
  "questions": {
    "grounding": {
      "type": "noul",
      "instructions": "Is the drafted reply fully supported by the retrieved chunks?",
      "criteria": {
        "yes": "Every claim in the reply is present in the chunks.",
        "no":  "At least one claim is not in the chunks, or the reply invents a policy, number, or fact."
      }
    }
  }
}
```

### B v2 — `grounding_score` (score) — defence-in-depth third gate

```json
{
  "questions": {
    "grounding_score": {
      "type": "score",
      "instructions": "Rate how well the drafted reply is supported by the retrieved chunks, from 0 (unsupported, hallucinated) to 10 (every claim directly cited).",
      "criteria": {
        "low":    "0-3: reply invents facts not in the chunks.",
        "medium": "4-6: reply is partially grounded, some claims are unsupported.",
        "high":   "7-10: reply is fully grounded in the chunks."
      }
    }
  }
}
```

The response shape is always:

```json
{
  "answers": {
    "question_type":   { "choice": "policy",  "confidence": 0.91 },
    "grounding":       { "choice": "yes",     "confidence": 0.88 },
    "grounding_score": { "score":  8,         "confidence": 0.85 }
  }
}
```

The workflow then uses pure `If` and `Switch` nodes — no LLM in the shipping path.

---

## 📐 The deterministic gates

### Question-type gate

```js
leftValue: $json.answers.question_type.choice
operator:   equals
account / policy / how_to → continue to Qdrant retrieve
other                     → Slack #human-review (question type unclear)
```

### Grounding `noul` gate

```js
leftValue: $json.answers.grounding.choice
operator:   equals
yes → Update row in sheet (status=answered)
no  → Slack #human-review (+ chunks attached)
```

### Grounding `score` gate (defence-in-depth)

```js
leftValue: $json.answers.grounding_score.score
rightValue: 7
operator:   gte
score >= 7 → Update row in sheet (status=answered)
score <  7 → Slack #human-review (+ chunks attached)
```

> **Why two grounding gates?** Belt-and-braces. The `noul` gate is a yes/no on grounding; the `score` gate catches edge cases where JEV says "yes" but the numerical confidence is borderline. Both must clear for a write-back.

---

## 📂 Files in this folder

| File | Purpose |
|---|---|
| `workflows/workflow-a-ingestion.sanitized.json` | Workflow A export — Drive folder → Qdrant upsert. |
| `workflows/workflow-b-rag-baseline.sanitized.json` | Workflow B export — baseline RAG, no grounding gate. |
| `workflows/workflow-b-v2-rag-with-jev.sanitized.json` | Workflow B v2 export — production RAG with JEV `choice` + `noul` + `score` gates. **Recommended import.** |
| `diagrams/architecture.mmd` | Mermaid source for the Workflow B v2 architecture diagram (final shipped version). |
| `screenshots/workflow-b-rag-baseline.png` | Screenshot of Workflow B baseline. |
| `screenshots/workflow-b-v2-with-jev.png` | Screenshot of Workflow B v2 (final shipped version). |
| `screenshots/support-question-sample-1.png` | Sample pending question (Sheet row). |
| `screenshots/support-question-sample-2.png` | Sample pending question (Sheet row). |

---

## ⚙️ Setup instructions

### Prerequisites

- A self-hosted or cloud n8n instance (≥ 1.50 recommended).
- Credentials in n8n for:
  - **Google Drive OAuth2** (search + download — Workflow A)
  - **Qdrant** (self-hosted endpoint *or* Qdrant Cloud API key) — Workflows A, B, B v2
  - **OpenAI API** (for `text-embedding-3-small` embeddings) — Workflows A, B, B v2
  - **Google Gemini (PaLM) API** (for `gemini-2.5-pro`) — Workflows B, B v2
  - **Google Sheets OAuth2** — Workflows B, B v2
  - **OpenRouter API** (for JEV via `openRouterApi`) — Workflow B v2
  - **Slack OAuth2** (`slackOAuth2Api`) — Workflow B v2
- A Qdrant collection named `northstar-support` with the right vector size (1536 for `text-embedding-3-small`).
- A Google Drive folder named `Northstar/Support` containing the support PDFs/docs to ingest.
- A Google Sheet with columns: `status, question, subject, draft_reply, grounding_choice, grounding_score, grounding_confidence, retrieved_chunks`.

### Import the workflows

1. In n8n: **Workflows → Import from File…**
2. Pick `workflow-a-ingestion.sanitized.json`, then `workflow-b-v2-rag-with-jev.sanitized.json` (skip B baseline for production).
3. Re-create the credentials. The placeholder IDs will resolve when you select a real credential in each node.

### Configure Workflow A (ingestion)

- In **Schedule Trigger**, set the cron to your preferred re-ingestion cadence (e.g. nightly).
- In **Google Drive: Search files and folders**, point `folderId` at your `Northstar/Support` folder.
- In **Qdrant Vector Store**, set `collection` to `northstar-support` and `mode` to `insert` (or `upsert` if you re-ingest).
- In **Embeddings OpenAI**, the model is `text-embedding-3-small` (1536 dims) — keep dims consistent with the collection.

### Configure Workflow B v2 (production RAG)

- In **Get row(s) in sheet**, set `status = pending` as the filter.
- In **HTTP - JEV Choice**, the model is `typesafe/jev-1.13` — keep it unless you have an eval set justifying a swap.
- In **Qdrant Vector Store**, set `top-k = 5`.
- In **HTTP - JEV Score**, the threshold is `>= 7` (see `If` node).
- In **HTTP - JEV Noul**, the gate is `choice = yes` → write-back; `choice = no` → escalation.
- In **Slack #human-review**, replace `<YOUR_SLACK_CHANNEL_ID>` with the real channel ID.
- In **Update row in sheet**, set `status = answered` and write back the draft reply + grounding metadata.

### Configure the JEV gates

- The HTTP Request nodes already include `Authorization: Bearer YOUR_OPENROUTER_API_KEY` — when you select a real `openRouterApi` credential, n8n will replace this header automatically.
- If you swap the JEV model, re-run your eval set (see below).

---

## 🧪 Build the eval set (do this before scaling)

1. Pick 20–30 real support questions that came in over the last month.
2. For each one, manually decide: (a) the question type (`account / policy / how_to / other`), (b) the ideal retrieved chunks, (c) whether the draft reply is grounded, (d) what the grounding score should be.
3. Run Workflow B v2 once per question. Compare the JEV `choice` + `score` to your manual labels.
4. Tune the threshold (`>= 7`) and the `noul` criteria wording until the eval set matches.
5. Re-run after every model swap, prompt change, or Qdrant collection rebuild.

> *The eval set is the contract.* The JEV gates only matter if their verdicts line up with the human labels.

---

## 🧮 Why JEV (decision models) instead of a free-form LLM judge?

| Approach | Pros | Cons |
|---|---|---|
| **Free-form LLM** ("Is this reply grounded? answer yes/no") | Easy to write. | Non-deterministic. Output drift. Models disagree. Hard to gate on. |
| **JEV `noul`** (typed yes/no with criteria + confidence) | Typed output. Deterministic downstream. Comparable across models. Replayable. | You have to write criteria. Some criteria are genuinely ambiguous. |
| **JEV `score`** (typed 0-10 with criteria + confidence) | Numerical, easy to threshold. Catches borderline cases a yes/no misses. | Less interpretable than a `choice`. |
| **JEV `choice`** (typed categorical with criteria + confidence) | Routes by category. First-class gate. | You have to enumerate the categories. |

**Rule of thumb:**

- Use a free-form LLM when the answer is *open-ended* (summarise, draft, explain).
- Use a `noul` decision model when the answer is binary and the cost of being wrong is high (shipping a hallucination).
- Use a `score` decision model when you need a numerical threshold (defence-in-depth).
- Use a `choice` decision model when you need to route by category before doing anything else.

---

## 📖 Related reading

- [Article 02 — I Thought LLMs Could Handle Yes/No Decisions](../../articles/02-i-thought-llms-could-handle-yesno-decisions.md)
- [Project 01 — Document Intelligence Pipeline](../01-document-intelligence-pipeline) — the eval-set discipline was built here first.
- [Project 02 — AI Email Intelligence & Routing (JEV)](../02-ai-email-intelligence-routing-jev) — JEV `choice` + `score` in an email-routing context.
- [Project 03 — AI Purchase Request Approval & Routing System](../03-ai-purchase-request-routing-jev) — all three JEV primitives in one workflow.

---

## 🔐 Sanitization notes

Every workflow JSON in `workflows/` has been scrubbed of:

- credential references (replaced with `YOUR_*_CREDENTIAL` placeholders)
- real Google Drive / Sheets IDs and URLs
- real Slack channel IDs (replaced with `<YOUR_SLACK_CHANNEL_ID>` — `cachedResultName` labels preserved)
- hardcoded email recipients
- cached UI selections, `pinData`, `meta.credentials`, top-level `id`/`versionId`/`tags`
- `active: true` → set to `false` so you activate explicitly after credential setup

See [`../../README.md`](../../README.md) for the full sanitization policy.

---

> *Zero hallucinated answers shipped to users.* The JEV grounding gate is the contract — every reply either clears both gates or escalates to a human with the chunks attached.
