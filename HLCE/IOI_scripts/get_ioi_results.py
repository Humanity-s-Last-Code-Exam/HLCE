import os
import json
import time
import random
import argparse
import datetime
from tqdm import tqdm
from DrissionPage import ChromiumPage
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse


def random_sleep(min_sec=1, max_sec=3):
    """Random wait for a period of time"""
    sleep_time = random.uniform(min_sec, max_sec)
    time.sleep(sleep_time)


def is_logged_in(page):
    """Check if currently logged into ioi.contest.codeforces.com"""
    page.get('https://ioi.contest.codeforces.com/')
    html = page.html
    soup = BeautifulSoup(html, 'html.parser')
    user_info = soup.find('a', href=lambda href: href and '/profile/' in href)
    return bool(user_info)


def safe_get_text(element):
    """Safely get text from an element that might be None"""
    if element is None:
        return "Unknown"
    return element.text.strip() if hasattr(element, 'text') else "Unknown"


def extract_submission_details(html_content, submission_id):
    """Extract submission details from HTML content"""
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the submission row with the given ID
    submission_row = soup.find('tr', attrs={'data-submission-id': submission_id})

    if not submission_row:
        return {
            "submission_id": submission_id,
            "status": "Not found",
            "error": "Submission row not found in the HTML"
        }

    # Extract submission time
    time_cell = submission_row.find('td', class_='status-small')
    time_span = time_cell.find('span', class_='format-time') if time_cell else None
    submission_time = safe_get_text(time_span)

    # Extract user info
    user_cell = submission_row.find('td', class_='status-party-cell')
    user_link = user_cell.find('a') if user_cell else None
    username = safe_get_text(user_link)

    # Extract problem info
    problem_cells = submission_row.find_all('td', class_='status-small')
    problem_cell = problem_cells[1] if len(problem_cells) > 1 else None
    problem_link = problem_cell.find('a') if problem_cell else None
    problem_name = safe_get_text(problem_link)
    problem_url = problem_link['href'] if problem_link and 'href' in problem_link.attrs else "Unknown"

    # Extract language
    td_cells = submission_row.find_all('td')
    language_cell = td_cells[4] if len(td_cells) > 4 else None
    language = safe_get_text(language_cell)

    # Extract verdict - improved to better handle different verdict types
    verdict_cell = submission_row.find('td', class_='status-verdict-cell')

    # First try to get the verdict from the submissionVerdictWrapper span
    verdict_span = verdict_cell.find('span', class_='submissionVerdictWrapper') if verdict_cell else None
    verdict = safe_get_text(verdict_span)

    # Check if we have a verdict attribute that might help identify the type
    verdict_type = verdict_span.get('submissionVerdict') if verdict_span else None

    # Extract points if available
    points = None
    if verdict:
        points_match = re.search(r'(\d+(?:\.\d+)?)\s*points', verdict)
        if points_match:
            try:
                points = float(points_match.group(1))
            except (ValueError, TypeError):
                points = None

    result = {
        "submission_id": submission_id,
        "status": "Found",
        "submission_time": submission_time,
        "username": username,
        "problem": problem_name,
        "problem_url": problem_url,
        "language": language,
        "verdict": verdict,
        "verdict_type": verdict_type,
        "points": points
    }

    # If we have a verdict_type, make sure it's reflected in the verdict
    if verdict_type and verdict == "Unknown":
        if verdict_type == "COMPILATION_ERROR":
            result["verdict"] = "Compilation error"
        elif verdict_type == "RUNTIME_ERROR":
            result["verdict"] = "Runtime error"
        elif verdict_type == "WRONG_ANSWER":
            result["verdict"] = "Wrong answer"
        elif verdict_type == "TIME_LIMIT_EXCEEDED":
            result["verdict"] = "Time limit exceeded"
        elif verdict_type == "MEMORY_LIMIT_EXCEEDED":
            result["verdict"] = "Memory limit exceeded"
        elif verdict_type == "OK":
            result["verdict"] = "Accepted"
        elif verdict_type == "PARTIAL":
            result["verdict"] = "Partial result"

    return result


def get_submission_result(page, submission_id, group_id=None, contest_id=None):
    """Get submission result by ID"""
    print(f"Fetching result for submission ID: {submission_id}")

    if group_id and contest_id:
        # If we have group and contest IDs, go to the my submissions page
        url = f'https://ioi.contest.codeforces.com/group/{group_id}/contest/{contest_id}/my'
    else:
        # Otherwise, try to find the submission in the general submissions page
        url = 'https://ioi.contest.codeforces.com/submissions'

    page.get(url)
    random_sleep(2, 3)

    # Try to find the submission on the current page
    result = extract_submission_details(page.html, submission_id)

    # If not found and we have group/contest IDs, try the submission URL directly
    if result.get("status") == "Not found" and group_id and contest_id:
        direct_url = f'https://ioi.contest.codeforces.com/group/{group_id}/contest/{contest_id}/submission/{submission_id}'
        print(f"Submission not found on list page. Trying direct URL: {direct_url}")
        page.get(direct_url)
        random_sleep(2, 3)

        # Extract from the submission page
        soup = BeautifulSoup(page.html, 'html.parser')

        # Try multiple ways to find the verdict
        verdict_div = soup.find('div', class_='verdict-format-judged')

        if verdict_div:
            verdict_text = safe_get_text(verdict_div)
            result = {
                "submission_id": submission_id,
                "verdict": verdict_text,
                "status": "Found",
                "source": "direct_url"
            }

            # Extract points if available
            points_match = re.search(r'(\d+(?:\.\d+)?)\s*points', verdict_text)
            if points_match:
                try:
                    result["points"] = float(points_match.group(1))
                except (ValueError, TypeError):
                    pass
        else:
            # Check for compilation error
            compilation_error = soup.find('pre', class_='error')
            if compilation_error:
                result = {
                    "submission_id": submission_id,
                    "verdict": "Compilation error",
                    "verdict_type": "COMPILATION_ERROR",
                    "compilation_message": safe_get_text(compilation_error),
                    "status": "Found",
                    "source": "direct_url_compilation_error"
                }
            else:
                # Try to find any verdict information on the page
                verdict_elements = soup.find_all(['div', 'span'], class_=lambda c: c and (
                            'verdict' in c.lower() or 'status' in c.lower()))
                if verdict_elements:
                    verdict_text = safe_get_text(verdict_elements[0])
                    result = {
                        "submission_id": submission_id,
                        "verdict": verdict_text,
                        "status": "Found",
                        "source": "direct_url_alternative"
                    }

    return result


def save_results(results, output_file="submission_results.json"):
    """Save submission results to JSON file"""
    # Read existing records
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                records = json.load(f)
        except:
            records = []
    else:
        records = []

    # Add new records
    for result in results:
        # Add timestamp
        result["checked_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        records.append(result)

    # Save back to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"Results saved to {output_file}")


def load_submission_records(input_file="submission_records_v4.json"):
    """Load submission records from the JSON file"""
    if not os.path.exists(input_file):
        print(f"File not found: {input_file}")
        return []

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            records = json.load(f)
        print(f"Loaded {len(records)} submission records")
        return records
    except Exception as e:
        print(f"Error loading submission records: {e}")
        return []


def main():
    # Set up command line arguments for input and output files only
    parser = argparse.ArgumentParser(description='Process IOI contest submission results')
    parser.add_argument('--input', '-i', type=str,
                        default="./submit_results/ioi_contest_problems_gemini-2.5-pro-exp-03-25_filter_part2_submission.jsonl",
                        help='Input JSONL file with submission IDs')
    parser.add_argument('--output', '-o', type=str,
                        default="./ioi_scores/ioi_contest_problems_gemini-2.5-pro-exp-03-25_filter_part2_score.jsonl",
                        help='Output JSONL file for results')

    args = parser.parse_args()

    # Get file paths from command line arguments
    input_file = args.input
    output_file = args.output

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Load submission records
    submission_records = load_submission_records(input_file)

    if not submission_records:
        print("No submission records found. Exiting.")
        return

    # Initialize browser
    print("Starting browser...")
    page = ChromiumPage()

    try:
        # Open login page
        login_url = 'https://ioi.contest.codeforces.com/enter?back=%2F'
        page.get(login_url)
        print("Please complete login in the browser window, waiting 30 seconds...")

        # Wait for manual login
        for i in tqdm(range(30), desc="Waiting for login"):
            time.sleep(1)

        # Check if login was successful
        if not is_logged_in(page):
            print("Login failed or timed out. Please ensure you're logged in.")
            input("Press Enter to continue anyway or Ctrl+C to exit...")

        # Get username
        user_info = BeautifulSoup(page.html, 'html.parser').find('a', href=lambda href: href and '/profile/' in href)
        username = safe_get_text(user_info)
        print(f"Successfully logged in as: {username}")

        # Process each submission
        results = []
        for i, record in enumerate(submission_records):
            print(f"\nProcessing submission {i + 1}/{len(submission_records)}:")

            submission_id = record.get("submission_id")
            group_id = record.get("group_id")
            contest_id = record.get("contest_id")

            if not submission_id:
                print("Skipping: No submission ID found")
                continue

            # Get submission result
            try:
                result = get_submission_result(page, submission_id, group_id, contest_id)

                # Add original record info
                result["problem_title"] = record.get("title")
                result["problem_index"] = record.get("problem_index")
                result["date"] = record.get("date")
                result["original_record_id"] = i  # Store the index of the original record

                results.append(result)
                print(f"Result: {result.get('verdict', 'Unknown')}")
            except Exception as e:
                print(f"Error processing submission {submission_id}: {e}")
                error_result = {
                    "submission_id": submission_id,
                    "status": "Error",
                    "error_message": str(e),
                    "problem_title": record.get("title"),
                    "problem_index": record.get("problem_index"),
                    "date": record.get("date"),
                    "original_record_id": i
                }
                results.append(error_result)

            # Wait between requests
            if i < len(submission_records) - 1:
                wait_time = random.uniform(3, 6)
                print(f"Waiting {wait_time:.2f} seconds before next request...")
                time.sleep(wait_time)

        # Save results
        save_results(results, output_file)
        print("\nAll submissions processed")

    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close browser
        page.quit()


if __name__ == "__main__":
    main()



