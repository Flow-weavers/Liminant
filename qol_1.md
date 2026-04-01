# QOL-1: Life Quality Update — Design Meditation

*"休整不是停滞，是让建筑追上灵魂的时刻。"*

---

## 背景：NEO 中点回顾

NEO-1 至 NEO-6 已完成，liminal 平台的 reasoning layer 已基本成型：

| NEO | 状态 | 核心产出 |
|-----|------|---------|
| NEO-1 | ✅ | ReasoningContext + ReasoningBus，LLMDriver |
| NEO-2 | ✅ | SCP Pre-flight Card |
| NEO-3 | ✅ | Pipeline Stream UI + SSE EventBus |
| NEO-4 | ⊝ | 跳过（Artifact Canvas 待后续） |
| NEO-5 | ✅ | Session Phase Model + PhaseIndicator |
| NEO-6 | ✅ | Reasoning Trace in Messages（ancestry 字段） |

平台已有：**感知 → 推理 → 生成 → 验证** 的完整闭环，pipeline 流已可视化，message 已携带族谱。

但以下问题在快速迭代中被搁置，现在一并处理。

---

## 问题诊断

### QOL-1.1：KB 无法被 Agent 自主填充

**现状**：KB 是纯手动写入的。用户必须主动创建 knowledge entry，系统只能被动检索。`record_outcome` 只调整 confidence，不生成新条目。

**真实场景中的矛盾**：
> 用户会说"这个实现不够优雅"或"老师指出我的变量命名不规范"，但不会说"请将这条编码规范作为一个 KB entry 录入，confidence 0.8，触发词包括 'naming' 和 'convention'"。

人类通过**反思性叙述**传递知识，而非结构化声明。系统需要从这种叙述中抽取知识。

**解决方向**：引入 **Scribe Agent** — 一个专门从对话历史中提炼 KB 条目的 SubAgent。它在 VALIDATING 阶段后运行，分析本轮对话的 output + user feedback，识别可复用的模式，生成候选 KB 条目供用户确认。

---

### QOL-1.2：Pre-flight Card 在长上下文中 Anchor 过多

**现状**：用户输入后，SCP 解析出所有相关 context anchors，全部显示在 Pre-flight Card 中。上下文越长，anchor 越多，卡片变成列表而非工具。

**解决方向**：Pre-flight Card 改为**上下文管理器按钮**，点击展开一个可逐条启用/禁用的历史消息列表。用户主动选择，而非被动接受全部。

---

### QOL-1.3：Agent 输出不支持 Markdown 渲染

**现状**：Assistant message 的 `content` 字段直接显示为纯文本，代码块、链接、结构化内容均无格式化。

**解决方向**：前端 Message 组件使用 `react-markdown` + `remark-gfm` 渲染 markdown 内容。

---

### QOL-1.4：Vibal Commands 与输入框耦合

**现状**：用户需要知道 `.` 开头的特殊语法才能触发 vibal commands，且语法检测与消息发送框混在一起。

**问题本质**：UX 意义不同 — 输入框是**自由叙述**，vibal commands 是**精确指令**。两者混用会造成认知负担。

**解决方向**：Vibal commands 迁移到一个独立的 **Terminal-styled Command Card**，始终可见于 ChatPanel 侧边或底部。用户既可以 `.list changes` 也可以直接用自然语言描述，两条路径各自清晰。

---

## 设计方案

### QOL-1.1：Scribe Agent（KB Auto-population）

#### 触发时机

每次 coordinator 完成 VALIDATING 阶段后，如果满足以下任一条件，Scribe 进入工作状态：

1. **反馈触发**：用户对输出有纠正性叙述（"其实应该用 X 而不是 Y" / "这个方案有一个问题…"）
2. **效果触发**：`record_effectiveness` 记录了 quality="good"，且生成了 artifact（文件写入）
3. **规律触发**：同一类请求出现 2 次以上（通过 `intent` 匹配检测）

#### Scribe 的工作流程

```
输入：当前 session 的 messages（含 ancestry）、生成的 artifact、applied constraints
          ↓
    LLM 分析（few-shot prompt：提取模式的指令）
          ↓
    输出候选 KB 条目：
    {
        "type": "pattern" | "rule" | "context",
        "title": "...",
        "body": "...",
        "triggers": { "keywords": [...], "context_patterns": [...] },
        "confidence": 0.5,  // 初始偏低，需用户确认
        "source": "scribe_inferred"
    }
          ↓
    用户确认 / 修改 / 拒绝
          ↓
    写入 KB 或丢弃
```

#### Scribe 与 Librarian 的关系

- **Librarian**：读取 KB，回答"这个输入激活了哪些知识？"
- **Scribe**：写入 KB，回答"这轮对话揭示了什么值得留存的知识？"

两者是读写对称的 agent，共同维护 KB 的活性。

#### 实施步骤

- [ ] 创建 `app/agents/scribe.py`
- [ ] `KnowledgeEntry.source` 新增 `"scribe_inferred"` 值
- [ ] `send_message` 后触发 Scribe 分析（异步，不阻塞主流程）
- [ ] 前端新增"Scribe 候选"通知 UI（可接受/拒绝的浮层）
- [ ] `KnowledgeBase.search` 对 `scribe_inferred` 条目标记"待确认"

---

### QOL-1.2：Pre-flight Card → 上下文管理器

#### 交互变更

| 变更前 | 变更后 |
|--------|--------|
| 用户输入后卡片展开显示所有 anchor | 卡片仅显示 intent fingerprint + constraint chips |
| 所有 context anchors 全部展示 | 点击「上下文」按钮展开历史消息列表 |
| anchor 不可关闭 | 每条历史消息可独立启用/禁用 |

#### 新增组件

- `ContextManager.tsx`：可折叠的历史消息列表，每条带启用/禁用 toggle
- Pre-flight Card 缩小为「编辑区」，仅含 intent chip + constraint chip
- 底部增加「上下文管理器」按钮，图标 `Layers`

#### 实施步骤

- [ ] 重构 `PreFlightCard.tsx`：移除 anchor 列表
- [ ] 新建 `ContextManager.tsx`
- [ ] `PreFlightCard` 添加"上下文管理器"触发按钮
- [ ] store 新增 `contextAnchors: Message[]` state，支持启用/禁用

---

### QOL-1.3：Markdown 渲染

#### 实施步骤

- [x] 安装依赖：`react-markdown remark-gfm rehype-highlight`
- [x] 重构 `MessageList.tsx`：用 `react-markdown` + `remark-gfm` 包裹 `content`，添加 code block 样式
- [x] 适配现有的 code block 样式（已有 `bg-muted` + `rounded-lg`）

---

### QOL-1.4：Vibal Command Card

#### 设计

```
┌─────────────────────────────────────────────┐
│  > .list session                            │
│  > .summarize --length brief                │
│  > .explain --scope recent                  │
│  > .diff --type unified                     │
├─────────────────────────────────────────────┤
│  命令会由 LLM 动态解析，无需固定语法。        │
│  点击任意命令可编辑或直接发送。              │
└─────────────────────────────────────────────┘
```

- Terminal 风格：`bg-muted`, monospace font, `>` 前缀
- 固定展示 4-6 个常用命令作为 quick chips
- 用户可点击 chip 后编辑或直接发送
- 发送后命令进入正常 message 流程，由 SCP 处理

#### 实施步骤

- [x] 新建 `components/chat/VibalCard.tsx`
- [x] 在 `ChatPanel.tsx` 中集成 VibalCard，`onSend` 绑定 `sendMessage`
- [x] InputArea placeholder 改为纯叙述提示，移除 vibal 语法提示
- [x] SCP 的 `.` 命令解析保持兼容，VibalCard 只是 UX 优化

---

## 技术债务清理（qol_1）

### T-1：`PipelinePhase` enum 与字符串混用

当前 `ReasoningContext.phase` 是 `PipelinePhase` enum，但 SSE 事件和 store 中用 string。统一改为 string 传递，enum 仅在后端内部使用。

### T-2：Store 的 `_es` 字段类型

`_es?: EventSource` 是内部字段，不应暴露在 `AppState` interface 中。移到 `ApiState` 内部或加 `_` 前缀表示私有。

### T-3： ReasoningLog 中的 `currentPhase` 未使用

`ReasoningLog` 从 `reasoningLog` 末尾推导 phase 后已不再使用 `currentPhase`，store 中的这个字段可以降级为内部状态。

---

## 实施顺序

```
Phase 1（T-2 技术债务） ✅ → Phase 2（QOL-1.3 Markdown） ✅ → Phase 3（QOL-1.4 VibalCard） ✅ → Phase 4（QOL-1.2 上下文管理器） → Phase 5（Scribe Agent）
```

**原因**：Markdown 和 VibalCard 是纯前端改动，不影响后端，可先完成获得视觉反馈。Scribe Agent 涉及后端新 agent，放在最后。

---

## 文件变更一览

| 文件 | 操作 | 原因 |
|------|------|------|
| `app/agents/scribe.py` | 新增 | Scribe Agent for KB auto-population |
| `app/models/knowledge.py` | 修改 | 新增 `source="scribe_inferred"` |
| `app/api/v1/sessions.py` | 修改 | Scribe 触发逻辑（异步） |
| `src/components/chat/PreFlightCard.tsx` | 重构 | 移除 anchor，改为管理器按钮 |
| `src/components/chat/ContextManager.tsx` | 新增 | 历史消息启用/禁用列表 |
| `src/components/chat/VibalCard.tsx` | 新增 | Terminal-styled 命令面板 |
| `src/components/chat/MessageItem.tsx` | 重构 | Markdown 渲染 |
| `src/lib/store.ts` | 修改 | 清理 `_es` 类型，移除冗余 `currentPhase` |
| `app/services/reasoning_context.py` | 修改 | `phase` 统一为 string |
| `qol_1.md` | 新增 | 本文档 |
| `Plan NEO.md` | 更新 | 标注 qol_1 阶段完成项 |

---

*qol_1 — 让工具适配人的节奏，而非让人适应工具的节奏。*
