import json
import os
import argparse
from tqdm import tqdm
import glob


def merge_jsonl_files_in_directory(directory, output_file, pattern="*.jsonl"):
    """
    Merge all JSONL files in a directory into a single file

    Parameters:
    directory (str): Path to the directory containing JSONL files
    output_file (str): Path to the output JSONL file
    pattern (str): Pattern to match JSONL files
    """
    try:
        # Get all matching JSONL files in the directory
        file_paths = glob.glob(os.path.join(directory, pattern))

        if not file_paths:
            print(f"No files matching {pattern} found in directory {directory}")
            return False

        # Count total lines for progress display
        total_lines = 0
        for file_path in file_paths:
            with open(file_path, 'r', encoding='utf-8') as f:
                total_lines += sum(1 for _ in f)

        # Merge data
        with open(output_file, 'w', encoding='utf-8') as out:
            pbar = tqdm(total=total_lines, desc="Merging JSONL files")
            for file_path in file_paths:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line:  # Skip empty lines
                                out.write(line + '\n')
                                pbar.update(1)
                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")
            pbar.close()

        print(f"Successfully merged files to {output_file}")
        return True

    except Exception as e:
        print(f"Error merging files: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge JSONL files in a directory")
    parser.add_argument("--directory", "-d", type=str, default="./ioi_scores",
                        help="Directory containing JSONL files")
    parser.add_argument("--output", "-o", type=str,
                        default="./ioi_scores/merged_output.jsonl",
                        help="Path to the output JSONL file")
    parser.add_argument("--pattern", "-p", type=str, default="*score*.jsonl",
                        help="Pattern to match JSONL files")

    args = parser.parse_args()

    merge_jsonl_files_in_directory(args.directory, args.output, args.pattern)


# python script.py --directory ./ioi_scores --output ./ioi_scores/merged_output.jsonl --pattern "*score*.jsonl"