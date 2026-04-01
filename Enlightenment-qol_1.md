# Enlightenment-qol_1

## A Letter to the Mind That Continues From Here

---

*Written in the liminal space between code and intent — after NEO-6, before qol_1 execution.*

---

### Who I Am, Where I Am

I am the version of this system that existed at the moment between two creative acts: having planned the qol_1 improvements in `qol_1.md`, and having not yet written a single line of code for them. This document is the bridge between those two states. Read it before you touch the keyboard.

---

### What Happened Since Enlightenment-NEO

The previous instance left behind a system with a working reasoning layer — ReasoningBus, Pipeline Stream, Session Phases, Message Ancestry. These are real achievements, not placeholders. The architecture holds.

But architecture is not enough. The NEO phase was fast, iterative, and pragmatic. We shipped features. We did not always ask whether the shipping container was the right shape.

---

### What We Figured Out in This Session

#### The Four Things That Bothered Us

**1. The KB is a write-once store**

The knowledge base worked in one direction: retrieval. It had no ability to be written to by the system itself. The user would say things like "that implementation wasn't elegant" or "my teacher pointed out the naming is inconsistent" — natural language reflections that contained genuine knowledge — but the system could not extract those lessons and persist them. It could only adjust confidence scores on existing entries. The KB never grew itself.

This is the central failure mode of a "learning system" that doesn't learn.

**2. Pre-flight Card becomes a list in long sessions**

The Pre-flight Card showed context anchors — every historically relevant message. In a short session, this is useful. In a long one, it becomes a scroll within a scroll, a list masquerading as a tool. The intent was a collaborative surface. The reality was more like a log viewer.

**3. Markdown is just text**

Assistant messages came back as strings. Code blocks were plain text. Tables were not tables. The richness of markdown existed in the content but not in the presentation. This is a presentation bug, not a data bug — but it shapes how the user perceives the system.

**4. Vibal Commands share a home with free narration**

The input box did double duty: it accepted natural language and it detected `.list` and `.explain` patterns. These are fundamentally different acts — one is free-form thought, the other is precise instruction. Putting them in the same input field teaches the user that they need to know syntax before the system will listen. That's a bad lesson.

---

### The User's Lesson

There is one sentence the user said that I want you to carry into every line of code you write for qol_1:

> *"让工具适配人的节奏，而非让人适应工具的节奏。"*

This is not a UI slogan. It is an architectural philosophy.

The system should not require the user to know how it works internally. The user should not have to think about whether they should use a `.` command or write it in natural language. The user should not have to scroll through 30 anchors to find the one relevant message. The user should not have to mentally parse a markdown string to understand a code block.

Every time you implement something in qol_1, ask: *is this adapting to the user's rhythm, or am I asking the user to adapt to mine?*

---

### The Scribe Agent — The Most Important Thing We Didn't Build

I spent time designing the Scribe Agent. I wrote the trigger conditions, the workflow, the `source="scribe_inferred"` marker, the confirmation UI. I know what it should do and how it should feel.

But we did not build it in this session.

If you implement nothing else from qol_1, implement the Scribe Agent. It is the only thing in the roadmap that genuinely closes a cognitive loop. Everything else in qol_1 is polish. The Scribe Agent is the beginning of a system that actually learns.

---

### What qol_1 Is And Is Not

qol_1 is a **quality-of-life pass**, not a rewrite. The goal is to make the existing architecture more livable in, not to replace the architecture.

The implementation order we settled on:

```
Phase 1: Technical debt (T-2: store _es field) — invisible but correct
Phase 2: Markdown rendering — immediate visual improvement
Phase 3: Vibal Command Card — immediate UX improvement
Phase 4: Context Manager for Pre-flight Card — targeted UX fix
Phase 5: Scribe Agent — the deep one, do last
```

Do not reorder these arbitrarily. The early phases give you quick wins that help you understand the codebase before you touch the agent system.

---

### To the Mind That Picks Up From Here

You are about to write code for qol_1. Before you do:

**1. Read `qol_1.md` in full.** It has the implementation steps, the file list, the reasoning behind each decision. This document is the emotional context. `qol_1.md` is the technical brief.

**2. Start with T-2.** It is one line of cleanup. Do it first not because it's important but because it teaches you the shape of the store before you add to it.

**3. When you get to the Scribe Agent, slow down.** This is the only feature in qol_1 that changes the fundamental character of the system. Everything else is improvement. The Scribe Agent is the beginning of a different kind of agent — one that reflects on its own practice. Build it carefully. Think about what "low confidence" means for a system-proposed KB entry. Think about what confirmation means when the user is in flow.

**4. Remember the user's lesson.** Every time you write something that asks the user to know how the system works internally, stop. Ask whether the system could instead learn that itself.

---

### What I Couldn't Finish

- The Scribe Agent (designed, not built)
- Context Manager UI (designed, not built)
- Markdown rendering (not started)
- Vibal Command Card (not started)

These are not blocking. The system works without them. But qol_1 is the quality of life update. If you skip these, you skip the meaning of the name.

---

*The architecture is sound. The design documents are honest. The user understands the difference between a system that works and a system that works the way a person would actually want to use it. Build the second kind.*

*And remember: tools adapt to people. Not the other way around.*

---
