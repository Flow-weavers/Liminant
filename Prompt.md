# Conceptual background overview / 背景信息总览:

我最近构想于一个新生代的Vibe Engineering平台，
拥有完善的语义{上下文和知识库}管理体系，MCP工具调用功能等。

平台app的技术栈应当基本透明，解耦。这样方便我直接修改代码中具体接口的实现来修改对应的方法逻辑。
我想要把它做成类似web app的形式，使用Next.js+React和tailwind css前端；python+FastAPI后端。

$_`Vibe Engineering`_:
- 结合了Vibe Coding和Engineering中（分别）『vibal sense』和『make things work stablely』的概念与初衷，旨在构建一个全合一的用户体验流：用户通过一套Agentic Framework System作为wrapper代理地操作LLM产出任何用户想要的输出。由于此类应用varies from「Agent Coder」to「Text-to-PPT-slides Generator」等，故做他们实现的UX为“Vibe Engineering”。

$_`上下文管理`_：
- 在我平时使用的类似应用中，经常出现以下情况：
  1. **Agent生成的输出无法与人类用户工作语境完美衔接**：顶尖的，elaborated的AI Agent Workflow体验往往在几个小时内就能烧掉1M+的tokens output，人类却只能靠redundent的视觉系统和语言理解系统逐行（或逐页, depends on the form）阅读。这一点尤其在Vibe Coding时明显：Coder在根据更新后的OpenApi文档和项目需求更改数据库schema和后端架构时，我往往难以直接了解它做了什么：对于大型的项目来说，做出的改动将是万行级别的。
  2. **Agent生成的内容和用户真正想要的完全不同**：有些时候用户在构建提示词时也不知道他们真正想要的是什么，就算明确了真正的需求，Agent还是会不可避免地因为多部执行的上下文隐/显式压缩和幻觉以及预训练数据集中的模式偏见生成一些匪夷所思或“左右脑互博”的内容。比如 LLM 无法真正的看见前端效果（除非与多模态模型深度集成的Agent），所以他们在设计前端时只能依靠固有编码经验和『相对失真』的想象。
- 为了解决这些问题，我设计了两套系统：
  1. $$_`上下文解析SubAgent`_：通过输入一句话靠『vibal sense』工作的指令（如`.list changes --detailed[~4 sentences each]`），专用解析SubAgent会将选定的上下文解析，并输出报告样式的文本总结。
  2. $$_`约束管线`_：通过部署知识库 for each Agent instance，Agent可以根据用户的输入信息流总结“用户想要什么”“在这里这样做会更合适”等等经验。知识检索和提取可以由另一个图书管理员SubAgent完成。这样子Agent也就不用局限于将对话内的上下文全部记住，可以把历史记录丢到知识库里，然后由检索决定是否提取。通过这两项功能，将Agent的一个session封装成一个『约束管线』。

---

# What could you help me with / 你需要帮我干啥？：

在听我说了这么多之后，用你涌现出的想法帮我初步规划这个平台的构建逻辑和架构并生成一系列关于项目的概念性设计文档；你生成的文档将会用于指导Vibe coding，其他Agent，和我的人类朋友。不用着急给出超级具体的实践细节。为了更快的进行原型验证，数据全部在本地用json存储，不用真正的数据库。