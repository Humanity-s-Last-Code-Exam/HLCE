import json
import numpy as np
import argparse
from collections import defaultdict


def pass_at_k(n, c, k):
    if c == 0:  # If no successful attempts, return 0
        return 0.0
    if n - c < k:
        return 1.0
    return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))


def analyze_submissions(data):
    # Define composite problems that need special handling
    composite_problems = {
        "A. Crayfish scrivener (IOI 2012 day 1)": ['A1', 'A2', 'A3', 'A4', 'A5']
        # Add more composite problems and their subtasks here if needed
    }

    # Group submissions by problem
    submissions_by_problem = defaultdict(list)

    for submission in data:
        problem_title = submission['problem_title']
        date = submission['date']
        problem_index = submission['problem_index']

        # Check if the problem is a composite problem
        if date == "IOI 2012 day 1" and problem_index.startswith('A'):
            problem_key = "A. Crayfish scrivener (IOI 2012 day 1)"
        else:
            problem_key = f"{problem_title} ({date})"

        submissions_by_problem[problem_key].append(submission)

    # Overall statistics
    overall_stats = {
        "pass_at_1_sum": 0.0,
        "pass_at_5_sum": 0.0,
        "avg_points_sum": 0.0,
        "problem_count": 0,
        "solved_problems": 0
    }

    problem_stats = defaultdict(
        lambda: {"submissions": 0, "passes": 0, "total_points": 0.0, "pass_rate": 0.0, "valid_submissions": 0})

    # Store detailed information for each problem
    problem_details = {}

    for problem_key, submissions in submissions_by_problem.items():
        overall_stats["problem_count"] += 1
        problem_stats[problem_key]["submissions"] += len(submissions)

        if problem_key in composite_problems:
            # Handle composite problems
            sub_tasks = composite_problems[problem_key]
            # Sort by original_record_id
            sorted_submissions = sorted(submissions, key=lambda x: x.get('original_record_id', 0))

            attempts = []
            current_attempt = defaultdict(float)
            required_sub_tasks = set(sub_tasks)

            for sub in sorted_submissions:
                subtask = sub['problem_index']
                if subtask not in sub_tasks:
                    continue  # Skip non-target subtasks
                if sub.get('verdict') == "Compilation error" or sub.get('points') is None:
                    points = 0.0
                else:
                    points = float(sub['points'])
                current_attempt[subtask] = points

                if set(current_attempt.keys()) == required_sub_tasks:
                    # Complete one attempt
                    total_points = sum(current_attempt.values())
                    attempts.append(total_points)
                    current_attempt = defaultdict(float)  # Reset for next attempt

            # Calculate pass@1 and avg_points
            n = len(attempts)  # Total number of attempts
            c = sum(1 for total in attempts if total == 100.0)  # Number of correct attempts

            # Use pass_at_k function to calculate pass@1
            pass_at_1_p = pass_at_k(n, c, 1) if n > 0 else 0.0
            pass_at_5_p = pass_at_k(n, c, 5) if n > 0 else 0.0

            overall_stats["pass_at_1_sum"] += pass_at_1_p
            overall_stats["pass_at_5_sum"] += pass_at_5_p
            problem_stats[problem_key]["passes"] += c
            problem_stats[problem_key]["pass_rate"] = pass_at_1_p

            total_points_sum = sum(attempts)
            problem_stats[problem_key]["total_points"] += total_points_sum
            problem_stats[problem_key]["valid_submissions"] += n

            # Calculate average score for this problem
            avg_points_p = total_points_sum / n if n > 0 else 0.0
            problem_details[problem_key] = {
                "pass@1": pass_at_1_p,
                "avg_points": avg_points_p,
                "total_attempts": n,
                "correct_attempts": c,
                "is_solved": c > 0,
                "attempts": attempts
            }
            overall_stats["avg_points_sum"] += avg_points_p  # Accumulate average score

            if c > 0:
                overall_stats["solved_problems"] += 1
        else:
            # Handle regular problems
            valid_submissions = []
            for sub in submissions:
                if sub.get('verdict') == "Compilation error" or sub.get('points') is None:
                    # Count compilation errors as attempts with score 0
                    valid_submissions.append(0.0)
                else:
                    points = float(sub['points'])
                    valid_submissions.append(points)

            n = len(valid_submissions)  # Total number of attempts
            c = sum(1 for points in valid_submissions if points == 100.0)  # Number of correct attempts

            # Use pass_at_k function to calculate pass@1
            pass_at_1_p = pass_at_k(n, c, 1) if n > 0 else 0.0
            pass_at_5_p = pass_at_k(n, c, 5) if n > 0 else 0.0

            overall_stats["pass_at_1_sum"] += pass_at_1_p
            overall_stats["pass_at_5_sum"] += pass_at_5_p
            problem_stats[problem_key]["passes"] += c
            problem_stats[problem_key]["pass_rate"] = pass_at_1_p

            total_points = sum(valid_submissions)
            problem_stats[problem_key]["total_points"] += total_points
            problem_stats[problem_key]["valid_submissions"] += n

            # Calculate average score for this problem
            avg_points_p = total_points / n if n > 0 else 0.0
            problem_details[problem_key] = {
                "pass@1": pass_at_1_p,
                "pass@5": pass_at_5_p,
                "avg_points": avg_points_p,
                "total_attempts": n,
                "correct_attempts": c,
                "is_solved": c > 0,
                # "attempts": attempts  # or valid_submissions, depending on whether it's a composite or regular problem
            }

            overall_stats["avg_points_sum"] += avg_points_p  # Accumulate average score

            if c > 0:
                overall_stats["solved_problems"] += 1

    # Calculate final statistics
    pass_at_1 = overall_stats["pass_at_1_sum"] / overall_stats["problem_count"] if overall_stats[
                                                                                       "problem_count"] > 0 else 0.0
    pass_at_5 = overall_stats["pass_at_5_sum"] / overall_stats["problem_count"] if overall_stats[
                                                                                       "problem_count"] > 0 else 0.0

    avg_points = overall_stats["avg_points_sum"] / overall_stats["problem_count"] if overall_stats[
                                                                                         "problem_count"] > 0 else 0.0

    final_stats = {
        "pass@1": pass_at_1,
        "pass@5": pass_at_5,
        "avg_points": avg_points,
        "total_problems": overall_stats["problem_count"],
        "solved_problems": overall_stats["solved_problems"],
        "problem_details": problem_details
    }

    return final_stats, problem_stats


def main():
    parser = argparse.ArgumentParser(description="Analyze IOI problem submissions")
    parser.add_argument("--input", "-i", type=str,
                        default='./ioi_scores/ioi_contest_problems_chatgpt-4o-latest_score_merge.jsonl',
                        help="Input JSONL file with submission data")
    parser.add_argument("--output", "-o", type=str,
                        default='results.jsonl',
                        help="Output JSONL file for results")
    args = parser.parse_args()

    # Read data
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Analyze data
    overall_stats, problem_stats = analyze_submissions(data)

    # Output overall performance
    print("=== Overall Performance ===")
    print(f"Pass@1: {overall_stats['pass@1']:.4f}")
    print(f"Pass@5: {overall_stats['pass@5']:.4f}")
    print(f"Avg Points: {overall_stats['avg_points']:.2f}")
    print(f"Solved/Total: {overall_stats['solved_problems']}/{overall_stats['total_problems']}")
    print("-" * 65)

    # Output problem statistics
    print("\n=== Problem Statistics ===")
    print(f"{'Problem':<60} {'Pass Rate':<10} {'Avg Points':<15} {'Submissions'}")
    print("-" * 100)

    for problem, stats in sorted(problem_stats.items()):
        pass_rate = stats["pass_rate"]
        # Calculate average points using valid submissions
        avg_points = stats["total_points"] / stats["valid_submissions"] if stats["valid_submissions"] > 0 else 0.0
        print(f"{problem:<60} {pass_rate:.4f}    {avg_points:.2f}         {stats['submissions']}")

    # Save results to JSONL file
    results = []

    # Add overall statistics
    result = {
        "type": "overall_stats",
        "pass@1": overall_stats["pass@1"],
        "pass@5": overall_stats["pass@5"],
        "avg_points": overall_stats["avg_points"],
        "total_problems": overall_stats["total_problems"],
        "solved_problems": overall_stats["solved_problems"],
        "problem_details": overall_stats["problem_details"]
    }
    results.append(result)

    # Add problem statistics
    for problem, stats in problem_stats.items():
        result = {
            "type": "problem_stats",
            "problem": problem,
            "pass_rate": stats["pass_rate"],
            "avg_points": stats["total_points"] / stats["valid_submissions"] if stats["valid_submissions"] > 0 else 0.0,
            "submissions": stats["submissions"],
            "valid_submissions": stats["valid_submissions"],
            "passes": stats["passes"],
            "total_points": stats["total_points"]
        }
        results.append(result)

    # Debug output
    for problem, details in overall_stats["problem_details"].items():
        n = details.get("total_attempts", 0)
        c = details.get("correct_attempts", 0)
        print(
            f"Problem: {problem}, Attempts: {n}, Correct: {c}, pass@1: {details.get('pass@1', 0)}, pass@5: {details.get('pass@5', 0)}")

    # Write to JSONL file
    with open(args.output, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result) + '\n')

    print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()


# python script_name.py --input path/to/your/input_file.jsonl --output path/to/your/output_file.jsonl