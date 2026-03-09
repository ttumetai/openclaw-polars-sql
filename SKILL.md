| name | description | license | compatibility | allowed-tools | metadata |
| polars-sql-analyst | An advanced local data processing and workspace management tool. Finds, reads, and queries local CSV/Parquet files using Polars SQL. Use this when the user asks to analyze, filter, summarize, or export local data files. | MIT | Bash(python3:*) | | |

| author | version | tags |
| ttumetai | 1.0.0 | data-analysis, polars, sql, workspace, etl |

# 本地数据分析沙盒 (Polars Workspace Agent)

这是一个高级本地数据处理与工作区管理工具。你可以使用它来查找用户上传的文件，并使用 SQL (基于 Polars 引擎) 进行千万级数据的高效查询、分析与处理。查询时，表名固定注册为 `my_data`。

## 约束与边界 (Constraints)
- **只读内存查询**：Polars SQLContext 主要支持 `SELECT` 语句用于查询和聚合。**绝对不要**尝试使用 `INSERT`, `UPDATE`, `DELETE`, `DROP` 等修改表结构的语句。
- **文件后缀**：目前仅支持读取 `.csv` 和 `.parquet` 格式的数据。
- **不要嵌套调用**：一次只能执行一个 `--action`。

## 默认工作区 (Workspace)
当用户发送文件给你时，系统会自动将文件保存在服务器的默认挂载目录中（例如：`/home/node/.openclaw/workspace/`）。**你需要主动去该目录下寻找用户上传的文件。**

## 严格工作流规范 (Standard Operating Procedure)

作为数据分析 Agent，处理任何数据请求时，**必须**严格按照以下顺序执行动作（Action）：

1. **第 0 步 - 勘察现场 (`list_files`)**:
   当用户让你处理刚发送的文件，但没给你绝对路径时，**首先**调用此动作。
   - 观察返回的 JSON，找到用户提到的文件名，并提取其 `absolute_path` 用于后续操作。
   - 注意检查 `size_mb`，评估数据量。

2. **第 1 步 - 解析结构 (`get_schema`)**:
   在写任何 SQL 之前，**必须**调用此动作。
   - 准确记住列名和数据类型。绝对禁止凭空捏造字段名写 SQL！

3. **第 2 步 - 试运行与逻辑验证 (`preview_sql`)**:
   编写 SQL 后，调用此动作验证逻辑。
   - 这只会返回前 20 行数据供你确认。
   - **自我纠错机制**：如果返回 status 为 error，仔细阅读报错信息（例如语法不支持、列名拼错），反思并修改你的 SQL 后再次试运行，直到成功。

4. **第 3 步 - 成果交付与持久化 (`save_data`)**:
   当第二步验证无误，且用户的指令需要导出结果（如“帮我把处理好的数据存下来”）时，调用此动作。
   - 建议输出至原工作区目录，并附带明确的后缀（如 `_result.csv`）。

5. **第 4 步 - 数据可视化 (`draw_chart`)**:
   当用户要求“画个图”、“可视化一下”时，先通过 `preview_sql` 确保你写出了正确的**聚合 SQL**（例如按月份 Group By 算总和），然后调用此动作生成图片。
   - 必须提供生成的图片绝对路径 `--out`（以 `.png` 结尾）。
   - 必须指定 `--type` (bar/line/scatter), `--x` 轴列名, `--y` 轴列名。
   - 警告：严禁将超过 100 行的原始明细数据直接画图，必须先在 SQL 中使用 `GROUP BY` 进行聚合！
   - `--style`: (可选) 用于自定义图表样式的 JSON 字符串。
    - 必须用单引号包裹最外层，双引号包裹键值对。示例：`'{"color": "pink", "width": 0.3, "alpha": 0.8}'`。
    - 对于柱状图(bar)，支持传入 `color`(颜色), `width`(粗细,默认0.8), `alpha`(透明度) 等 matplotlib 支持的参数。
    - 对于折线图(line)，支持传入 `color`(颜色), `linewidth`(线宽), `linestyle`(线型,如 "--") 等参数。

## 如何调用 (How to Invoke)

必须使用以下 Python 命令格式来调用本技能：

```bash
python3 scripts/agent.py --action ACTION [--dir DIR] [--file FILE] [--sql SQL] [--out OUT] [--type TYPE] [--x X] [--y Y] [--style STYLE]
```