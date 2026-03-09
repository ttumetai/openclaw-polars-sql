<<<<<<< HEAD
# 📊 OpenClaw Polars SQL Agent (本地数据分析沙盒)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Polars](https://img.shields.io/badge/Polars-Fast_DataFrames-bluewithyellow)](https://pola.rs/)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Native_Skill-brightgreen)](https://github.com/openclaw/openclaw)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📖 项目简介

本项目是为 OpenClaw 框架开发的高级原生技能 (Native Skill)。它赋予了 LLM Agent 直接在其运行环境中“感知、查询、分析和可视化”本地海量结构化数据（CSV/Parquet）的能力。

**为什么不直接让大模型写 Python 脚本执行？**
传统的 Code Interpreter 方案存在极高的沙盒越权风险和运行不稳定性。本项目创新性地采用了 **“降维与沙盒化”** 策略：
1. **绝对安全**：基于 Polars `SQLContext` 构建纯内存只读环境，仅支持 `SELECT` 语法，从物理层面杜绝了 LLM 产生幻觉执行 `DROP/DELETE` 等破坏性操作的可能。
2. **极速性能**：抛弃了传统的 Pandas 或 SQLite 导入方案，底层依托 Rust 编写的 Polars 引擎，实现 Zero-copy (零拷贝) 的 GB 级数据毫秒级查询。
3. **无状态工作流**：通过精准设计的 Prompt (SKILL.md) 约束 LLM，将其复杂的分析任务拆解为标准的 SOP (寻找文件 -> 解析结构 -> 验证逻辑 -> 导出/可视化)，极大降低了上下文消耗和出错率。

## ✨ 核心动作流 (Toolchain Actions)

本项目暴露了一个统一的路由脚本，包含 5 个原子化 Action，供大模型自由组合编排：

* 🔍 **`list_files` (勘察现场)**：让 Agent 能够主动扫描 Workspace 目录，获取文件的绝对路径和大小，摆脱对用户提供精确路径的依赖。
* 📋 **`get_schema` (结构解析)**：在编写 SQL 前强制获取表字段与类型，彻底解决大模型“凭空捏造列名”的经典幻觉。
* ⚡ **`preview_sql` (试运行校验)**：执行 SQL 并带截断保护（防止 Token 爆炸），为 Agent 提供“自我纠错 (Self-Correction)”的观察窗口。
* 💾 **`save_data` (结果落盘)**：将经过复杂聚合过滤后的干净数据，持久化导出为新的 CSV/Parquet 文件。
* 📈 **`draw_chart` (动态可视化)**：基于 `**kwargs` 动态解包技术，允许 LLM 通过 JSON 注入高度自定义的样式（如颜色、线宽），生成统计图表并保存。

## 🛠️ 技术栈

* **核心引擎**: Python 3.11+
* **数据处理**: [Polars](https://pola.rs/) (Fast OLAP query engine)
* **可视化**: Matplotlib (Agg backend for headless environments)
* **交互协议**: 标准化 JSON 标出输出 + OpenClaw SKILL.md Schema定义

## 🚀 快速部署

**1. 进入 OpenClaw 的技能目录**
```bash
cd ~/.openclaw/workspace/skills/
git clone https://github.com/ttumetai/openclaw-polars-sql.git
```

**2. 安装核心依赖 (根据你的部署方式选择)**

**情况 A：使用 Docker 部署的 OpenClaw**
由于该技能需要运行在 OpenClaw 容器内，请先进入容器再安装依赖：
```bash
docker exec -u root -it openclaw bash
pip3 install polars matplotlib --break-system-packages
exit
```

**情况 B：在本机直接运行的 OpenClaw**
直接在你运行 OpenClaw 的本地终端 / Python 环境中安装即可：
```bash
pip3 install polars matplotlib
```

**3. 重启网关以挂载技能**

如果是 Docker 部署：
```bash
docker restart openclaw
```
如果是本机部署：
直接在终端使用 `Ctrl+C` 中断当前的 OpenClaw 进程，然后重新执行启动命令即可。

## 💬 经典对话示例 (Prompt Examples)

在飞书或命令行界面中，你可以这样直接向 Agent 下达高优指令：

> **用户**："我刚才传了一个 `sales_2025.csv` 到你的工作区，请你帮我找出销售额排名前 10 的商品品类，然后把结果画成一个猛男粉色、柱子比较细的柱状图发给我。"

**Agent 在后台的自主思考链路 (ReAct)：**
1. *Action*: `list_files` -> 找到 `sales_2025.csv` 的真实路径。
2. *Action*: `get_schema` -> 发现包含 `category` 和 `amount` 列。
3. *Action*: `preview_sql` -> 试写 `SELECT category, SUM(amount)...` 并验证成功。
4. *Action*: `draw_chart` -> 注入样式 `{"color": "pink", "width": 0.3}`，生成最终报表。

## 📁 目录结构

```text
openclaw-polars-sql/
├── SKILL.md                 # OpenClaw 技能定义与 Agent 工作流系统提示词
├── README.md                # 项目文档
├── scripts/
│   └── agent.py             # 核心业务逻辑与 Action 路由分发器
└── examples/
    └── mock_data.csv        # 用于测试的样例数据集
```

## 📄 License
MIT License
