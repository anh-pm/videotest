import os
import requests
import json
from collections import defaultdict
from datetime import datetime
import time

# API endpoint to upload videos
api_url = 'https://be.video-id.3.26.13.166.sslip.io/identify'

# Directory containing video files
directory = r'E:\sharex\ShareX\Screenshots\2025-03\make up'

# Collect all .mp4 files in the directory
video_files = [f for f in os.listdir(directory) if f.lower().endswith('.mp4')]

# Overall counters
total_uploaded = 0
total_success = 0
total_failed = 0

# Results: testcase -> user -> stats and ID counts
results = defaultdict(lambda: defaultdict(lambda: {
    'total': 0,
    'user_found': 0,
    'created_new': 0,
    'found_ids': defaultdict(int),
    'new_ids': defaultdict(int)
}))

# Log detailed response for each file
for video in video_files:
    total_uploaded += 1
    file_path = os.path.join(directory, video)
    print(f'▶ Uploading: {video}')

    # Try uploading up to 3 times if server error
    max_retries = 3
    attempt = 0
    response = None

    while attempt < max_retries:
        attempt += 1
        with open(file_path, 'rb') as f:
            files = {'file': (video, f, 'video/mp4')}
            try:
                response = requests.post(api_url, files=files)
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Request error: {e}, retry {attempt}/{max_retries} for {video}...")
                time.sleep(1)
                continue

        if response.status_code not in [500, 502, 503, 504]:
            break

        print(f"⚠️ Server error {response.status_code}, retry {attempt}/{max_retries} for {video}...")
        time.sleep(1)

    # Prepare response JSON for logging
    try:
        response_json = response.json()
        formatted = json.dumps(response_json, indent=4, ensure_ascii=False)
    except Exception:
        response_json = None
        formatted = response.text

    # Append to results_log.txt
    with open('results_log.txt', 'a', encoding='utf-8') as log_file:
        log_file.write(f"File name: {video}\n")
        log_file.write(f"Status code: {response.status_code}\n")
        log_file.write("Response content:\n")
        log_file.write(formatted + "\n")
        log_file.write("=" * 70 + "\n")

    # Success or failure
    if response and response.status_code == 200:
        total_success += 1
        print(f'✅ Success: {video}')
    else:
        total_failed += 1
        print(f'❌ Failure: {video} - Status code: {response.status_code if response else "No Response"}')
        time.sleep(30)
        continue

    # Parse testcase and user key from filename
    base = os.path.splitext(video)[0]
    if ' user ' in base:
        parts = base.split(' user ', 1)
        testcase_name = parts[0].strip()
        raw_user = parts[1].strip()
        user_key = raw_user.split('(', 1)[0].strip()
    else:
        testcase_name = 'Unknown'
        user_key = 'Unknown'

    # Update basic counts
    data = results[testcase_name][user_key]
    data['total'] += 1

    # Analyze response IDs and counts
    if response_json and 'video' in response_json:
        vid_field = response_json['video'].get('id', '')
        vid_code = vid_field.split(' (')[0]
        if '(User found)' in vid_field:
            data['user_found'] += 1
            data['found_ids'][vid_code] += 1
        elif '(Created new user)' in vid_field:
            data['created_new'] += 1
            data['new_ids'][vid_code] += 1

    time.sleep(30)

# Append summary to results_status.txt
with open('results_status.txt', 'a', encoding='utf-8') as status_file:
    status_file.write(f"\n=== RUN RESULTS at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    status_file.write("* 📊 Summary:\n")
    status_file.write(f"   📁 Total files: {total_uploaded}\n")
    status_file.write(f"   ✅ Success: {total_success}\n")
    status_file.write(f"   ❌ Failed: {total_failed}\n\n")

    for testcase, users in results.items():
        status_file.write(f"* Testcase: {testcase}\n")
        for user, stats in users.items():
            status_file.write(f"User {user}\n")
            status_file.write(f"   📁 Total files: {stats['total']}\n")
            status_file.write(f"   ✅ User found: {stats['user_found']}\n")
            status_file.write(f"   🆕 Created new user: {stats['created_new']}\n")
            # List User Found IDs
            if stats['found_ids']:
                status_file.write("   Found IDs:\n")
                for id_code, count in stats['found_ids'].items():
                    status_file.write(f"     - {id_code}: {count} times\n")
            # List Created New User IDs
            if stats['new_ids']:
                status_file.write("   Created New User IDs:\n")
                for id_code, count in stats['new_ids'].items():
                    status_file.write(f"     - {id_code}: {count} times\n")
            # Pass/Fail logic
            union_ids = set(stats['found_ids'].keys()) | set(stats['new_ids'].keys())
            if (len(union_ids) == 1 and stats['total'] > 0) or (stats['found_ids'] and stats['new_ids'] and stats['found_ids'].keys() == stats['new_ids'].keys()):
                only_id = list(union_ids)[0]
                status_file.write(f"   ✔️ {testcase} user {user} pass - ID: {only_id}\n")
            else:
                status_file.write(f"   ❌ {testcase} user {user} fail\n")
        status_file.write("\n")

print("✅ Finished writing results_log.txt and results_status.txt")