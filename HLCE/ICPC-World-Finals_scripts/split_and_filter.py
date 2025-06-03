import json
import os
import argparse
import subprocess


def icpc_jsonl_split(raw_icpc_jsonl, split_icpc_json):
    try:
        # 读取并解析输入文件
        with open(raw_icpc_jsonl, "r", encoding="utf-8") as f:
            data = [json.loads(line) for line in f]

        # 处理每条数据
        for item in data:
            # 移除不需要的字段
            item.pop('test_cases', None)

            # 处理每个响应
            for response_idx, response in enumerate(item['code_responses'][:10]):
                # 创建输出数据副本以避免修改原数据
                output_item = item.copy()
                output_item['response'] = response

                # 准备输出目录和文件路径
                output_subdir = os.path.join(split_icpc_json, str(response_idx))
                os.makedirs(output_subdir, exist_ok=True)
                output_file = os.path.join(output_subdir, 'icpc.json')

                # 写入输出文件
                with open(output_file, "a", encoding="utf-8") as f:
                    json.dump(output_item, f, ensure_ascii=False)
                    f.write("\n")  # 添加换行符使文件成为JSONL格式
        print("Split icpc jsonl success!")

    except FileNotFoundError:
        print(f"Error: Input file not found at {raw_icpc_jsonl}")
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON data: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def icpc_json_filter(model):
    # 遍历每个模型并运行命令
    for iter in range(10):
        # 构造输出文件路径
        input_file = f"examples/{model}/{iter}/icpc.json"

        # 构造命令
        command = [
            "python", "filter_generated_results.py",
            "--input_file", input_file,
            "--benchmark", "icpc",
            "--fix_exit",
        ]

        # 执行命令
        try:
            subprocess.run(command, check=True)
            print("Filter icpc jsonl success!")
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while processing model : {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some JSON Lines files.")
    parser.add_argument("--raw_icpc_jsonl", type=str, required=True, help="Path to the raw icpc JSON Lines file")
    parser.add_argument("--split_icpc_json", type=str, required=True,
                        help="Directory where split icpc JSON will be saved")
    parser.add_argument("--model", type=str, required=True, help="Model name")
    args = parser.parse_args()

    icpc_jsonl_split(args.raw_icpc_jsonl, args.split_icpc_json)
    icpc_json_filter(args.model)
