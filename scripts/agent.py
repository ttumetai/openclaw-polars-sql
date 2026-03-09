import polars as pl
import argparse
import json
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

def get_schema(file_path: str):
    """动作 1：读取文件并返回表结构，供 LLM 了解数据"""
    try:
        # 使用 scan_csv 延迟加载，极速获取 schema，不占内存
        df = pl.scan_csv(file_path)
        schema_info = {name: str(dtype) for name, dtype in df.schema.items()}
        return {"status": "success", "action": "get_schema", "schema": schema_info}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def preview_sql(file_path: str, sql_query: str, limit: int = 20):
    """动作 2：执行 SQL 并返回预览数据，供 LLM 验证逻辑"""
    try:
        df = pl.read_csv(file_path)
        ctx = pl.SQLContext()
        ctx.register("my_data", df)
        
        # 执行查询并截断结果防 Token 爆炸
        result_df = ctx.execute(sql_query).collect()
        preview_data = result_df.head(limit).to_dicts()
        
        return {
            "status": "success", 
            "action": "preview_sql",
            "total_rows": result_df.height,
            "preview_data": preview_data
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def save_data(file_path: str, sql_query: str, output_path: str):
    """动作 3：执行 SQL 并将结果保存为新文件"""
    try:
        df = pl.read_csv(file_path)
        ctx = pl.SQLContext()
        ctx.register("my_data", df)
        
        result_df = ctx.execute(sql_query).collect()
        # 将结果持久化为 CSV 或 Parquet
        if output_path.endswith('.parquet'):
            result_df.write_parquet(output_path)
        else:
            result_df.write_csv(output_path)
            
        return {
            "status": "success", 
            "action": "save_data",
            "message": f"成功将 {result_df.height} 行数据保存至 {output_path}"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def list_files(directory: str):
    """动作 0：列出指定工作区目录下的所有文件，供 LLM 寻找目标数据"""
    try:
        p = Path(directory)
        if not p.exists() or not p.is_dir():
            return {"status": "error", "error": f"目录 {directory} 不存在。"}
        
        files_info = []
        for item in p.iterdir():
            if item.is_file():
                # 顺手把文件大小转成 MB，并附带后缀名，帮大模型更好地做判断
                size_mb = round(item.stat().st_size / (1024 * 1024), 3)
                files_info.append({
                    "name": item.name,
                    "absolute_path": str(item.resolve()),
                    "size_mb": size_mb,
                    "extension": item.suffix
                })
                
        return {
            "status": "success", 
            "action": "list_files", 
            "directory": str(p.resolve()),
            "total_files": len(files_info),
            "files": files_info
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
    
def draw_chart(file_path: str, sql_query: str, out_path: str, chart_type: str, x_col: str, y_col: str, style_str: str = None):
    """执行 SQL 并利用 matplotlib 绘图，支持通过 JSON 动态注入样式"""
    try:
        # 1. 使用 Polars 执行 SQL
        df = pl.read_csv(file_path)
        ctx = pl.SQLContext()
        ctx.register("my_data", df)
        result_df = ctx.execute(sql_query).collect()
        
        if result_df.height > 100:
            return {"status": "error", "error": f"数据量过大 ({result_df.height} 行)，请在 SQL 中使用 GROUP BY 或 LIMIT。"}
            
        x_data = result_df[x_col].to_list()
        y_data = result_df[y_col].to_list()

        # 2. 解析大模型传过来的样式 JSON
        style_kwargs = {}
        if style_str:
            try:
                style_kwargs = json.loads(style_str)
            except json.JSONDecodeError as e:
                # 容错机制：解析失败就用空字典，不阻断程序运行
                print(f"警告: 样式 JSON 解析失败 ({e})，将使用默认样式。传入的字符串为: {style_str}", file=sys.stderr)

        # 3. 开始绘图
        plt.figure(figsize=(10, 6))
        
        # 使用 **style_kwargs 动态解包注入样式！
        if chart_type == "bar":
            plt.bar(x_data, y_data, **style_kwargs)
        elif chart_type == "line":
            plt.plot(x_data, y_data, **style_kwargs)
        elif chart_type == "scatter":
            plt.scatter(x_data, y_data, **style_kwargs)
        else:
            return {"status": "error", "error": f"不支持的图表类型: {chart_type}"}

        plt.title(f"{y_col} by {x_col}")
        plt.xlabel(x_col)
        plt.ylabel(y_col)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # 4. 保存图片
        plt.savefig(out_path, dpi=150)
        plt.close()
        
        return {
            "status": "success", 
            "action": "draw_chart",
            "message": f"成功生成 {chart_type} 图表，已保存至 {out_path}",
            "applied_styles": style_kwargs # 把生效的样式返回给大模型看，方便它确认
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Polars SQL 数据处理与工作区工具链")
    parser.add_argument("--action", required=True, choices=["list_files", "get_schema", "preview_sql", "save_data"], help="要执行的操作")
    parser.add_argument("--dir", help="工作区目录路径 (仅针对 list_files)")
    parser.add_argument("--file", help="源数据文件路径")
    parser.add_argument("--sql", help="要执行的 SQL 语句 (针对 preview_sql 和 save_data)")
    parser.add_argument("--out", help="输出文件路径 (仅针对 save_data)")
    # 绘图专属参数
    parser.add_argument("--type", help="图表类型: bar, line, scatter")
    parser.add_argument("--x", help="X 轴列名")
    parser.add_argument("--y", help="Y 轴列名")
    # 新增的 style 参数
    parser.add_argument("--style", help="自定义样式的 JSON 字符串 (例如 '{\"color\": \"red\", \"width\": 0.5}')")
    
    args = parser.parse_args()
    
    # 路由分发
    if args.action == "list_files":
        if not args.dir:
            output = {"status": "error", "error": "list_files 必须提供 --dir 参数"}
        else:
            output = list_files(args.dir)
    elif args.action == "get_schema":
        output = get_schema(args.file)
    elif args.action == "preview_sql":
        if not args.sql:
            output = {"status": "error", "error": "preview_sql 必须提供 --sql 参数"}
        else:
            output = preview_sql(args.file, args.sql)
    elif args.action == "save_data":
        if not args.sql or not args.out:
            output = {"status": "error", "error": "save_data 必须提供 --sql 和 --out 参数"}
        else:
            output = save_data(args.file, args.sql, args.out)
    elif args.action == "draw_chart":
        if not all([args.sql, args.out, args.type, args.x, args.y]):
            output = {"status": "error", "error": "draw_chart 必须提供 --sql, --out, --type, --x, --y 参数"}
        else:
            # 把 args.style 传进去
            output = draw_chart(args.file, args.sql, args.out, args.type, args.x, args.y, args.style)

    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    main()