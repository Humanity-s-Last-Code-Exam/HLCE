# ICPC World Finals Problems Model Evaluation Guide

This guide provides instructions on how to evaluate the performance of a language model on problems from the International Collegiate Programming Contest (ICPC) World Finals.

## Table of Contents

- [1. Generate LLM Responses](#1-generate-llm-responses)
- [2. Usage](#2-usage)
  - [2.1 Data Preprocessing](#21-data-preprocessing)
  - [2.2 Evaluation](#22-evaluation)

## 1. Generate LLM Responses

To start, use the prompts provided in the problem files to generate responses from your language model. Example response files can be found in `responses_raw/`.


## 2. Usage

### 2.1 Data Preprocessing

Before evaluation, you need to preprocess your language model's responses:

- Split and filter the raw JSON Lines file using the following command:

```bash
python split_and_filter.py --raw_icpc_jsonl responses_raw/icpc_deepseek_r1.jsonl --split_icpc_json examples/deepseek_r1 --model deepseek_r1
```

The file split count corresponds to the number of model responses per test case.

- Merge the split files into a complete file ready for evaluation:

  ```bash
  python jsons_filter_merge.py --model deepseek_r1 --n 10
  ```

  An example merged file can be located at: examples/chatgpt-4o-latest/icpc_filter_merge.json

### 2.2 Evaluation

To evaluate the performance, navigate to the LiveCodeBench directory and run the evaluation scripts:

- Execute the custom evaluator script:

  ```bash
  python -m lcb_runner.runner.custom_evaluator --custom_output_file /examples/deepseek_r1/icpc_filter_merge.json --release_version release_v7 --timeout 60
  ```

- Calculate the scores based on the evaluation results:

  ```bash
  python -m lcb_runner.evaluation.compute_scores --eval_all_file /examples/deepseek_r1/icpc_filter_merge_codegeneration_output_eval_all.json
  ```


