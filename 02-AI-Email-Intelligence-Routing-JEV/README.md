# Project 02 — AI Email Intelligence & Routing (Jev)

> **An n8n workflow that classifies inbound Gmail messages with the Jev decision model, gates on confidence + urgency, routes to Slack channels, and escalates low-confidence / high-urgency items to a human reviewer.**

This is the **v1 → v2 evolution of an email triage system**. The big idea: stop asking a generic LLM "is this important?" and instead ask a typed decision model a question that has a defined answer space, criteria, and a confidence score.

---

## 🎯 The business problem

Northstar Office Supplies Ltd. receives a constant stream of inbound email — sales inquiries, support questions, complaints, supplier communications, billing issues, etc. Manually triaging each one is slow and inconsistent.

Goal: an automated classifier that:

1. Reads an incoming Gmail message.
2. Decides **what kind** of email it is.
3. Decides **how urgently** Northstar needs to respond.
4. Routes the email to the right team's Slack channel.
5. Escalates to a human reviewer when the AI isn't sure enough.

---

## 🧬 Why LLMs struggle with deterministic Yes/No / threshold decisions

The full case study is in [Article 02](../../articles/02-i-thought-llms-could-handle-yesno-decisions.md). The condensed version:

- An LLM is **probabilistic**, not deterministic.
- A prompt that says "answer yes or no" is *not* a contract — the model can decide to hedge, add commentary, return the wrong token, or flip the answer when the temperature is bumped.
- "Use temperature 0" helps but is not a guarantee across all backbones.
- Different models give different answers on the same input.

### What I changed

Instead of asking the LLM "is this urgent? answer yes/no", I now ask a **decision model** (Jev via OpenRouter) a typed question:

```jsonc
{
  "urgency": {
    "type": "score",
    "instructions": "Assess how urgently Northstar Office Supplies Ltd. needs to respond…",
    "criteria": { "routine": "…", "important": "…", "urgent": "…" }
  }
}
```

Jev returns a structured `{ score, confidence, choice }` object. **The workflow then gates on deterministic thresholds** (`score >= 6` → urgent; `confidence <= 0.6` → uncertain). The decision is *never* an LLM string match.

---

## 🏗️ Architecture

### v2 — final shipped version

```mermaid
flowchart TD
    A([Gmail Trigger<br/>unread, everyWeek, maxResults=5]) --> B[Prepare Email<br/>Set: id, sender, recipient, subject, body]
    B --> C{{Jev — Classify Email<br/>OpenRouter HTTP<br/>model=typesafe/jev-1.13<br/>question: urgency score}}
    C -- score >= 6 --> D[Prepare Human Review Output<br/>reason: Email Urgency Score above 6]
    C -- score < 6 --> E{{Jev — Classify Email #2<br/>question: category choice}}
    E --> F[Merge1]
    F --> G{{Switch — Route by Classification<br/>category ∈ sales_inquiry / supplier_communication / billing / customer_complaint / customer_support / general / operations}}
    G --> H1[Slack #sales]
    G --> H2[Slack #purchasing]
    G --> H3[Slack #billing]
    G --> H4[Slack #customer-experience]
    G --> H5[Slack #operations]
    D --> I[Append row in sheet<br/>Google Sheets log]
    D --> J[Gmail — Notify reviewer]
    C -- confidence <= 0.6 --> K[Prepare Human Review Output2<br/>reason: Confidence under 60%]
    K --> L[Append row in sheet1]
    K --> M[Gmail — Notify reviewer]
    style C fill:#bfdbfe,stroke:#1e3a8a
    style E fill:#bfdbfe,stroke:#1e3a8a
    style G fill:#fde68a,stroke:#92400e
    style I fill:#bbf7d0,stroke:#14532d
```

![v2 workflow screenshot — final shipped architecture with urgency gate + Switch routing](./assets/workflow-v2.png)

### v1 → v2 — what changed

| Area | v1 | v2 |
|---|---|---|
| **LLM model** | Jev via OpenRouter | Jev via OpenRouter |
| **First decision** | Category (`choice`) | Urgency (`score`) — earlier, broader gate |
| **Confidence gate** | Hard IF on `confidence <= 0.85` | Hard IF on `confidence <= 0.6` (more lenient) |
| **Urgency gate** | None | New IF: `score >= 6` → escalate |
| **Routing** | None — everything was either human-reviewed or sent onward | New `Switch` node routes by category to per-team Slack channels |
| **Human channels** | Gmail + Google Sheets | Gmail + Google Sheets (×2 for urgency vs low-confidence paths) |
| **Merge logic** | n/a | `Merge1` joins the second Jev call (category) with the urgency path before routing |

### v1 architecture (for reference)

```mermaid
flowchart LR
    A([Gmail Trigger]) --> B[Prepare Email]
    B --> C[Jev — Classify Email<br/>category]
    C --> D{{If — Confidence Check<br/>confidence <= 0.85}}
    D -- yes --> E[Prepare Human Review Output]
    E --> F[Google Sheets: append row]
    E --> G[Gmail: notify reviewer]
    D -- no --> H[Jev — Assess Priority<br/>priority]
    H --> I[Gmail: classify & forward]
```

![v1 workflow screenshot — original architecture (category choice + confidence gate)](./assets/workflow-v1.png)

---

## 🧠 The Jev calls

Both v1 and v2 use the OpenRouter **alpha/decisions** endpoint:

```
POST https://openrouter.ai/api/alpha/decisions
Authorization: Bearer YOUR_OPENROUTER_API_KEY
Content-Type: application/json
```

### v1 — `category` (choice)

```json
{
  "model": "typesafe/jev-1.13",
  "state": {
    "subject": "...",
    "sender":  "...",
    "body":    "..."
  },
  "questions": {
    "category": {
      "type": "choice",
      "instructions": "What category best describes this incoming business email?",
      "criteria": {
        "customer_support":      "The customer is asking for help…",
        "sales_inquiry":         "The sender is asking about buying…",
        "customer_complaint":    "The sender is expressing dissatisfaction…",
        "billing":               "The email is about invoices, payments, refunds…",
        "supplier_communication":"The email is from a vendor / supplier…",
        "general":               "Anything that doesn't fit the above."
      }
    }
  }
}
```

### v1 — `priority` (choice) — secondary gate

```json
{
  "questions": {
    "priority": {
      "type": "choice",
      "instructions": "How urgent is this incoming business email?",
      "criteria": {
        "routine":   "Normal business request, no prompt attention needed.",
        "important": "Meaningful attention required, but not time-critical.",
        "urgent":    "Significant business consequence if delayed."
      }
    }
  }
}
```

### v2 — `urgency` (score) — primary gate

```json
{
  "questions": {
    "urgency": {
      "type": "score",
      "instructions": "Assess how urgently Northstar Office Supplies Ltd. needs to respond. Use only information explicitly contained in the email. Do not infer deadlines, consequences, or urgency that are not supported by the email. A stated date-based deadline does not automatically make an email urgent; a normal business deadline should remain routine. However, explicit business consequences such as payment being withheld, a significant financial dispute, a customer refusing payment, an important business activity being blocked, or a serious complaint should raise urgency.",
      "criteria": {
        "routine":   "Normal business communication; can be handled in standard workflow.",
        "important": "Requires meaningful attention but is not time-critical.",
        "urgent":    "Significant consequence if delayed (payment, dispute, blocked activity)."
      }
    }
  }
}
```

The response shape is always:

```json
{
  "answers": {
    "urgency": {
      "choice":     "urgent",
      "score":      7.5,
      "confidence": 0.82
    }
  }
}
```

The workflow then uses pure `If` and `Switch` nodes — no LLM in the decision path.

---

## 📐 The deterministic gates

### Urgency gate

```js
leftValue: $json.answers.urgency.score
rightValue: 6
operator:   gte
```

Anything scoring **6 or above** is escalated to a human reviewer (Gmail + Google Sheets log).

### Low-confidence gate

```js
leftValue: $json.answers.urgency.confidence
rightValue: 0.6
operator:   lte
```

Anything at or below **60% confidence** is escalated to a human reviewer, regardless of the urgency score.

### Routing switch

```js
leftValue: $json.answers.category.choice
operator:   equals
sales_inquiry         → Slack #sales
supplier_communication → Slack #purchasing
billing                → Slack #billing
customer_complaint     → Slack #customer-experience
customer_support       → Slack #customer-experience
operations             → Slack #operations
general                → Slack #operations  (fallback)
```

> **Why use `Switch` and not nested `If` nodes?** Readability. Each route is one line in the workflow graph.

---

## 📂 Files in this folder

| File | Purpose |
|---|---|
| `workflows/AIEmailIntelligenceRouting.v1.sanitized.json` | v1 export — category-first Jev decision + 85% confidence gate + Gmail/Sheets escalation. |
| `workflows/AIEmailIntelligenceRouting.v2.sanitized.json` | v2 export — urgency-score-first Jev decision + dual gate (urgency ≥ 6 OR confidence ≤ 60%) + Slack routing via `Switch`. **Recommended import.** |
| `diagrams/architecture-v2.mmd` | Mermaid source for the v2 architecture diagram. |
| `diagrams/routing-overview.mmd` | Mermaid source for the v1 → v2 comparison diagram. |

---

## ⚙️ Setup instructions

### Prerequisites

- A self-hosted or cloud n8n instance (≥ 1.50 recommended).
- Credentials in n8n for:
  - **Gmail OAuth2** (trigger + send + read)
  - **OpenRouter API** (`openRouterApi` credential type, used by the HTTP Request nodes)
  - **Google Sheets OAuth2** (append row)
  - **Slack OAuth2** (`slackOAuth2Api`)
- One Google Sheet created with the columns:
  `Status, Reason, Score, Confidence, Sender, Subject, Message ID`

### Import the workflow

1. In n8n: **Workflows → Import from File…**
2. Pick `AIEmailIntelligenceRouting.v2.sanitized.json`.
3. Re-create the credentials. The placeholder IDs (`YOUR_GMAIL_OAUTH2_CREDENTIAL`, `YOUR_OPENROUTER_API_CREDENTIAL`, `YOUR_GOOGLE_SHEETS_OAUTH2_CREDENTIAL`, `YOUR_SLACK_OAUTH2_CREDENTIAL`) will resolve when you select a real credential in each node.

### Configure Gmail

- In **Gmail Trigger**, set `pollTimes` (e.g. every 5 minutes), `maxResults` and any filters (e.g. `readStatus: unread`).
- In **Prepare Email**, adjust the field mapping if your Gmail payload uses different keys.
- In the two **Gmail (notify reviewer)** nodes, replace `<YOUR_TARGET_INBOX@example.com>` with the address of whoever should receive human-review notifications.

### Configure Google Sheets

- In both **Append row in sheet** nodes, replace `<YOUR_GOOGLE_SHEETS_ID>` with your sheet's document ID (between `/d/` and `/edit` in the URL).
- Make sure the sheet has the right columns. n8n's mapping is defined in `columns.mappingMode: "defineBelow"`.

### Configure Slack

- In each **Slack (Send a message)** node, replace `<YOUR_SLACK_CHANNEL_ID>` with the real channel ID for sales / purchasing / billing / customer-experience / operations.

### Configure Jev

- The HTTP Request nodes already include `Authorization: Bearer YOUR_OPENROUTER_API_KEY` — when you select a real `openRouterApi` credential, n8n will replace this header automatically.
- The model is `typesafe/jev-1.13`. If you swap it, re-run your eval set.

---

## 🧪 Build the eval set (do this before scaling)

1. Pick 20–30 real inbound emails.
2. Manually classify each one (category + urgency + whether you'd escalate).
3. Set the Gmail Trigger to read only from a test mailbox or label.
4. Run the workflow once per email. Compare to your manual classification.
5. Tune the thresholds (`6`, `0.6`) and the prompt instructions until the eval set matches.

> *Confidence is a feature, not a bug.* Treat it as a first-class signal — and escalate when it's low.

---

## 🧮 Why Jev (decision models) instead of a free-form LLM?

| Approach | Pros | Cons |
|---|---|---|
| **Free-form LLM** ("Is this urgent? answer yes/no") | Easy to write. | Non-deterministic. Output drift. Models disagree. Hard to gate on. |
| **Jev decision model** (`type: choice / score`, with `criteria` and `confidence`) | Typed output (`{choice, score, confidence}`). Deterministic downstream. Comparable across models. Replayable. | You have to write criteria. Some criteria are genuinely ambiguous. |

**Rule of thumb:**

- Use a free-form LLM when the answer is *open-ended* (summarise, draft, explain).
- Use a decision model when the answer is *bounded* (categorise, score, prioritise, route).
- Always gate on **confidence** when the cost of a wrong answer is high.

---

## 📖 Related reading

- **<a href="https://flyinghigherai.substack.com/p/i-thought-llms-could-handle-yesno" target="_blank" rel="noopener noreferrer">02 — I Thought LLMs Could Handle "Yes/No" Decisions. Here's What I Learned ↗</a>**  
  A live case study of building a YES/NO review classifier for incoming business documents. Explores how temperature, prompt phrasing, and model choice change the result, why raw LLMs drift on binary classification, and why an evaluation set is non-negotiable.
- [Project 01 — Document Intelligence Pipeline](../01-Document-Intelligence-Pipeline) — the eval-set discipline was built here first.

---

## 🔐 Sanitization notes

Every workflow JSON in `workflows/` has been scrubbed of:

- credential references (replaced with `YOUR_*_CREDENTIAL` placeholders)
- real Google Sheets document ID & URL
- real Slack channel IDs (replaced with `<YOUR_SLACK_CHANNEL_ID>`)
- hardcoded Gmail recipient
- cached UI selections, `pinData`, `meta.credentials`, top-level `id`/`versionId`/`tags`
- `active: true` → set to `false` so you activate explicitly after credential setup

See [`../../README.md`](../../README.md) for the full sanitization policy.
