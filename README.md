# Engineering Pattern Evaluation & Decision Engine
> 面向 Coding Agent 的软件工程决策证据系统与架构方案库 (Engineering Memory & Decision Engine)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Architecture Standard](https://img.shields.io/badge/standard-MADR%20%2F%20Anthropic%20Agentic-orange.svg)](https://github.com/adr/madr)
[![Evaluation Benchmark](https://img.shields.io/badge/benchmark-SWE--bench%20aligned-green.svg)](https://www.swebench.com/)

---

## 🌟 核心理念与行业标准对齐

传统针对 Coding Agent 的方案往往局限于“静态文档 RAG”或“代码生成”，但代码生成并不等于**工程架构决策能力**。随着大语言模型能力进化，普通的语法与基础代码生成会被模型内化，而**“真实项目中的架构权衡、失败边界、反事实演进与可验证代码切片”**成为最稀缺的工程资产。

本项目对齐全球工业界与学术界顶尖标准：
- 🏛️ **Anthropic: Building Effective Agents**：权威 Agent 工作流架构规范（Prompt Chaining, Routing, Parallelization, Orchestrator-Workers, Evaluator-Optimizer）。
- 📝 **MADR (Markdown Any Architecture Decision Records)**：机器可读的微架构决策标准。
- 🧪 **Voyager (NVIDIA/Stanford)**：代码必须通过独立沙箱单测验证后方可入库与沉淀的自进化闭环。
- 🔍 **Reflexion (NeurIPS)**：结构化失败反思与边界防坑机制（Failure Pattern）。
- 📊 **SWE-bench / SWE-agent (Princeton NLP)**：真实仓库级修复轨迹（Trajectory）与评估基准。
- 🌳 **Tree-sitter (GitHub)**：精确提取跨语言最小可运行代码切片（Code Slice）。

---

## 🏗️ 系统核心架构 (CBR 决策引擎)

系统基于经典人工智能的 **CBR (Case-Based Reasoning, 4R 模型)** 范式运作：

```
                [ 1. 用户开发任务 / Target Context ]
                                 │
                                 ▼
         ┌────────────────────────────────────────────────┐
         │ 1. 任务解析 (Retrieve): 抽取软硬件环境与硬性约束 │
         └───────────────────────┬────────────────────────┘
                                 │
                                 ▼
         ┌────────────────────────────────────────────────┐
         │ 2. 双路检索 (Hybrid Retrieval):                │
         │    - 语义相似度 (ChromaDB / 意图与场景匹配)      │
         │    - 约束拓扑过滤 (NetworkX / 版本兼容与拓扑图谱)│
         └───────────────────────┬────────────────────────┘
                                 │
                                 ▼
         ┌────────────────────────────────────────────────┐
         │ 3. 权衡矩阵与裁决 (Reuse/Advise):              │
         │    输出候选 Pattern 的优缺点、落地代价、失败边界 │
         └───────────────────────┬────────────────────────┘
                                 │
                                 ▼
         ┌────────────────────────────────────────────────┐
         │ 4. 范例自我变异 (Revise/Adapt):                │
         │    基于高质量验证代码切片生成适配目标项目的代码   │
         └───────────────────────┬────────────────────────┘
                                 │
                                 ▼
         ┌────────────────────────────────────────────────┐
         │ 5. 沙箱验证与经验回流 (Retain/Feedback):       │
         │    单测与基准通过后更新证据图谱，记录失败反思    │
         └────────────────────────────────────────────────┘
```

---

## 📂 模块目录结构

```text
Engineering Pattern Evaluation/
├── config/                        # 全局配置模块
│   └── settings.py
├── core/                          # 核心领域模型与规范
│   ├── schema.py                  # Pydantic 数据模型 (DecisionSlice, Evidence, Constraints)
│   ├── graph_schema.py            # 证据图谱节点与边关系定义
│   └── constants.py               # 权威模式与证据分级常量
├── storage/                       # 混合存储层 (向量 + 知识图谱)
│   ├── vector_store.py            # 语义检索 (ChromaDB)
│   ├── evidence_graph.py          # 拓扑约束与证据关联图谱 (NetworkX)
│   └── hybrid_repository.py       # 统一数据持久化门面
├── ingestion/                     # 方案提取与代码切片
│   ├── ast_slicer.py              # Tree-sitter / AST 提取可运行切片
│   ├── reverse_adr_miner.py       # 从 PR/Issue/Commit 逆向抽取 ADR
│   └── trajectory_parser.py       # SWE-bench 轨迹解析器
├── evaluator/                     # 验证与评测引擎
│   ├── sandbox_runner.py          # Docker / 进程沙箱执行器
│   ├── evidence_scorer.py         # 证据分级与置信度算法 (L1/L2/L3)
│   └── stale_detector.py          # 依赖弃用与时效性探测
├── engine/                        # CBR 决策与代码变异运行时
│   ├── task_analyzer.py           # 任务场景与约束解析器
│   ├── pattern_retriever.py       # 混合检索器
│   ├── tradeoff_advisor.py        # 权衡矩阵与正反边界分析器
│   ├── adaptation_agent.py        # 范例自变异生成器
│   └── cbr_orchestrator.py        # 决策流程总编排器
├── seeds/                         # 预置权威 Golden Cases 种子库
│   ├── agent_patterns/            # Anthropic 5大Agent核心工作流
│   └── backend_patterns/          # 分布式队列、缓存一致性等模式
├── tests/                         # 单元测试与端到端集成测试
└── cli.py                         # 交互式命令行工具
```

---

## 🚀 快速上手

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 导入种子方案库
```bash
python cli.py seed
```

### 3. 进行架构方案评估与决策 (Evaluate)
```bash
python cli.py evaluate --query "设计一个需要并行处理10万用户请求并进行最终汇总校验的 Agent 系统"
```

### 4. 端到端 CBR 代码生成与变异 (Solve)
```bash
python cli.py solve --query "给异步订单系统引入基于 Redis Stream 的消费组重试机制，要求低延迟且不引入额外中间件" --output ./output_solution
```

### 5. 运行完整测试套件
```bash
pytest tests/ -v
```
