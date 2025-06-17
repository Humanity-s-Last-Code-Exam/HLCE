# ICPC World Finals Problems Model Evaluation Guide

This guide provides instructions on how to evaluate the performance of a language model on problems from the International Collegiate Programming Contest (ICPC) World Finals.


## 1. Generate LLM Responses

To start, use the prompts provided in the [problem files](https://huggingface.co/datasets/HumanLastCodeExam/icpc-world-finals) to generate responses from your language model. Particularly, arrange the outputs in the following format. An example is in the examples/icpc_filter_merge.json file, with the required fields structured as follows:
```
[
    {
        "question_title": "xxx",
        "platform": "xxx",
        "question_id": "xxx",
        "question_content": "xxx",
        "code_list": ["code1", "code2"]
    },
    {
        "question_title": "xxx",
        "platform": "xxx",
        "question_id": "xxx",
        "question_content": "xxxt",
        "code_list": ["code1", "code2"]
    }
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


