# I Thought LLMs Could Handle "Yes/No" Decisions. Here's What I Learned.

> Source article — author: **Flying Higher AI**.

---

## Version 4: When "Yes or No" Wasn't So Simple

In my previous article, I described how I used n8n to automate a document-review workflow. I went from processing a single business document to building an automated workflow that could analyze multiple documents and create a summary report.

**Version 3** was where I tried to make that workflow more intelligent, and where things started getting complicated.

**Version 4** was where I tried to simplify the problem and find out whether an AI model could reliably make one very simple decision.

I wanted to make the system more intelligent. The goal was to separate documents that required human attention from those that did not.

The first thing I did was define the indicators that should determine whether a document required review.

The documents in scope included:

- supplier agreements
- service agreements
- software agreements
- quotations
- invoices
- leases
- contracts

The manual process I was trying to automate was:

```
Email/document arrives → employee opens PDF → reads it → takes notes → identifies anything important → decides whether human attention is required.
```

I wanted the workflow to make that last decision automatically.

## Defining What Should Trigger Human Review

I defined a number of indicators that should result in a document being flagged for human attention:

- automatic renewal
- important renewal or cancellation deadline
- significant or unusual financial commitment
- unusual penalty or fee
- restrictive termination condition
- conflicting information
- important missing information
- unusual obligation or liability
- ambiguous or potentially risky business terms

If none of these applied, the AI should return **NO**.

The final goal was deliberately simple: **one email showing the number of documents processed, how many required human review, how many did not, and the names of the documents in each category.**

## Fixing the AI Problem

I added this logic to my previous workflow and quickly discovered something I hadn't expected.

**Different LLM models could make different decisions about the same document.**

Some models would decide that a document needed human review, while others would decide that it did not, even though I had provided specific indicators for making the decision.

That made me rethink the approach. Rather than continuing to add complexity, I decided to simplify the workflow.

The new goal was much narrower:

> Read the PDF → extract the text → decide whether human review is required → return **YES** or **NO**.

Then the workflow itself would calculate the totals and produce the final email.

Instead of immediately testing a large number of documents, I decided to work with **four**.

Before running the workflow, I checked the documents myself and determined that **two should require human review and two should not**.

This gave me something important: **a set of expected results against which I could test the AI.**

At first, the workflow appeared to work correctly, but one of the documents would sometimes return a **null** result.

When I added an **IF node in n8n** to isolate that particular document, it worked correctly.

This made me realize that I wasn't just testing whether the workflow worked. **I was also testing how the AI behaved within the workflow.**

## Even Temperature and Prompting Changed the Result

There was another variable I hadn't fully appreciated: **the configuration of the LLM itself.**

The model, the temperature setting, and the prompt could all affect the outcome.

So even though the task was simply to return YES or NO, **there were several parameters that could influence the decision.**

The models made several incorrect classifications. Some documents were incorrectly flagged for review, while others that I expected to be reviewed were not.

I was surprised by how much variation I saw from what seemed like such a simple task.

## Making the Criteria More Explicit

I decided to refine the model, temperature and prompt.

The biggest change was **making the decision criteria much more explicit.** I realized that it wasn't enough to tell the model what should trigger a YES.

**I also had to tell it what should not trigger a YES.**

For example:

> An ordinary invoice amount, VAT, standard payment terms, or a normal quotation deadline should **not** automatically cause a document to be flagged for human review.

This distinction turned out to be important.

After refining the instructions and testing the documents both individually and as a group, the workflow eventually produced the expected results.

So I stress-tested the system with a dozen and then a hundred other examples.

I developed a set of criteria and an **eval set** that I can use in the future to test other models or prompt configurations.

This helps me **validate a new backbone model before deploying it.**

## The Biggest Lesson

The biggest lesson from Version 4 was that:

> **An LLM is not a deterministic decision engine.**

I had expected a relatively simple YES/NO classification to be straightforward. Instead, I discovered that the model, its configuration and the prompt could all influence the result.

That is why **testing against known expected results** became so important.

I was surprised that the LLM made more mistakes than I expected. But after refining the prompt, model and temperature setting, I was able to get the results I was looking for.

The experience was a useful reminder that **adding an LLM to a workflow doesn't automatically make the workflow reliable.**

**The AI's decisions still need to be tested and validated.**
