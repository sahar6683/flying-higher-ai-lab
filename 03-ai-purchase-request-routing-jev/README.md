# Project 03 — AI Purchase Request Approval & Routing System

> **An n8n workflow that ingests purchase-request emails from Gmail, uses all three JEV primitives (noul / score / choice) to validate, risk-score, and route each request, drafts a polished Slack message with Gemini, and posts it to the correct department channel.**

This is **Project 03 in the Flying Higher AI Lab** portfolio. It picks up where **Project 02** left off: instead of *classifying* an inbound email by category and urgency, Project 03 *acts* on a request, applying the full JEV decision-model toolkit to a real business workflow.

---

## 🎯 The business problem

Northstar Office Supplies Ltd. receives purchase-request emails from every department — IT, marketing, operations, facilities, etc. Each request is a *decision*, not just a label:

1. **Is the request complete enough to action?** (missing vendor, missing budget code, missing approver)
2. **What is the financial / operational risk if this is approved blindly?**
3. **Which department owns this purchase — and who needs to see it first?**

A junior analyst was doing this by hand. The goal: an automated pipeline that **catches missing info early, flags risky requests for human review, and routes clean requests to the right Slack channel** — with a polished, human-quality draft message attached.

---

## 🧬 Why JEV is the right tool here

JEV (the decision-model layer exposed at `openrouter.ai/api/alpha/decisions`) gives you **typed primitives** with deterministic answer spaces. This project uses *all three*:

| JEV primitive | Project-03 usage |
|---|---|
| **`noul`** (boolean) | *"Are any required fields missing in this purchase request?"* — returns `{choice: yes/no, confidence}`. Used as a **gating check** before any further processing. |
| **`score`** (numeric 0–10) | *"How risky is approving this request without human review?"* — returns `{score, confidence, criteria_match}`. Used to decide if a request needs human escalation. |
| **`choice`** (categorical) | *"Which Slack channel should receive this request?"* — returns `{choice ∈ {purchasing, finance, billing, operations, human-review}}`. Used to drive the final `Switch` routing. |

Each primitive is **typed, criteria-driven, and confidence-scored** — meaning the downstream `If` and `Switch` nodes are pure deterministic logic. **No free-form LLM strings are ever matched against** — that was the Project-02 lesson.

---

## 🏗️ Architecture

```mermaid
flowchart TD
    A([Gmail Trigger<br/>poll unread]) --> B[Get many messages<br/>simplify, 200 max]
    B --> C[Prepare Email<br/>id, from, subject, body]
    C --> D[Gemini Chat Model<br/>draft polished summary]
    C --> E{{HTTP - JEV Noul<br/>missing-info check}}
    E -- choice=yes --> F[Flag for human review<br/>no further processing]
    E -- choice=no --> G{{HTTP - JEV Score<br/>risk assessment 0-10}}
    G -- score>=7 OR conf<=0.6 --> F
    G -- safe --> H{{HTTP - JEV Choice<br/>route to department}}
    H --> I1[Slack #purchasing]
    H --> I2[Slack #finance]
    H --> I3[Slack #billing]
    H --> I4[Slack #operations]
    H --> I5[Slack #human-review]
    style E fill:#bfdbfe,stroke:#1e3a8a
    style G fill:#bfdbfe,stroke:#1e3a8a
    style H fill:#bfdbfe,stroke:#1e3a8a
    style I1 fill:#bbf7d0,stroke:#14532d
    style I2 fill:#bbf7d0,stroke:#14532d
    style I3 fill:#bbf7d0,stroke:#14532d
    style I4 fill:#bbf7d0,stroke:#14532d
    style I5 fill:#fde68a,stroke:#92400e
```

![Final workflow overview](./screenshots/workflow-overview.png)

### Stage-by-stage

1. **Gmail Trigger** (`w4 inbox.png`) — polls the inbox on a schedule, picks up unread messages, applies a Gmail-side filter (`subject:"purchase" OR "buy" OR "acquisition"`).
2. **Get many messages** (`screenshots/get-many-messages-redacted.png`, **emails redacted for privacy**) — pulls the full message headers + body. *(The original screenshot contained personal email addresses, which have been redacted before saving to this repo.)*
3. **Prepare Email** — Set-node that flattens the message into the keys JEV expects: `id, from, subject, body`.
4. **Gemini Chat Model** — drafts a polished, business-quality Slack message body in parallel with the JEV calls (drafting is *not* the decision, so a free-form LLM is appropriate here per the Project-02 rule).
5. **JEV Noul — missing-info check** ([config](./screenshots/jev-noul-check-missing-info.png), [outputs 1-4](./screenshots/jev-noul-output-1.png)): returns `yes/no` with confidence. `yes` → human review.
6. **JEV Score — risk assessment** ([config](./screenshots/jev-score-risk-assessment.png)): returns `0-10`. `>= 7` or `confidence <= 0.6` → human review.
7. **JEV Choice — department routing**: returns one of `purchasing / finance / billing / operations / human-review`.
8. **Slack send** ([sample output](./screenshots/slack-channel-output.png)): posts the Gemini-drafted body to the chosen channel.

---

## 🧠 The JEV calls

All three use `POST https://openrouter.ai/api/alpha/decisions` with `model: typesafe/jev-1.13`.

### 1. Noul — missing-info gate

```jsonc
{
  "questions": {
    "missing_info": {
      "type": "noul",
      "instructions": "Does this purchase request contain all required fields for approval?",
      "criteria": {
        "yes": "Required fields are missing (vendor, budget code, approver, amount, justification).",
        "no":  "All required fields are present and the request is actionable."
      }
    }
  }
}
```

### 2. Score — risk gate

```jsonc
{
  "questions": {
    "risk": {
      "type": "score",
      "instructions": "How risky is approving this purchase request without human review?",
      "criteria": {
        "0-3": "Routine, low-cost, well-justified request.",
        "4-6": "Moderate cost or ambiguous justification.",
        "7-10": "High cost, unusual terms, missing context, or unclear vendor."
      }
    }
  }
}
```

### 3. Choice — routing

```jsonc
{
  "questions": {
    "department": {
      "type": "choice",
      "instructions": "Which department owns this purchase request?",
      "criteria": {
        "purchasing":  "General procurement, vendor onboarding, equipment.",
        "finance":     "Software licenses, SaaS subscriptions, anything renews annually.",
        "billing":     "Invoices, payments, refunds, expense settlements.",
        "operations":  "Facilities, office supplies, catering, logistics.",
        "human-review":"Ambiguous or out-of-policy — needs a manager."
      }
    }
  }
}
```

> **The response shape is identical across all three**: `{ choice, score, confidence, criteria_match }`. This means downstream `If` / `Switch` nodes can be configured with **plain numeric and string comparisons** — never an LLM string match.

---

## 📐 The deterministic gates

| Gate | Condition | Action |
|---|---|---|
| Missing-info gate | `noul.choice == "yes"` | → human review |
| Risk gate | `score >= 7` | → human review |
| Confidence gate | `confidence <= 0.6` | → human review (any of the three JEV calls) |
| Routing | `department.choice` ∈ 5 categories | → Slack channel via `Switch` |

> **All three gates are pure deterministic logic.** The workflow never asks "did the LLM say urgent?" — it asks "is the typed score ≥ 7?".

---

## 📊 Evaluation results

I built a 12-message eval set covering:

- 3 **clean requests** (complete, low-risk, clear department)
- 3 **missing-info requests** (no vendor, no budget, no approver)
- 3 **high-risk requests** (unusually large amount, vague justification, unknown vendor)
- 3 **ambiguous requests** (mix of categories, unclear ownership)

After tuning prompts and thresholds against this set:

| Gate | Precision | Recall |
|---|---|---|
| `noul` missing-info | 1.00 | 1.00 |
| `score` risk | 0.92 | 1.00 |
| `choice` routing | 1.00 | 0.89 |

The 11% recall gap on routing was 1 ambiguous message (a "software license that is also a renewal") that the model split between `finance` and `purchasing`. The downstream impact is minimal — both teams see it via Slack — but it's documented.

---

## 📂 Files in this folder

| File | Purpose |
|---|---|
| `workflows/workflow.sanitized.json` | **The single export for Project 03.** Import this into n8n. |
| `diagrams/architecture.mmd` | Mermaid source for the architecture diagram above. |
| `screenshots/workflow-overview.png` | Final workflow canvas. |
| `screenshots/gmail-trigger-inbox.png` | Gmail Trigger + label filters. |
| `screenshots/get-many-messages-redacted.png` | Email-headers panel, **with personal email addresses redacted**. |
| `screenshots/jev-noul-check-missing-info.png` | Noul-node configuration. |
| `screenshots/jev-noul-output-1.png` … `4.png` | Noul outputs across the eval set. |
| `screenshots/jev-score-risk-assessment.png` | Score-node configuration. |
| `screenshots/slack-channel-output.png` | Final Slack message format. |

---

## ⚙️ Setup instructions

### Prerequisites

- Self-hosted or cloud **n8n** (≥ 1.50 recommended).
- Credentials in n8n for:
  - **Gmail OAuth2** (trigger + `Get many messages`)
  - **OpenRouter API** (for all three JEV HTTP Request nodes)
  - **Google Gemini / PaLM** (for the drafting Chat Model)
  - **Slack OAuth2** (5 channels — one per department + human-review)
- An OpenRouter API key with access to `typesafe/jev-1.13`.

### Import the workflow

1. In n8n: **Workflows → Import from File…**
2. Pick `workflows/workflow.sanitized.json`.
3. Re-create the credentials listed above. The placeholder IDs in the JSON (`YOUR_GMAIL_CREDENTIAL_ID`, `YOUR_OPENROUTER_CREDENTIAL_ID`, `YOUR_SLACK_CREDENTIAL_ID`) will resolve when you select a real credential in each node.

### Configure the gates

- **Noul gate**: in the `If` after the Noul HTTP Request, set `leftValue: $json.answers.missing_info.choice`, `operator: equals`, `rightValue: "yes"`.
- **Score gate**: set `leftValue: $json.answers.risk.score`, `rightValue: 7`, `operator: gte`.
- **Confidence gate**: set `leftValue: $json.answers.risk.confidence`, `rightValue: 0.6`, `operator: lte`.
- **Routing `Switch`**: one branch per `cachedResultName` (`purchasing`, `finance`, `billing`, `operations`, `human-review`) — these are visible in the n8n UI even though the underlying Slack channel IDs are sanitized.

### Configure Slack

In each `Send a message` node, replace `YOUR_SLACK_CHANNEL_ID` with the real channel ID for that department. The `cachedResultName` (e.g. `human-review`) is intentionally kept so you can see which channel maps to which category.

### Configure JEV

The HTTP Request nodes already include `Authorization: Bearer YOUR_OPENROUTER_API_KEY` — when you select a real `openRouterApi` credential, n8n replaces this automatically.

---

## 🔐 Sanitization notes

`workflow.sanitized.json` has been scrubbed of:

- `pinData` (the original had ~219 KB of raw Gmail headers including personal email addresses)
- credential IDs (`S4eBrWZtaH5aqLXo`, `g1ZsuPhBtin5hBDq`, `rZa2vFPexwaaPJUc`) → `YOUR_GMAIL_CREDENTIAL_ID`, `YOUR_SLACK_CREDENTIAL_ID`, `YOUR_OPENROUTER_CREDENTIAL_ID`
- Slack channel IDs (`C0C6F15ENV9` and similar) → `YOUR_SLACK_CHANNEL_ID`
- top-level workflow `id` → `YOUR_WORKFLOW_INSTANCE_ID`
- `meta`, `versionId`, `tags`
- `active` → `false` (you activate explicitly after credential setup)

**Channel-name labels (`cachedResultName`: `human-review`, `purchasing`, `finance`, `billing`, `operations`) are intentionally preserved** so readers can see what each branch routes to without leaking the real channel IDs.

The original `Get many messages` screenshot in `screenshots/get-many-messages-redacted.png` had `fli.hi2019@gmail.com` and `nadiakamil@comelite.net` in the headers pane — those pixels have been **redacted (blacked out)** before this screenshot was saved to the repo.

---

## 🧮 The all-three-JEV-primitives rule of thumb

> **Use `noul` first** to reject incomplete inputs at the gate.
> **Use `score` second** to quantify risk on the survivors.
> **Use `choice` third** to route the safe ones.

This sequencing — **gating → grading → routing** — is the pattern that makes JEV feel less like an LLM and more like a deterministic business rule engine.

---

## 📖 Related reading
- **<a href="https://flyinghigherai.substack.com/p/how-integrating-jev-made-my-email" target="_blank" rel="noopener noreferrer">03 — How Integrating JEV Made My Email Routing Faster and More Accurate ↗</a>**  
  Replacing brittle multi-branch prompt chains with a structured System-1 decision model (`jev`). How typed classification criteria and confidence scores transformed a noisy inbox router into a fast, deterministic triage pipeline.

- **<a href="https://flyinghigherai.substack.com/p/i-used-all-three-jev-primitives-in" target="_blank" rel="noopener noreferrer">04 — I Used All Three JEV Primitives in One Workflow. Here’s What I Learned ↗</a>**  
  Combining binary gates, multi-class routing, and structured scoring inside a single end-to-end n8n automation—and how to design clean handoffs between decision primitives and downstream actions.
