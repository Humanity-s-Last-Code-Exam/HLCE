import os
from pathlib import Path
import json
import argparse


def main(model, N):
    # 初始化一个字典用于存储合并后的数据
    merged_data = {}
    print(f"Processing model: {model}")
    print(f"{'=' * 40}")

    # 定义输出文件路径
    output_file = Path(f"examples/{model}/icpc_filter_merge.json")

    for iter_num in N:
        print(f"Running iteration: {iter_num}")

        # 定义输入文件路径
        icpc_filter_path = Path(f"examples/{model}/{iter_num}/icpc_filter.jsonl")
        # 检查输入文件是否存在
        if not icpc_filter_path.exists():
            print(f"Warning: Scores file not found: {icpc_filter_path}")
            continue
        try:
            # 打开并读取整个 JSON 文件
            with open(icpc_filter_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)  # 加载整个文件为一个 JSON 数组
                except json.JSONDecodeError as e:
                    print(f"Invalid JSON format in file {icpc_filter_path}. Error: {e}")
                    continue

                for record in data:
                    question_id = record.get("question_id")
                    code_list = record.get("code_list", [])

                    if question_id in merged_data:
                        # 如果已存在相同的 question_title，拼接 code_list
                        merged_data[question_id]["code_list"].extend(code_list)
                    else:
                        # 如果是第一次遇到该 question_title，直接添加记录
                        merged_data[question_id] = record.copy()  # 使用 copy 防止引用问题
        except Exception as e:
            print(f"Error processing file {icpc_filter_path}: {e}")
        continue

    # 将字典转换为列表形式
    result = list(merged_data.values())

    # 将结果写入输出文件
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)  # 写入 JSON 格式
        print(f"合并完成，结果已保存到 {output_file}")
    except Exception as e:
        print(f"Error writing to output file {output_file}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="合并多个 JSONL 文件为一个 JSON 文件")
    parser.add_argument("--model", nargs='+', required=True, help="模型名称")
    parser.add_argument("--n", type=int, default=10, help="迭代次数，默认是 10")
    args = parser.parse_args()

    main(args.models, args.n)
