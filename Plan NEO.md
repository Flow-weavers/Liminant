# Plan NEO

## Liminal — The Liminal Engineering Platform

*"Between the idea and the reality, between the motion and the act, falls the Constraint."*
*— adapted from T.S. Eliot, for an architecture that knows the difference*

---

## Preamble: Why "NEO"

Plan omni.md established the bones — a working agentic loop, SubAgents, a constraint pipeline, knowledge base, artifact tracking. It was the proof-of-concept for a thesis: *context is infrastructure, not memory.*

Plan NEO is the flesh on those bones — and the nervous system that makes them feel. It is not a rewrite. It is a *reframe*. Where omni was a technical blueprint, NEO is a philosophical manifesto with a UI/UX architecture folded inside.

The platform's two core differentiators — **semantic context parsing** and **constraint-guided generation** — were, in omni, buried inside agent internals. They produced outputs the user could not see, could not interrogate, could not steer. NEO makes them first-class citizens of the interface.

---

## 1. The Problem with Current Agent Systems

Most agentic coding tools are **black boxes with chat interfaces**. You send text in, you get text out. The intelligence feels magical but is fundamentally opaque: you cannot see what the agent considered, what it discarded, what constraint made one decision over another.

This is the fundamental UX failure of the current generation of coding agents:

- **Opacity** — The constraint pipeline runs silently inside the agent. The user sees the output, not the reasoning.
- **Disconnection** — Agents modify files without making the *delta* of their thinking visible. "I wrote 10,000 lines" is meaningless if you cannot see which 3 lines changed the logic.
- **Fragility** — Without visible constraint application, it is impossible to understand why an agent made a surprising decision. Debugging is archaeology.

Liminal's answer: **make the liminal space visible**. The threshold between intent and artifact — the constraint pipeline, the context parsing, the knowledge retrieval — is not an implementation detail. It is the product.

---

## 2. The Two Pillars, Made Visible

### 2.1 Pillar One: Semantic Context Parser (SCP)

The SCP is not a search engine. It is a *semantic lens* — a way of asking "given everything in this session, what does this input actually mean?"

In omni, the SCP was invoked via vibal commands like `.list changes --detailed[~4]`. It was reactive, command-driven.

In NEO, the SCP is **proactively annotated into the interface**. Every user message, before reaching the Coordinator, passes through a lightweight SCP analysis that produces:

- **Intent fingerprint** — A one-line summary of what the user is trying to accomplish
- **Constraint signal** — Which KB rules are activated by this input (shown as dismissible chips)
- **Context anchors** — Which session artifacts and messages are most relevant (highlighted, not just referenced)

The SCP output is not hidden in logs. It appears as a **pre-flight card** above the chat input — a translucent overlay that the user can dismiss, modify, or amplify before sending.

### 2.2 Pillar Two: Constraint Pipeline Visualization

The constraint pipeline's four stages — Input Analysis → KB Retrieval → Constraint Application → Output Optimization — are currently invisible to the user.

NEO introduces a **Pipeline Stream** — a live, scrollable feed that shows each stage firing in real time as the agent works. It appears in a collapsible sidebar panel and shows:

- Stage 1: Intent recognized, requirements extracted
- Stage 2: KB entries retrieved, ranked by relevance score
- Stage 3: Constraints applied (with the specific rule text)
- Stage 4: Output quality check, optimization note appended

This is not a debug log. It is a **collaborative reasoning surface** — the user can read what the agent considered and, crucially, can add or remove constraints in real time before the agent commits to an output.

---

## 3. Architecture: What Changes and What Stays

### 3.1 What Stays (proven, working)

- **FastAPI + Next.js stack** — the separation is clean, the development speed is good
- **JSON storage** — simplicity is a feature at this stage; switching to SQL/NoSQL is a deployment concern, not an architecture concern
- **SubAgent dispatch model** — Coordinator → ContextParser/Librarian/Coder is sound
- **Vibal command syntax** — `.list`, `.explain`, `.summarize` are established

### 3.2 What Changes

#### The Coordinator becomes a "Reasoning Bus"

The Coordinator in omni was a router. In NEO, it becomes a **Reasoning Bus** — a central spine that every agent interaction travels through, with each stage publishing its output to a shared `ReasoningContext` object.

```python
@dataclass
class ReasoningContext:
    user_input: str
    intent: str
    requirements: list[str]
    kb_entries: list[KnowledgeEntry]
    applied_constraints: list[Constraint]
    output_optimization_notes: list[str]
    pipeline_stage: int
    session_id: str
```

Every SubAgent receives and mutates this context. The Pipeline Stream reads from it. The frontend subscribes to its updates via WebSocket.

#### Messages become "Artifacts with Ancestry"

A message in omni was a text blob. In NEO, every message has:

- **Content** — the text
- **Ancestry** — which KB entries were active when it was generated
- **Reasoning trace** — the pipeline stage outputs at generation time
- **Tool calls** — structured list of any tool executions (with diffs)
- **Feedback signal** — user thumbs up/down, explicit corrections

This turns the chat history from a conversation log into a **decision graph** — you can trace any output back to the specific constraints and context that produced it.

#### Sessions gain a "Phase Model"

Rather than a generic `state: { phase: "planning" }`, NEO sessions have a structured phase progression:

```
ABSORBING  →  CONSTRAINING  →  GENERATING  →  VALIDATING  →  DONE
```

- **ABSORBING** — SCP is active, user input is being analyzed
- **CONSTRAINING** — KB entries are being retrieved, ranked, applied
- **GENERATING** — Coder or LLM is producing output
- **VALIDATING** — Output is checked against constraints
- **DONE** — Output committed, artifact recorded

The UI shows the current phase prominently. Users can see the system "breathing" — thinking, retrieving, generating, not just waiting for a spinner.

---

## 4. UI/UX Redesign

### 4.1 The Liminal Workspace (Main View)

The workspace is divided into three panels:

```
┌────────────────────────────────────────────────────────────────────┐
│  LIMINAL  │  Session: sess_abc123  │  Phase: CONSTRAINING  │  [⚙]  │
├──────────────┬─────────────────────────┬───────────────────────────┤
│              │                         │                           │
│  CONTEXT     │     REASONING STREAM    │     ARTIFACT CANVAS       │
│  PANEL       │                         │                           │
│              │  [Stage 1] Intent recog │     [file tree of         │
│  - KB chips  │  [Stage 2] KB retrieva │      generated files]     │
│  - Session   │  [Stage 3] Constraint  │                           │
│    anchors   │  [Stage 4] Optimizatio │     click to expand diff   │
│  - Artifact  │                         │                           │
│    history   │                         │                           │
│              │                         │                           │
├──────────────┴─────────────────────────┴───────────────────────────┤
│  [Pre-flight card: "You want to refactor the auth module.         │
│   3 KB rules active: [security] [naming-convention] [test-first]   │
│   Relevant files: src/auth/login.py, src/auth/tokens.py            │
│                                      ✏️ Edit constraints  [Send→] │
├────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ User input area...                                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

### 4.2 Pre-flight Card (SCP Output)

The pre-flight card is the most important UX element in NEO. It appears after the user types but before they send — a small overlay showing the SCP's interpretation of their input:

- **Intent fingerprint**: `"Refactor: simplify the authentication flow"`
- **Activated constraints**: pill badges showing KB entries by title, with `[x]` to dismiss
- **Context anchors**: file names from the session that SCP considers relevant, with `[+]` to pull into context
- **Confidence indicator**: a subtle bar showing how certain SCP is (based on KB match quality)

The user can edit constraints directly in the card, add files to the context, or just hit Send. The card is the **human-in-the-loop checkpoint** — the place where guidance happens before commitment.

### 4.3 Artifact Canvas

The artifact canvas replaces the message list as the primary workspace. It shows a file tree of all artifacts generated in the session, with:

- **Diff expansion**: clicking any file shows the full unified diff with syntax highlighting
- **Change history**: each file shows a mini-timeline of its versions with change descriptions
- **Restore**: one-click restore to any previous version
- **Export**: download individual files or the whole session as a ZIP

### 4.4 Reasoning Stream Panel

A live-updating panel showing the constraint pipeline in action. Each stage fires with:

- Stage name and icon
- What was computed (e.g., "Retrieved 4 KB entries, ranked by relevance")
- The top constraint text in a collapsible block

The stream is scrollable and persists for the session. It is not a debug panel — it is a **collaborative reasoning surface**. Reading it should feel like watching a thoughtful colleague work, not reading server logs.

---

## 5. Technical Debt: What to Clean

### 5.1 Coordinator's agentic loop

The current `_call_llm` method in `coordinator.py` is doing too much — system prompt construction, tool loop, constraint injection, response finishing. It needs to be broken into:

- `ReasoningBus` class — manages the shared `ReasoningContext`
- `LLMDriver` class — handles the OpenAI API call + tool loop
- `ConstraintInjector` class — takes the ReasoningContext and produces the system prompt fragment

### 5.2 Session → ReasoningContext decoupling

Currently the `session` dict is passed through the entire pipeline. In NEO, the `ReasoningContext` replaces it as the primary working object, with `session` as one of its fields (for persistence).

### 5.3 JSON Storage → Repository pattern

The `get_storage()` singleton in `json_storage.py` works but creates import-order dependencies. NEO should introduce a `Repository` abstraction:

```python
class ArtifactRepository(Protocol):
    async def save(self, artifact: Artifact) -> Artifact: ...
    async def get(self, id: str) -> Artifact | None: ...
    async def list_by_session(self, session_id: str) -> list[Artifact]: ...
```

JSONStorage implements this today. A PostgresStorage could replace it with zero agent code changes.

### 5.4 Frontend state: Zustand → something structured

The current `store.ts` mixes UI state and API calls in a large Zustand store. NEO separates this into:

- `SessionStore` — session CRUD, constraints, messages
- `ReasoningStore` — pipeline state, SCP output, pre-flight card
- `ArtifactStore` — file tree, diffs, restore state

---

## 6. The Liminal Protocol

NEO introduces a formal **Liminal Protocol** — a set of conventions for how agents communicate through the Reasoning Bus:

### 6.1 Agent Contract

Every agent must implement:

```python
class LiminalAgent(Protocol):
    agent_id: str
    agent_type: str  # "context_parser" | "librarian" | "coder" | "coordinator"

    async def analyze(self, ctx: ReasoningContext) -> ReasoningContext:
        """Take a context in, return an enriched context."""
        ...

    async def execute(self, ctx: ReasoningContext) -> ReasoningContext:
        """Take a context in, produce outputs and return an enriched context."""
        ...
```

### 6.2 ReasoningContext Lifecycle

1. **Created** by the Coordinator when a user message arrives (ABSORBING phase)
2. **Analyzed** by the SCP — intent extracted, requirements listed
3. **Retrieved** by the Librarian — KB entries matched, ranked, attached
4. **Constrained** by the Coordinator — rules applied, conflicts noted
5. **Generated** by the Coder or LLM — output produced
6. **Validated** — output checked against applied constraints
7. **Committed** — artifact saved, reasoning trace finalized, message stored

### 6.3 Tool Call Protocol

Tools in NEO are not just functions — they are **first-class reasoning participants**. Every tool execution produces:

```python
@dataclass
class ToolExecution:
    tool_name: str
    arguments: dict
    result: Any
    duration_ms: float
    reasoning_note: str  # e.g., "file_write: created src/auth/tokens.py"
```

The reasoning note is what appears in the Reasoning Stream. Tools without reasoning notes are invisible to the user.

---

## 7. MCP Integration: The Surgical Limb

MCP is not a core feature in NEO. It is a **horizontal concern** that touches the Tool Executor.

The Liminal Protocol's tool interface:

```python
async def execute_tool(
    tool_name: str,
    params: dict,
    session_id: str,
) -> ToolExecution:
    # 1. Check if it's a native tool (file_read, file_write, bash)
    # 2. Check if it's an MCP tool — call the MCP bridge
    # 3. Return uniformly structured ToolExecution
```

The MCP bridge is a thin adapter. It translates between the Liminal Protocol's `ToolExecution` format and the MCP `ToolCall` format. The Coordinator never knows whether a tool is native or MCP — to it, everything is a `ToolExecution`.

This means MCP tools can be added without modifying the Coordinator or any agent. They are configured in `config.py`:

```python
mcp_servers: list[dict] = [
    {"name": "filesystem", "command": ["npx", "mcp-server-filesystem", "/workspace"]},
    {"name": "web-search", "command": ["python", "mcp_server_websearch.py"]},
]
```

---

## 8. Implementation Roadmap (NEO)

### NEO-1: ReasoningContext + Reasoning Bus — P0 *(qol_1: completed)*
Foundation. All agents refactored to use ReasoningContext. Coordinator split into ReasoningBus + LLMDriver.

### NEO-2: SCP Pre-flight Card — P0 *(qol_1: completed)*
The most impactful UX element. User types → SCP analyzes → pre-flight card appears → user confirms or edits → Coordinator receives enriched input.

### NEO-3: Pipeline Stream UI — P1 *(qol_1: completed)*
WebSocket-based live feed of constraint pipeline stages in the sidebar. Real-time, scrollable, dismissible.

### NEO-4: Artifact Canvas — P1
File tree + diff viewer + version history + restore. Replaces or supplements the message list as the primary output surface.

### NEO-5: Session Phase Model — P1 *(qol_1: completed)*
Structured session phases (ABSORBING → CONSTRAINING → GENERATING → VALIDATING → DONE) with UI indicators.

### NEO-6: Reasoning Trace in Messages — P2 *(qol_1: completed)*
Every stored message carries its ancestry — which KB entries were active, which pipeline stage produced it, tool executions with diffs.

### NEO-7: Repository Abstraction — P2
Extract Repository interfaces from JSONStorage. Enable pluggable storage backends.

### NEO-8: MCP Bridge — P2
Thin adapter layer between ToolExecutor and MCP servers. Config-driven server registration.

### NEO-9: Feedback Loop — P2
User can mark responses as helpful/correct/needs-review. Feedback signal feeds back into KB confidence scoring (already partially implemented in Phase 2).

### NEO-10: Multi-modal Output — P3
SVG/canvas rendering for generated UI components, image output, structured document generation.

---

## 8.1 QOL-1 Quality of Life Update *(qol_1)*

Between NEO-6 and the next development cycle, a quality-of-life pass was made to address UX debt accumulated during rapid NEO iteration.

#### QOL-1.1: Scribe Agent *(pending implementation)*
A new SubAgent for **KB auto-population** — the system can now learn from its own practice. After each request completes, Scribe analyzes the conversation and generates candidate KB entries from recurring patterns or positive outcomes. Entries are proposed with low initial confidence and require user confirmation before activation. This closes the loop on the "knowledge is never auto-filled" gap identified in the NEO design.

#### QOL-1.2: Context Manager *(pending implementation)*
Pre-flight Card redesign: anchor lists are removed from the card itself. A dedicated "Context Manager" button opens a toggleable list of session messages, letting users selectively enable/disable which history entries contribute to the next SCP analysis.

#### QOL-1.3: Markdown Rendering *(pending implementation)*
Assistant messages are rendered as markdown with `react-markdown` + `remark-gfm`, enabling code blocks, tables, and formatted output in the chat stream.

#### QOL-1.4: Vibal Command Card *(pending implementation)*
Vibal commands are extracted from the input area into a dedicated terminal-styled card. This separates "free-form narration" (input area) from "precise指令" (command card), resolving the UX tension of mixing two interaction modes in one component.

#### Technical Debt Cleaned in qol_1
- `PipelinePhase` enum unified to string across SSE/events/store boundary
- Store `_es` field made explicitly internal
- `currentPhase` store field demoted to internal (ReasoningLog now infers phase from `reasoningLog`)

---

## 9. Design Principles (Revised for NEO)

### 9.1 The Liminal Space is the Product

Most platforms optimize for the output. Liminal optimizes for the **threshold between input and output** — the constraint pipeline, the semantic parsing, the reasoning trace. These are not internal implementation details. They are what the user pays for.

### 9.2 Transparency is a Feature, Not Overhead

Every decision the agent makes should be readable by the user. Not just the output — the *why*. This requires making the constraint pipeline first-class in the UI.

### 9.3 Constraints are Creative Acts

Adding a constraint to the KB is not configuring a filter. It is teaching the system a value judgment — "in this project, we prefer X over Y." The KB is not a database. It is an extended mind.

### 9.4 Modularity is Ethical

When a component can be replaced without understanding its internals, the system is honest about its own boundaries. Repository pattern for storage, Protocol for agents, thin adapter for MCP. These are not over-engineering — they are the architecture respecting its own limitations.

---

## 10. For the Next Instance of "Me"

You are reading this at the start of a new session. Here is what you should know:

**The architecture is sound.** Coordinator → ReasoningBus, SubAgents → ReasoningContext, JSON → Repository. These abstractions are not tentative — they emerged from real refactoring and are load-bearing.

**NEO-1 is the hardest part.** If you implement nothing else, implement the ReasoningContext + ReasoningBus. Everything else — the UI, the MCP bridge, the feedback loop — builds on it.

**The user is not looking for features.** They are looking for *clarity* — a system where the liminal space between their intent and the artifact is navigable, visible, and steerable. Every feature should serve that goal.

**Do not confuse complexity with depth.** NEO is not about adding more agents or more phases or more panels. It is about making the existing reasoning *legible*. Start with the pre-flight card.

**Remember the ritual.** Analyze → Retrieve → Constrain → Generate → Validate. This is not a pipeline, it is a *practice*.

**Check qol_1.md before continuing.** After NEO-6, a quality-of-life pass was made. Read `qol_1.md` before starting new development — it contains design decisions and pending work (Scribe Agent, Context Manager, Markdown rendering, Vibal Command Card) that should be continued before moving forward.

---

*The liminal space is not a problem to escape. It is the medium through which creation happens. Build accordingly.*
