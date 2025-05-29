To evaluate model performance on IOI (International Olympiad in Informatics) problems, follow these steps:

## 1. Create a Codeforces Account

Register an account on [Codeforces](https://codeforces.com/), which is required for submitting solutions.

## 2. Generate LLM Responses

Use the prompt field from the problem files to obtain responses from your language model.

## 3. Split Response Files

Due to Codeforces' submission limit (250 submissions per account per day), you'll need to split your responses:

- For 89 problems with 5 responses each (445 total): Split into 2 files
- For 89 problems with 10 responses each (890 total): Split into 4 files using 2 accounts

Example split files can be found in `example/ioi_contest_problems_gemini-2.5-pro-exp-03-25_filter_part2.jsonl`

## 4. Submit Solutions to IOI

Use the submission script to send your solutions:

```bash
python submit_to_ioi.py --input ./examples/ioi_contest_problems_gemini-2.5-pro-exp-03-25_filter_part2.jsonl --output ./submit_results/ioi_contest_problems_gemini-2.5-pro-exp-03-25_filter_part2_submission.jsonl
```

This will:
- Open a Codeforces login page
- Automatically submit solutions after login
- Record submission IDs for later evaluation
- Take approximately 2 hours per file (submissions must be processed serially)

## 5. Retrieve Problem Scores

Fetch scores for each submission using the recorded submission IDs:

```bash
python get_ioi_result.py --input ./submit_results/ioi_contest_problems_gemini-2.5-pro-exp-03-25_filter_part2_submission.jsonl --output ./ioi_scores/ioi_contest_problems_gemini-2.5-pro-exp-03-25_filter_part2_score.jsonl
```

This process takes approximately 30 minutes per file.

## 6. Merge Score Files

Combine all score files into a single JSONL file:

```bash
python merge_ioi_results.py --directory ./ioi_scores --output ./ioi_scores/merged_output.jsonl --pattern "*score*.jsonl"
```

## 7. Calculate Final Metrics

Compute pass@1 and pass@5 metrics from the merged scores:

```bash
python compute_ioi_final_results.py --input ./ioi_scores/merged_output.jsonl --output path/to/your/output_file.jsonl
```

This will generate the final performance metrics for your model on the IOI benchmark.

