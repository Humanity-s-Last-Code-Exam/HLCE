# ICPC World Finals Problems Model Evaluation Guide

This guide provides instructions on how to evaluate the performance of a language model on problems from the International Collegiate Programming Contest (ICPC) World Finals.

## Table of Contents

- [1. Generate LLM Responses](#1-generate-llm-responses)
- [2. Usage](#2-usage)
  - [2.1 Data Preprocessing](#21-data-preprocessing)
  - [2.2 Evaluation](#22-evaluation)

## 1. Generate LLM Responses

To start, use the prompts provided in the problem files to generate responses from your language model. Example response files can be found in `responses_raw/`. Particularly, arrange the outputs in the following format.
```
[
    {"question_id": "id1", "code_list": ["code1", "code2"]},
    {"question_id": "id2", "code_list": ["code1", "code2"]}
]
```

## 2. Evaluation

To evaluate the performance, navigate to the LiveCodeBench directory and run the evaluation scripts:

- Execute the custom evaluator script:

  ```bash
  python -m lcb_runner.runner.custom_evaluator --custom_output_file your_file.jsonl --timeout 60
  ```

- Calculate the scores based on the evaluation results:

  ```bash
  python -m lcb_runner.evaluation.compute_scores --eval_all_file your_file_codegeneration_output_eval_all.json
  ```


