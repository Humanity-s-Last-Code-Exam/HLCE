import os
import json
import time
import random
import datetime
import argparse
from tqdm import tqdm
from DrissionPage import ChromiumPage
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("submission.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define problem_indices that require Odometer language
ODO_PROBLEM_INDEXES = ['A1', 'A2', 'A3', 'A4', 'A5']
ODO_PROGRAM_TYPE_ID = "82"  # programTypeId for Odometer
DEFAULT_PROGRAM_TYPE_ID = "91"  # programTypeId for GNU G++17

# Submission rate control parameters
MAX_SUBMISSIONS_PER_HOUR = 95  # Set to 95 to have some margin
SUBMISSION_WINDOW = 3600  # 1 hour = 3600 seconds


class SubmissionTracker:
    """Track submission frequency to ensure we don't exceed limits"""

    def __init__(self, max_per_hour=MAX_SUBMISSIONS_PER_HOUR, window=SUBMISSION_WINDOW):
        self.max_per_hour = max_per_hour
        self.window = window
        self.submission_times = []

    def can_submit(self):
        """Check if we can make a submission"""
        current_time = time.time()
        # Remove submissions outside the time window
        self.submission_times = [t for t in self.submission_times if current_time - t <= self.window]
        return len(self.submission_times) < self.max_per_hour

    def record_submission(self):
        """Record a submission"""
        self.submission_times.append(time.time())

    def wait_time_needed(self):
        """Calculate how long we need to wait"""
        if self.can_submit():
            return 0

        current_time = time.time()
        oldest_submission = min(self.submission_times)
        return max(0, self.window - (current_time - oldest_submission))


def random_sleep(min_sec=1, max_sec=3):
    """Sleep for a random amount of time"""
    sleep_time = random.uniform(min_sec, max_sec)
    time.sleep(sleep_time)


def is_logged_in(page):
    """Check if currently logged in to ioi.contest.codeforces.com"""
    try:
        # Visit the ioi contest subdomain homepage
        page.get('https://ioi.contest.codeforces.com/')
        html = page.html
        soup = BeautifulSoup(html, 'html.parser')
        # Check for login status by finding links containing '/profile/'
        user_info = soup.find('a', href=lambda href: href and '/profile/' in href)
        return bool(user_info)
    except Exception as e:
        logger.error(f"Error checking login status: {e}")
        return False


def get_latest_submission_id(page):
    """Get the ID of the most recent submission"""
    logger.info("Getting latest submission ID...")

    try:
        # Parse the current page HTML using BeautifulSoup
        soup = BeautifulSoup(page.html, 'html.parser')

        # Find the first (most recent) submission row
        submission_row = soup.find('tr', attrs={'data-submission-id': True})

        if submission_row:
            submission_id = submission_row.get('data-submission-id')
            logger.info(f"Found latest submission ID: {submission_id}")
            return submission_id
        else:
            logger.warning("No submission ID found")
            return None
    except Exception as e:
        logger.error(f"Error getting latest submission ID: {e}")
        return None


def extract_submission_id(url):
    """Extract submission ID from URL"""
    match = re.search(r'submission/(\d+)', url)
    if match:
        return match.group(1)
    return None


def extract_contest_info(url):
    """Extract group_id, contest_id and problem_index from URL"""
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.strip('/').split('/')

    if len(path_parts) >= 5 and path_parts[0] == 'group':
        group_id = path_parts[1]
        contest_id = path_parts[3]
        problem_index = path_parts[5] if len(path_parts) > 5 else None
        return group_id, contest_id, problem_index

    return None, None, None


def save_submission_record(submission_data, output_file="submission_records.json"):
    """Save submission record to JSON file (as an array)"""
    try:
        # Read existing records
        records = []
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    records = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read existing records: {e}, will create new file")
                records = []

        # Add new record
        records.append(submission_data)

        # Save back to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

        logger.info(f"Submission record saved to {output_file}")
    except Exception as e:
        logger.error(f"Error saving submission record: {e}")


def submit_code(problem_data, code, code_index, page, submission_tracker, output_file):
    """Submit a single code to the IOI Codeforces platform"""
    problem_url = problem_data.get("problem_url")
    title = problem_data.get("title")
    date = problem_data.get("date")

    # Extract group_id, contest_id and problem_index from URL
    group_id, contest_id, problem_index = extract_contest_info(problem_url)

    if not group_id or not contest_id:
        logger.error(f"Error: Could not extract contest info from URL: {problem_url}")
        return False

    logger.info(f"Preparing to submit code [{code_index + 1}] for problem: {title}")
    logger.info(f"Group ID: {group_id}, Contest ID: {contest_id}, Problem Index: {problem_index}")

    # Check if we can submit
    if not submission_tracker.can_submit():
        wait_time = submission_tracker.wait_time_needed()
        logger.warning(f"Hourly submission limit reached, need to wait {wait_time:.2f} seconds")
        time.sleep(wait_time + random.uniform(5, 10))  # Additional random wait of 5-10 seconds

    # Determine if we need to use Odometer language
    if problem_index in ODO_PROBLEM_INDEXES:
        program_type_id = ODO_PROGRAM_TYPE_ID
        logger.info("Language selected: Odometer")
    else:
        program_type_id = DEFAULT_PROGRAM_TYPE_ID
        logger.info("Language selected: GNU G++23 14.2")

    # Visit the contest page
    logger.info("Visiting contest page...")
    try:
        contest_url = f'https://ioi.contest.codeforces.com/group/{group_id}/contest/{contest_id}'
        page.get(contest_url)
        random_sleep(2, 4)
    except Exception as e:
        logger.error(f"Error visiting contest page: {e}")
        return False

    # Visit the submission page
    try:
        submit_url = f'https://ioi.contest.codeforces.com/group/{group_id}/contest/{contest_id}/submit'
        if problem_index:
            submit_url += f'/{problem_index}'

        page.get(submit_url)
        random_sleep(2, 4)
        logger.info(f"Successfully reached submission page: {page.url}")
    except Exception as e:
        logger.error(f"Error visiting submission page: {e}")
        return False

    # Select problem if needed (if problem index wasn't in the URL)
    if not problem_index:
        logger.info("Need to select problem from dropdown...")
        try:
            # Use JavaScript to select the problem
            js_result = page.run_js('''
                var selects = document.getElementsByTagName('select');
                for (var i = 0; i < selects.length; i++) {
                    if (selects[i].name === 'submittedProblemIndex') {
                        // Get first option value as default
                        var firstOption = selects[i].options[1]; // Skip first option which may be "Select problem"
                        if (firstOption) {
                            selects[i].value = firstOption.value;
                            selects[i].dispatchEvent(new Event('change'));
                            return firstOption.value;
                        }
                        return null;
                    }
                }
                return null;
            ''')

            if js_result:
                problem_index = js_result
                logger.info(f"Auto-selected problem: {problem_index}")
            else:
                logger.warning("Could not auto-select problem, trying alternative method...")

                problem_selector = page.ele('select[name="submittedProblemIndex"]')
                if problem_selector:
                    options = problem_selector.eles('option')
                    if len(options) > 1:
                        problem_index = options[1].attr('value')
                        problem_selector.select(value=problem_index)
                        logger.info(f"Selected problem: {problem_index}")
                    else:
                        logger.error("No problem options found")
                        return False
                else:
                    logger.error("Problem selector not found, cannot submit")
                    return False
        except Exception as e:
            logger.error(f"Error selecting problem: {e}")
            return False

    # Select language
    try:
        logger.info(f"Selecting language: {'Odometer' if problem_index in ODO_PROBLEM_INDEXES else 'GNU G++17 7.3.0'}")
        page.run_js(f'''
            var selects = document.getElementsByTagName('select');
            for (var i = 0; i < selects.length; i++) {{
                if (selects[i].name === 'programTypeId') {{
                    selects[i].value = "{program_type_id}";
                    selects[i].dispatchEvent(new Event('change'));
                    return true;
                }}
            }}
            return false;
        ''')
    except Exception as e:
        logger.error(f"Error selecting language: {e}")
        return False

    # Enter code
    try:
        logger.info("Setting code...")

        # Use JavaScript to set the code
        js_result = page.run_js('''
            var textarea = document.getElementById('sourceCodeTextarea');
            if (textarea) {
                textarea.value = arguments[0];
                textarea.dispatchEvent(new Event('change'));

                // If ACE editor exists, set its value as well
                if (typeof ace !== "undefined" && ace.edit) {
                    try {
                        var editor = ace.edit("editor");
                        editor.setValue(arguments[0]);
                        editor.clearSelection();
                    } catch (e) {
                        console.error("Failed to set ACE editor:", e);
                    }
                }
                return true;
            }
            return false;
        ''', code)

        if not js_result:
            logger.warning("Could not set code via JavaScript, trying alternative method...")

            code_textarea = page.ele('#sourceCodeTextarea')
            if code_textarea:
                code_textarea.input(code)
                logger.info("Successfully set code")
            else:
                logger.error("Code input area not found, cannot submit")
                return False
    except Exception as e:
        logger.error(f"Error setting code: {e}")
        return False

    random_sleep(1, 2)

    # Submit the form
    try:
        logger.info("Attempting to submit form...")

        # Try different ways to find the submit button
        submit_button = page.ele('input[type="submit"]')
        if submit_button:
            logger.info("Found submit button, clicking...")
            submit_button.click()
        else:
            logger.warning("Standard submit button not found, trying alternative methods...")

            # Try using JavaScript to submit the form
            js_result = page.run_js('''
                var forms = document.getElementsByTagName('form');
                for (var i = 0; i < forms.length; i++) {
                    if (forms[i].classList.contains('submit-form')) {
                        forms[i].submit();
                        return true;
                    }
                }
                return false;
            ''')

            if not js_result:
                logger.warning("Could not submit form via JavaScript, looking for other submit buttons...")

                # Try other possible submit buttons
                submit_buttons = page.eles('button, input[type="button"], input[type="submit"]')
                for btn in submit_buttons:
                    btn_text = btn.text.lower() if btn.text else ''
                    btn_value = btn.attr('value', '').lower()
                    btn_type = btn.attr('type', '').lower()

                    if ('submit' in btn_text or 'submit' in btn_value or
                            btn_type == 'submit' or 'submit' in btn_text):
                        logger.info(f"Found possible submit button: {btn.text}")
                        btn.click()
                        break
                else:
                    logger.error("No submit button found, cannot submit")
                    return False
    except Exception as e:
        logger.error(f"Error submitting form: {e}")
        return False

    # Record the submission
    submission_tracker.record_submission()

    # Wait for submission to complete
    logger.info("Waiting for submission results...")
    for _ in tqdm(range(8), desc="Waiting for submission"):
        time.sleep(1)

    # Visit My Submissions page to get the latest submission ID
    try:
        my_submissions_url = f'https://ioi.contest.codeforces.com/group/{group_id}/contest/{contest_id}/my'
        page.get(my_submissions_url)
        random_sleep(2, 3)
    except Exception as e:
        logger.error(f"Error visiting my submissions page: {e}")
        return False

    # Get the latest submission ID
    submission_id = get_latest_submission_id(page)

    # If submission_id is empty, the retrieval failed, might need to log in again
    if not submission_id:
        logger.warning("Could not get latest submission ID. May not be logged in or submission failed.")
        return False

    # Create submission record
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    submission_record = {
        "date": date,
        "timestamp": timestamp,
        "problem_url": problem_url,
        "title": title,
        "group_id": group_id,
        "contest_id": contest_id,
        "problem_index": problem_index,
        "submission_id": submission_id,
        "code_index": code_index,
        "code": code
    }

    # Save submission record
    save_submission_record(submission_record, output_file)
    return True


def submit_codes(problem_data, page, submission_tracker, output_file="submission_records.json"):
    """Submit codes to the IOI Codeforces platform"""
    problem_url = problem_data.get("problem_url")
    title = problem_data.get("title")
    codes = problem_data.get("extracted_cpp_code", [])

    if not problem_url or not codes:
        logger.warning(f"Skipping: Missing problem URL or codes - {title}")
        return False

    logger.info(f"Starting to process problem: {title}")
    logger.info(f"Found {len(codes)} codes to submit")

    success_count = 0

    # Submit each code
    for i, code in enumerate(codes):
        logger.info(f"\n[{i + 1}/{len(codes)}] Preparing to submit code...")

        # Submit the code
        if submit_code(problem_data, code, i, page, submission_tracker, output_file):
            success_count += 1

            # Wait between submissions to avoid submitting too quickly
            if i < len(codes) - 1:
                wait_time = random.uniform(8, 15)
                logger.info(f"Waiting {wait_time:.2f} seconds before submitting next code...")
                time.sleep(wait_time)
        else:
            logger.warning(f"Code [{i + 1}/{len(codes)}] submission failed")

            # Wait longer after a failed submission before trying the next one
            if i < len(codes) - 1:
                wait_time = random.uniform(20, 30)
                logger.info(f"Submission failed, waiting {wait_time:.2f} seconds before continuing...")
                time.sleep(wait_time)

    logger.info(f"Problem {title} processing completed, successfully submitted {success_count}/{len(codes)} codes")
    return success_count == len(codes)


def main():
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Process and submit IOI contest problems')
    parser.add_argument('--input', '-i', type=str,
                        default="./results/ioi_contest_problems_gemini-2.5-pro-exp-03-25_filter_part2.jsonl",
                        help='Input JSONL file path')
    parser.add_argument('--output', '-o', type=str,
                        default="./submit_results/ioi_contest_problems_gemini-2.5-pro-exp-03-25_filter_part2_submission.jsonl",
                        help='Output JSONL file path')

    args = parser.parse_args()

    # Get file paths from command line arguments
    input_file = args.input
    output_file = args.output

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Create submission tracker
    submission_tracker = SubmissionTracker()

    # Read already processed problem URLs
    processed_problem_urls = set()
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                try:
                    # Read entire file as JSON array
                    records = json.load(f)
                    for record in records:
                        if "problem_url" in record:
                            processed_problem_urls.add(record["problem_url"])
                    logger.info(f"Read {len(processed_problem_urls)} already processed problem URLs from output file")
                except json.JSONDecodeError as e:
                    logger.warning(f"Error parsing output file: {e}, will create new file")
        except Exception as e:
            logger.warning(f"Error reading output file: {e}")

    # Read JSONL file
    problems = []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():  # Skip empty lines
                    try:
                        problem_data = json.loads(line)
                        problems.append(problem_data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing JSON line: {e}")

        if not problems:
            logger.error("No valid problem data found")
            return

        logger.info(f"Read {len(problems)} problems in total")

        # Initialize browser
        logger.info("Starting browser...")
        page = ChromiumPage()

        try:
            # Open login page
            login_url = 'https://ioi.contest.codeforces.com/enter?back=%2F'
            page.get(login_url)
            logger.info("Please login in the opened browser window, waiting 30 seconds...")

            # Wait for manual login
            for i in tqdm(range(30), desc="Waiting for login"):
                time.sleep(1)

            # Check login status
            if not is_logged_in(page):
                logger.warning("May not be logged in, please verify login status")
                input("Press Enter to continue after confirming login...")

            # Get username
            user_info = BeautifulSoup(page.html, 'html.parser').find('a',
                                                                     href=lambda href: href and '/profile/' in href)
            username = user_info.text.strip() if user_info else "Unknown user"
            logger.info(f"Successfully logged in as: {username}")

            # Process each problem
            for i, problem in enumerate(problems):
                logger.info(f"\nProcessing problem {i + 1}/{len(problems)}:")

                # Check if problem has already been processed
                if problem.get("problem_url") in processed_problem_urls:
                    logger.info(f"Problem already processed, skipping: {problem.get('title')}")
                    continue

                submit_codes(problem, page, submission_tracker, output_file)

                # Update list of processed problems
                processed_problem_urls.add(problem.get("problem_url"))

                # Wait between processing multiple problems
                if i < len(problems) - 1:
                    wait_time = random.uniform(15, 30)
                    logger.info(f"Waiting {wait_time:.2f} seconds before processing next problem...")
                    time.sleep(wait_time)

            logger.info("\nAll problems processed")

        except Exception as e:
            logger.error(f"Error occurred: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            # Close browser
            page.quit()

    except Exception as e:
        logger.error(f"Error reading or processing input file: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()
