# I Thought AI Could Build the Automation for Me. Then I Had to Learn How to Think Like an Engineer

> Source article — author: **Flying Higher AI**.

---

## I Started with a Business Problem, not a Technology

I wanted to build a small business automation project to see whether I could take a pile of incoming business documents and turn them into something useful for management, without someone having to manually open every PDF, read it, take notes, and decide what needs attention.

But there was another question that I wanted to answer:

> With all the advances in AI, could someone without a traditional technical background actually build something like this?

I decided to find out.

I created a fictional company called **Northstar Office Supplies Ltd.**, a small-to-medium B2B company supplying office equipment, furniture, technology and workplace services to other businesses.

Its document process was completely manual:

```
Document arrives → employee opens it → reads it → takes notes → copies information somewhere → decides what needs attention.
```

I wanted to turn that into:

```
Document arrives → text is extracted → AI reviews it → potential issues are identified → management receives a simple summary.
```

That became my first AI automation project.

## From Manual Documents to an Automated Workflow

I started looking at which tools could be used to build something like this and decided to use **n8n**.

> n8n is a no-code/low-code workflow automation platform that connects different applications and services and allows you to build processes using individual nodes.

You can use nodes for things such as triggers, data processing, APIs and connectors, AI models, conditional logic, loops, merging and aggregating information, and sending emails and other outputs.

The interesting part for me wasn't simply automating a task.

It was the possibility of taking a business process and turning it into a system.

Instead of having humans manually move information from one place to another, the system could handle repetitive work and leave the human with the decisions that actually require judgment.

That was the idea.

Now I had to see whether I could actually build it.

## Version 1: Can I Get One Document Through the System?

The first version of my Document Intelligence workflow was deliberately simple. It would:

1. Retrieve one document from Google Drive.
2. Convert the PDF into text.
3. Send the text to an LLM — initially Gemini.
4. Ask the AI to extract specific information.
5. Turn the result into a structured business brief.
6. Send the result by email.

The workflow was basic, but it proved something important: **I could get a document from storage, process it, have AI analyze it, and produce something useful for a human.**

That gave me enough confidence to try something more ambitious.

## Version 2: What Happens When There Are Multiple Documents?

The next step was to scale beyond processing one document at a time.

I changed the workflow so it could retrieve multiple PDFs, extract the text from each one, analyze them individually, and then combine the results into one management summary.

The final email could tell management:

- how many documents had been processed
- what types of documents they were
- what the documents were generally about
- which documents needed human attention

Instead of receiving five separate AI analyses, the result was one clear management summary.

At this point, the project still felt relatively straightforward.

> And I started thinking: *Maybe a non-technical person really can build this with the help of AI.*

Then I increased the complexity.

That was when things got interesting.

## Then Things Started to Break

My next version was designed to process more documents and make a more specific decision about each one.

I wanted the AI to look for indicators such as:

- automatic renewals
- important cancellation deadlines
- significant financial commitments
- unusual penalties
- restrictive termination conditions
- unusual obligations
- potentially risky or ambiguous terms

The AI would then decide whether a particular document required human review.

This sounded simple. **It wasn't.**

As the workflow became more complicated, I started running into problems.

Gemini's API repeatedly reached its quota. I experimented with other models and providers, including **OpenRouter, Claude and DeepSeek**. Then I encountered rate limits, output-format problems and model compatibility issues.

Changing one part of the workflow could cause another part to fail.

And at one point, the workflow started **repeatedly running the initial analysis** when I didn't intend it to.

This was probably the most valuable part of the entire experiment.

Because at that point, I realized something.

> **I had been building the workflow, but I wasn't always understanding the workflow.**

## The Moment I Stopped Blindly Following AI

Up to this point, GPT had been guiding me through much of the process.

I would describe what I wanted, it would suggest the next node or configuration, and I would implement it.

When things worked, that was great.

But when the workflow became more complicated, I started encountering situations where blindly following instructions wasn't enough.

So I changed my approach.

Instead of asking:

> *"What should I do next?"*

I started asking:

> *"What is actually happening here?"*

I began looking at the data moving between nodes. I started questioning why a particular node was needed. I checked documentation, watched videos, searched support forums and investigated the errors myself.

Most importantly, I started telling GPT **what I wanted the system to do**, rather than simply asking it to design the system for me.

That was a turning point.

GPT was still extremely useful. But I was no longer treating it as the architect whose instructions I simply had to follow.

**I was using it as a tool to help me implement and troubleshoot my design.**

## What I Actually Learned

### 1. n8n is powerful, but the workflow is the product

I learned how to navigate n8n, what different types of nodes do, and how they can be connected.

I learned about triggers, data-processing nodes, AI nodes, logic nodes, merging and aggregation, and output nodes.

But the bigger lesson was that knowing individual nodes isn't enough.

As the workflow gets bigger, the design of the workflow becomes more important than any individual node.

> A workflow can contain perfectly good nodes and still be badly designed.

### 2. AI is only one component of the system

At the beginning, I was thinking heavily about the AI model.

Which model should I use? How good is Gemini? Would another model be better?

But I learned that the AI model is only one component of the overall system.

The rest of the workflow still needs to: get the right information, pass the information correctly, make logical decisions, handle errors, control how many times the AI is called, deal with limits, produce a useful final output.

> A great AI model inside a poorly designed workflow doesn't create a great automation.

### 3. Quotas, tokens and rate limits are part of the architecture

One of my biggest lessons was that choosing an AI model isn't simply about asking which model is "best."

You also need to think about:

- how many requests you will make
- how much information you are sending
- how much output you need
- token limits
- rate limits
- provider quotas
- whether the model supports the output format you need
- what happens when the service becomes unavailable

> A free model does not necessarily mean unlimited use. And a model that works perfectly for one task may not be suitable for another. These aren't minor technical details. They affect how you design the entire workflow.

### 4. The more complex the automation, the more you need to understand what you're building

When I started the project, I thought technical knowledge was almost unnecessary.

**I don't think that anymore.**

AI has dramatically lowered the barrier to building things. I was able to create a workflow that I probably would not have been able to build from scratch before starting this project.

But that doesn't mean technical understanding is unnecessary.

In fact, I found the opposite. The more I understood, the more useful AI became.

Once I understood what the workflow was trying to do, I could ask much better questions, identify when something didn't make sense, and correct mistakes instead of blindly implementing them.

That may be one of the biggest lessons I've taken from this project.

## What Happens When the Workflow Breaks?

This is where I think the distinction between using AI and building with AI becomes important.

If you're using AI as an assistant, you can often give it a problem and ask for an answer. But when you're building a system, **you have to understand what the system is doing.**

When a workflow breaks, the answer shouldn't always be:

> *Take a screenshot → send it to GPT → follow whatever it says.*

Instead, we need to be able to ask:

- What was supposed to happen?
- What actually happened?
- Which node failed?
- What data entered that node?
- What data came out?
- How many times was this node executed?
- Did the AI produce the expected format?
- Did an API limit or quota cause the failure?
- Is the problem with the AI, the data, or the workflow logic?

AI can help diagnose these questions. **But the decisions should still be yours.**

## When Should You Use n8n?

I think it is important to diagnose the business problem before deciding on the technology.

n8n can be a useful option when:

- several business systems need to communicate
- information needs to move automatically between applications
- there are repetitive processes
- APIs or connectors are available
- there is clear business logic
- AI can add useful classification, extraction, summarization or decision support
- a human still needs to review important decisions

But automation isn't automatically better just because it is possible.

> If a process takes two minutes to complete manually and only happens once a month, building a complicated automation may not make sense.

The same applies if the process is extremely simple, happens very infrequently, or doesn't involve enough volume to justify the effort.

And if sensitive information is involved, you also need to understand where the data is going, which providers are processing it, and what their data policies are.

**The technology should serve the business problem, not the other way around.**

## What I Would Do Before Building an Automation

If I were starting another automation project today, I would spend more time on the planning before opening the automation platform.

1. **First, define the problem.** What are you actually trying to improve?
2. **Then define the minimum useful version.** Don't start by trying to automate everything.
3. **Map the process:** Where does the information start? Where does it go? What decisions need to be made? What should happen at the end?
4. **Then think about failure.** What happens if:
   - the AI fails?
   - an API is unavailable?
   - a quota is reached?
   - the wrong information is extracted?
   - the AI makes the wrong classification?
   - a document cannot be read?
   - a workflow executes more times than expected?

These questions are not things to think about only after the system breaks. **They should be part of the design.**

## Test Before You Scale

One of my biggest mistakes was increasing the number of documents before I had completely understood how the workflow behaved.

> If one document requires one AI call, then 15 documents may require 15 calls. But if the workflow accidentally runs the AI several times for each document, the number of calls can increase dramatically. That can quickly turn a small test into a quota problem.

So the lesson is simple:

> *Test with one document. Then two. Then five. Only scale once you understand exactly how many times each part of the workflow is executing.*

Beyond n8n, this is a broader lesson for automation work in general.

## Continuing With n8n

I'm going to continue building with n8n using the fictional Northstar Office Supplies company.

There are still many things I want to explore, from document review to client-facing interfaces and other business processes.

But I think my perspective has changed.

When I started, I was asking:

> *"Can AI help me build an automation?"*

Now I'm asking a different question:

> *"What business problem can I turn into a reliable system, and where can AI add value?"*

That is a much more useful question.

I don't see automation as a way to eliminate people. I see it as a way to remove some of the repetitive work that consumes people's time and attention.

Instead of replacing human judgment, the goal is to give humans better information, at the right time, so they can spend more of their energy on work that actually requires them.

**AI helped me build something I couldn't easily have built before.**

But learning enough to question the AI, understand the workflow, and make my own decisions is what made the project useful.

And that, perhaps, was the biggest lesson of all.
