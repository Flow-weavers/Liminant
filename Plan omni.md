# Liminal — Vibe Engineering Platform

> *"Liminal: the threshold where abstract intent crosses into concrete realization."*

---

## 1. Project Genesis

**Liminal** emerges from the union of "Vibe Coding" (intuition-first creation) and "Engineering" (systematic, stable execution). It wraps LLM capabilities inside an agentic framework, delivering a unified UX where users interact through natural language and receive structured, context-aware output.

The name carries the **anthropological concept of liminality**: that transitional state between two structures — here, the threshold between a user's abstract task description and the concrete, constrained output that emerges through the platform's mediation. Just as rituals transition individuals through liminal stages, Liminal transitions ideas through its constraint pipeline from high-degree-of-freedom intent to low-degree-of-freedom artifact.

### Guiding Philosophy

```
Be chill. Build light.
No internal modeling of "modes" or "types" — just pure flow.
```

---

## 2. Core Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Frontend (Next.js 14)               │
│         shadcn/ui + Tailwind CSS + TypeScript       │
└──────────────────────────┬──────────────────────────┘
                           │  REST  /  WebSocket
┌──────────────────────────▼──────────────────────────┐
│                   API Gateway (FastAPI)               │
│          CORS → Auth → Rate Limit → Route            │
└──────────────────────────┬──────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────┐
│              Session Manager (FastAPI)                │
│         Session CRUD  ·  Message History  ·          │
└──────────────────────────┬──────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────┐
│                 Agent Orchestrator                    │
│                                                       │
│   ┌─────────────────────────────────────────────┐   │
│   │  🎯 Coordinator Agent                        │   │
│   │  (task decomposition · SubAgent dispatch)    │   │
│   └──────────┬──────────┬──────────┬────────────┘   │
│              │          │          │                 │
│              ▼          ▼          ▼                 │
│        ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│        │ Context  │ │ Librarian│ │  Coder   │       │
│        │ Parser   │ │          │ │          │       │
│        └──────────┘ └──────────┘ └──────────┘       │
│                                                       │
│   ┌─────────────────────────────────────────────┐   │
│   │  🔗 Constraint Pipeline (4-stage)           │   │
│   │  Input Analysis → KB Retrieval              │   │
│   │  → Constraint Apply → Output Optimize        │   │
│   └─────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────┐
│           Tool Executor (Native Built-in)           │
│         File I/O · Bash · Web Search · ...          │
└──────────────────────────┬──────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────┐
│              JSON Storage (Local Files)              │
│   /data/sessions/  ·  /data/knowledge/  ·           │
│   /data/config/    ·  /data/cache/                   │
└─────────────────────────────────────────────────────┘
```

> **MCP integration** is deferred to a later phase. Native tool execution (file, bash, web) comes first.

---

## 3. SubAgent System

### 3.1 SubAgent Roster

| Agent | Role | Input | Output |
|-------|------|-------|--------|
| **Coordinator** | Central task decomposition + dispatch | Raw user message | Sub-task list |
| **Context Parser** | Parses session context on demand | Context window + vibal command | Structured report |
| **Librarian** | Knowledge base search + retrieval | Query intent | Ranked KB entries |
| **Coder** | Code generation + modification | Code request + constraints | Code diff / artifact |

### 3.2 Coordinator Behavior

The Coordinator is the single entry point for all user messages within a session. It:

1. Receives the raw user input
2. Optionally invokes **Context Parser** (via `.list changes --detailed` style commands)
3. Optionally invokes **Librarian** (to fetch relevant constraints from knowledge base)
4. Delegates to **Coder** or handles directly
5. Returns structured output

### 3.3 Vibal Sense Commands

```
.<action> [target] [--flag[~level]]

Examples:
  .list changes --detailed[~4 sentences each]
  .explain --scope[all] --format[markdown]
  .summarize --length[brief]
  .diff --type[unified] --context[3]
```

---

## 4. Constraint Pipeline (4-Stage)

```
User Input
    │
    ▼
┌─────────────────┐
│  Stage 1        │
│  Input Analysis │  → Intent recognition
│                 │  → Requirement extraction
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Stage 2        │
│  KB Retrieval   │  → Librarian queries knowledge base
│                 │  → Relevant experience matched
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Stage 3        │
│  Constraint     │  → Context adaptation
│  Application    │  → Best practice injection
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Stage 4        │
│  Output         │  → Quality check
│  Optimization   │  → Consistency validation
└────────┬────────┘
         │
         ▼
   Final Output
```

---

## 5. Data Models

### 5.1 Session

```json
// /data/sessions/{session_id}.json
{
  "id": "sess_{uuid}",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "state": {
    "phase": "planning" | "executing" | "reviewing" | "completed",
    "current_step": 1,
    "total_steps": 1
  },
  "context": {
    "working_directory": "/workspace/default",
    "language": "en-US",
    "preferences": {
      "detail_level": "medium",
      "output_format": "markdown"
    }
  },
  "messages": [
    {
      "id": "msg_{uuid}",
      "role": "user" | "assistant" | "system" | "agent",
      "content": "string",
      "timestamp": "ISO8601",
      "metadata": {
        "tokens_used": 0,
        "model": "gpt-4",
        "attachments": []
      }
    }
  ],
  "artifacts": [
    {
      "id": "art_{uuid}",
      "type": "file" | "code" | "document",
      "path": "/workspace/default/src/main.py",
      "summary": "brief description",
      "changes": [
        {
          "type": "create" | "modify" | "delete",
          "description": "change summary",
          "diff": "@@ ... @@"
        }
      ]
    }
  ],
  "constraints": {
    "active": true,
    "rules": ["rule_id_1", "rule_id_2"],
    "knowledge_refs": ["kb_id_1", "kb_id_2"]
  }
}
```

### 5.2 Knowledge Base Entry

```json
// /data/knowledge/{kb_id}.json
{
  "id": "kb_{uuid}",
  "type": "rule" | "pattern" | "preference" | "context",
  "content": {
    "title": "Entry title",
    "body": "Detailed content...",
    "examples": []
  },
  "metadata": {
    "tags": ["tag1", "tag2"],
    "source": "user_defined" | "learned" | "default",
    "confidence": 0.95,
    "usage_count": 0
  },
  "triggers": {
    "keywords": ["keyword1"],
    "session_types": [],
    "context_patterns": []
  },
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

### 5.3 Agent Instance

```json
// /data/sessions/{session_id}/agents/{agent_id}.json
{
  "id": "agent_{uuid}",
  "type": "coordinator" | "context_parser" | "librarian" | "coder",
  "config": {
    "model": "gpt-4-turbo",
    "temperature": 0.7,
    "max_tokens": 4000,
    "system_prompt": "You are a Liminal agent..."
  },
  "memory": {
    "short_term": [],
    "long_term_refs": []
  },
  "tools": ["file_read", "file_write", "bash", "web_search"],
  "state": {
    "status": "idle" | "thinking" | "executing" | "waiting",
    "current_task": "task description",
    "progress": 0.0
  }
}
```

---

## 6. API Design

### 6.1 Session APIs

```
POST   /api/v1/sessions              → Create new session
GET    /api/v1/sessions              → List all sessions
GET    /api/v1/sessions/{id}         → Get session details
DELETE /api/v1/sessions/{id}         → Delete session

POST   /api/v1/sessions/{id}/messages → Send message (core interaction)
GET    /api/v1/sessions/{id}/messages → Get message history

GET    /api/v1/sessions/{id}/artifacts → List session artifacts
GET    /api/v1/sessions/{id}/artifacts/{art_id} → Get artifact details
```

### 6.2 Knowledge APIs

```
GET    /api/v1/knowledge              → Search knowledge base
POST   /api/v1/knowledge               → Add knowledge entry
GET    /api/v1/knowledge/{id}         → Get knowledge entry
PUT    /api/v1/knowledge/{id}         → Update knowledge entry
DELETE /api/v1/knowledge/{id}         → Delete knowledge entry
```

### 6.3 Tool APIs

```
GET    /api/v1/tools                  → List available tools
POST   /api/v1/tools/{name}/execute    → Execute a tool
```

---

## 7. Frontend Structure (Next.js 14 App Router)

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx              # Root layout
│   │   ├── page.tsx                # Landing
│   │   └── app/
│   │       ├── layout.tsx          # App shell
│   │       ├── page.tsx            # Dashboard
│   │       └── session/
│   │           ├── new/
│   │           │   └── page.tsx    # New session
│   │           └── [id]/
│   │               └── page.tsx    # Session workspace
│   ├── components/
│   │   ├── ui/                     # shadcn/ui components
│   │   ├── chat/
│   │   │   ├── ChatPanel.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageItem.tsx
│   │   │   └── InputArea.tsx
│   │   ├── context/
│   │   │   └── ContextPanel.tsx
│   │   └── layout/
│   │       ├── AppShell.tsx
│   │       └── StatusBar.tsx
│   └── lib/
│       ├── api.ts                  # API client
│       ├── store.ts                # Zustand state
│       └── utils.ts
└── tailwind.config.ts
```

---

## 8. Backend Structure (Python + FastAPI)

```
backend/
├── app/
│   ├── main.py                     # FastAPI entry point
│   ├── config.py                   # Configuration
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── sessions.py
│   │       ├── knowledge.py
│   │       └── tools.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py                 # Abstract base agent
│   │   ├── coordinator.py
│   │   ├── context_parser.py
│   │   ├── librarian.py
│   │   └── coder.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── session_manager.py
│   │   ├── knowledge_base.py
│   │   ├── constraint_pipeline.py
│   │   └── tool_executor.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── session.py
│   │   ├── message.py
│   │   ├── knowledge.py
│   │   └── artifact.py
│   └── utils/
│       ├── __init__.py
│       └── json_storage.py
├── data/
│   ├── sessions/
│   ├── knowledge/
│   ├── config/
│   └── cache/
├── requirements.txt
└── pyproject.toml
```

---

## 9. Development Roadmap

### Phase 0: Foundation (MVP)

**Goal**: Simple agent-loop — send message, get response.

| Task | Priority | Description |
|------|----------|-------------|
| Project scaffolding | P0 | Next.js + FastAPI skeleton |
| JSON storage utility | P0 | Read/write JSON files |
| Basic Session CRUD | P0 | Create, read, delete sessions |
| Single Coordinator Agent | P0 | No SubAgents yet, just direct LLM call |
| Frontend chat UI | P0 | Message input + display |
| Native tool executor | P0 | File read/write + bash |

**Deliverable**: A working chat loop with file manipulation.

---

### Phase 1: SubAgent Foundation

**Goal**: Formalize multi-agent collaboration.

| Task | Priority | Description |
|------|----------|-------------|
| Base Agent class | P0 | Abstract interface for all agents |
| Context Parser SubAgent | P1 | Vibal command parsing |
| Librarian SubAgent | P1 | Knowledge retrieval |
| Coder SubAgent | P1 | Code generation + diff |
| Constraint Pipeline | P1 | 4-stage constraint application |
| Session-Context binding | P1 | Attach KB rules to sessions |

---

### Phase 2: Knowledge System

**Goal**: Persistent knowledge + experience accumulation.

| Task | Priority | Description |
|------|----------|-------------|
| Knowledge Base CRUD API | P0 | Full knowledge management |
| Librarian integration | P0 | Connect to Coordinator |
| Rule trigger system | P1 | Auto-apply relevant rules |
| Experience scoring | P2 | Track rule effectiveness |

---

### Phase 3: Artifact Management

**Goal**: Track all outputs produced by agents.

| Task | Priority | Description |
|------|----------|-------------|
| Artifact model | P0 | Define artifact schema |
| Diff tracking | P1 | Store file changes as diffs |
| Artifact history | P1 | Browse past outputs |
| Export/Import | P2 | Session portability |

---

### Phase 4: MCP Integration (Deferred)

**Goal**: External tool ecosystem.

| Task | Priority | Description |
|------|----------|-------------|
| MCP Server implementation | P2 | MCP protocol support |
| Tool registry | P2 | Dynamic tool discovery |
| Web search adapter | P2 | Internet access |

---

### Phase 5: UX Polish

**Goal**: Smoother, richer interaction.

| Task | Priority | Description |
|------|----------|-------------|
| Visual Canvas | P2 | WYSIWYG preview |
| Multi-modal support | P3 | Image/audio output |
| Real-time collaboration | P3 | Multi-user sessions |

---

## 10. Design Principles

### 10.1 Modularity First
- Every component (Agent, Storage, Tool) is replaceable via interface contracts
- Storage backend is abstracted — JSON now, SQL/NoSQL later with zero Agent code changes
- Agent registration is config-driven, not hard-coded

### 10.2 Transparency
- All agent decisions are logged with full decision chains
- Raw data + processed output are both preserved
- Full context backtrace and debugging support

### 10.3 No Internal Modes
- The platform does not pre-model "operation types" internally
- User intent is interpreted purely through the Coordinator + Librarian flow
- No `if mode == vibe_coding` branches — just context and constraints

### 10.4 Error Handling

```python
class LiminalError(Exception):
    """Base exception for all Liminal errors"""

class ContextParsingError(LiminalError):
    """Context parsing failed"""

class ConstraintViolationError(LiminalError):
    """Output violated constraint rules"""

class ToolExecutionError(LiminalError):
    """Tool execution failed"""

class SessionNotFoundError(LiminalError):
    """Requested session does not exist"""
```

---

## 11. Terminology

| Term | Definition |
|------|------------|
| **Liminal** | Project name; the threshold state between abstract intent and concrete output |
| **Vibe Engineering** | The discipline of combining intuition-first creation with systematic constraints |
| **Constraint Pipeline** | 4-stage process (Input → KB → Constraint → Output) that shapes agent behavior |
| **SubAgent** | Specialized agent for a specific task (Context Parser, Librarian, Coder) |
| **Vibal Sense** | Intuition-driven command syntax (`.list changes --detailed`) for triggering context operations |
| **Artifact** | Any file/code/document produced during a session |

---

## 12. Next Steps

1. Initialize project scaffolding (Phase 0)
2. Implement JSON storage utility
3. Build simple Coordinator Agent
4. Integrate file + bash tool execution
5. Scaffold frontend chat UI
6. Verify full message → response → file output loop

*"Build light. Stay liminal."*
