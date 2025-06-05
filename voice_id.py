import os
import requests
import json
import time
from datetime import datetime

# --- Your Configuration ---
# API endpoint for audio file uploads
api_url = 'https://be.video-id.13.211.5.214.sslip.io/voice-id'

# Base directory containing Voice ID subfolders
# CHANGE THIS PATH TO YOUR ACTUAL BASE DIRECTORY
base_directory = r'E:\sharex\ShareX\Screenshots\2025-03\voice'

# Audio file extensions the script will process
# Add or remove formats as needed
AUDIO_EXTENSIONS = ('.mov', '.mp3', '.wav', '.m4a', '.mkv')

# File name for detailed upload logs
DETAIL_LOG_FILE_NAME = 'upload_log_audio_detail.txt'

# File name for summarized Voice ID test results
SUMMARY_LOG_FILE_NAME = 'upload_log_audio_summary.txt'

# Maximum number of retries for failed uploads (server errors or network issues)
MAX_RETRIES = 3


# --- Script Start ---

def upload_and_verify_voice_ids(base_dir, api_endpoint, detail_log_name, summary_log_name, max_retries):
    """
    Automatically uploads audio files from Voice ID subfolders,
    logs detailed responses, retries failed uploads, and verifies user_id consistency.
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Voice ID testing from: {base_dir}")
    print(f"API endpoint: {api_endpoint}")
    print(f"Detailed log file: {detail_log_name}")
    print(f"Summary log file: {summary_log_name}")

    # Write header for the new session in the detailed log file
    with open(detail_log_name, 'a', encoding='utf-8') as log_file:
        log_file.write(
            f"\n{'=' * 20} STARTING UPLOAD SESSION AT {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {'=' * 20}\n\n")

    # Write header for the new session in the summary log file
    with open(summary_log_name, 'a', encoding='utf-8') as log_file:
        log_file.write(f"\n{'=' * 20} SUMMARY RESULTS AT {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {'=' * 20}\n\n")

    # Overall counters for the entire process
    overall_total_files = 0
    overall_success_uploads = 0
    overall_failed_uploads = 0
    overall_passed_voice_ids = 0
    overall_failed_voice_ids = 0

    # Iterate through subfolders in the base directory
    # Each subfolder is treated as a "Voice ID"
    for voice_id_folder_name in sorted(os.listdir(base_dir)):
        voice_id_folder_path = os.path.join(base_dir, voice_id_folder_name)

        if not os.path.isdir(voice_id_folder_path):
            # Skip non-directory items (e.g., old log files)
            print(f"Skipping: {voice_id_folder_name} (Not a directory)")
            continue

        print(f"\n{'#' * 10} Processing Voice ID: {voice_id_folder_name} {'#' * 10}")

        # List all valid audio files in the current Voice ID folder
        current_voice_audio_files = [
            f for f in os.listdir(voice_id_folder_path)
            if os.path.isfile(os.path.join(voice_id_folder_path, f)) and
               f.lower().endswith(AUDIO_EXTENSIONS)
        ]

        if not current_voice_audio_files:
            print(f"  No audio files found in folder '{voice_id_folder_name}'. Skipping.")
            with open(summary_log_name, 'a', encoding='utf-8') as s_log:
                s_log.write(f"Voice ID: {voice_id_folder_name} - NO FILES FOUND FOR TESTING.\n\n")
            continue

        # Variables to track results for the current Voice ID
        voice_id_results = {
            'user_ids_returned': set(),  # Use a set to store unique user_ids
            'new_record_count': 0,
            'existing_record_count': 0,
            'failed_uploads_count': 0,
            'total_files_processed': 0
        }

        # Count total files for the current Voice ID
        num_files_in_current_voice_id = len(current_voice_audio_files)
        overall_total_files += num_files_in_current_voice_id

        for i, audio_file in enumerate(current_voice_audio_files):
            file_path = os.path.join(voice_id_folder_path, audio_file)
            print(f"  --- [{i + 1}/{num_files_in_current_voice_id}] Uploading: {audio_file} ---")

            response = None
            current_attempt = 0

            while current_attempt < max_retries:
                current_attempt += 1
                print(f"    Attempt {current_attempt}/{max_retries} for {audio_file}...")

                try:
                    with open(file_path, 'rb') as f:
                        # Field name for the form should be 'audio' as per API
                        files = {'audio': (audio_file, f, 'application/octet-stream')}
                        response = requests.post(api_endpoint, files=files,
                                                 timeout=60)  # Add timeout to prevent hanging

                    # If status code is not a server error (5xx), break retry loop
                    if response.status_code < 500:  # Includes 2xx, 3xx, 4xx
                        break
                    else:
                        print(f"    ⚠️ Server error {response.status_code}. Retrying...")

                except requests.exceptions.Timeout:
                    print(f"    ⏰ Connection timed out. Retrying...")
                except requests.exceptions.ConnectionError:
                    print(f"    🔌 Network connection error. Retrying...")
                except requests.exceptions.RequestException as e:
                    print(f"    ❌ Unknown request error: {e}. Retrying...")

                time.sleep(2)  # Wait 2 seconds before retrying

            # --- Log detailed results and process response for each file ---
            log_entry_content = ""
            log_entry_content += f"Voice ID Folder: {voice_id_folder_name}\n"
            log_entry_content += f"File Name: {audio_file}\n"
            log_entry_content += f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

            voice_id_results['total_files_processed'] += 1

            if response:
                try:
                    response_json = response.json()
                    formatted_response = json.dumps(response_json, indent=4, ensure_ascii=False)
                except json.JSONDecodeError:
                    response_json = None
                    formatted_response = response.text

                log_entry_content += f"HTTP Status Code: {response.status_code}\n"
                log_entry_content += "Response Content:\n"
                log_entry_content += formatted_response + "\n"

                if response.status_code == 200:
                    print(f"  ✅ Upload successful: {audio_file}")
                    overall_success_uploads += 1
                    if response_json and 'user_id' in response_json:
                        voice_id_results['user_ids_returned'].add(response_json['user_id'])
                        if response_json.get('new_record', False):
                            voice_id_results['new_record_count'] += 1
                        else:
                            voice_id_results['existing_record_count'] += 1
                else:
                    print(f"  ❌ Upload failed: {audio_file} (Code: {response.status_code})")
                    overall_failed_uploads += 1
                    voice_id_results['failed_uploads_count'] += 1
            else:
                log_entry_content += "No response received from API after all retries.\n"
                print(f"  ❌ Upload failed: {audio_file} (No Response)")
                overall_failed_uploads += 1
                voice_id_results['failed_uploads_count'] += 1

            log_entry_content += "=" * 70 + "\n\n"  # Separator for log entries

            # Write detailed log to file
            with open(detail_log_name, 'a', encoding='utf-8') as d_log:
                d_log.write(log_entry_content)

            time.sleep(0.5)  # Small delay between files to avoid overloading

        # --- Check User ID consistency for the current Voice ID ---
        with open(summary_log_name, 'a', encoding='utf-8') as s_log:
            s_log.write(f"Voice ID Folder: {voice_id_folder_name}\n")
            s_log.write(f"  Total files processed: {voice_id_results['total_files_processed']}\n")
            s_log.write(f"  New records created: {voice_id_results['new_record_count']}\n")
            s_log.write(f"  Existing records found: {voice_id_results['existing_record_count']}\n")
            s_log.write(f"  Failed uploads: {voice_id_results['failed_uploads_count']}\n")
            s_log.write(f"  Unique User IDs returned: {list(voice_id_results['user_ids_returned'])}\n")

            if voice_id_results['failed_uploads_count'] > 0:
                s_log.write("  STATUS: ❌ FAIL - Upload errors occurred.\n\n")
                overall_failed_voice_ids += 1
            elif not voice_id_results['user_ids_returned']:
                s_log.write("  STATUS: ❌ FAIL - No User IDs successfully returned.\n\n")
                overall_failed_voice_ids += 1
            elif len(voice_id_results['user_ids_returned']) == 1:
                s_log.write(
                    f"  STATUS: ✅ PASS - All files returned the same User ID: {list(voice_id_results['user_ids_returned'])[0]}\n\n")
                overall_passed_voice_ids += 1
            else:
                s_log.write("  STATUS: ❌ FAIL - User IDs are inconsistent across files!\n\n")
                overall_failed_voice_ids += 1

            s_log.write("=" * 70 + "\n\n")

    # --- Overall Test Summary Report ---
    print(f"\n{'=' * 70}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] VOICE ID TESTING COMPLETE")
    print(f"Total files attempted to upload: {overall_total_files}")
    print(f"Total successful uploads: {overall_success_uploads}")
    print(f"Total failed uploads: {overall_failed_uploads}")
    print(f"Total Voice IDs tested: {overall_passed_voice_ids + overall_failed_voice_ids}")
    print(f"Voice IDs PASSED: {overall_passed_voice_ids}")
    print(f"Voice IDs FAILED: {overall_failed_voice_ids}")
    print(f"Detailed logs available in: {DETAIL_LOG_FILE_NAME}")
    print(f"Summary results available in: {SUMMARY_LOG_FILE_NAME}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    upload_and_verify_voice_ids(base_directory, api_url, DETAIL_LOG_FILE_NAME, SUMMARY_LOG_FILE_NAME, MAX_RETRIES)