# 📀 Video Upload Automation to Video-ID API

This script automates the upload of `.mp4` video files to the Video-ID recognition API, analyzes the response, and logs structured results per user and testcase.

---

## 📁 Directory & File Naming

* Place all video files into the target directory (configured as `directory = ...` in the script).
* Supported format: `.mp4` (recommended for compatibility).
* File name pattern must follow:

```
<testcase_name> user <user_key> (<optional_number>).mp4
```

✅ Example:

* `chandor user A (1).mp4`
* `makeup user B.mp4`

This helps the script correctly associate results with each user and testcase.

---

## 🧠 Logic Overview

### Upload Behavior:

* Videos are uploaded via `POST` to the API endpoint.
* If server returns a 5xx error (e.g., 500, 502), the upload will retry up to **3 times**.
* After every upload (success or fail), the script **waits 30 seconds** before moving on.

### Response Handling:

The response is expected to contain:

* `video.id`: Contains ID string and tag (`(User found)` or `(Created a new user)`).
* `video.success`: Whether the video part succeeded.
* Specific error messages (e.g., `"Failed to extract face from video..."`).

---

## 🗞 Summary Result (`results_status.txt`)

Each test run will append a block like this:

```txt
=== RUN RESULTS at 2025-04-28 21:10:12 ===
* 📊 Summary:
   📁 Total files: 28
   ✅ Success: 26
   ❌ Failed: 2

* Testcase: chandor
User A
   📁 Total files: 12
   ✅ User found: 11
   🆕 Created new user: 1
   ⚠️ Failed to extract face: 0 times
   Found IDs:
     - chrome_123abc: 11 times
   Created New User IDs:
     - chrome_123abc: 1 times
   ✔️ chandor user A pass
```

### Notes:

* ✅ **User found**: Matched to existing user in system.
* 🆕 **Created new user**: A new user was registered.
* ⚠️ **Failed to extract face**: Face not detected in the video.
  ⚠️ This **does NOT affect pass/fail** status — it's just informational.

---

## ✅ Pass / ❌ Fail Criteria

**A user group passes if:**

* All IDs (found or created) are the same, or
* Found and created IDs are identical.

**Fails if:**

* Multiple different IDs detected (implying mismatch), or
* No successful matches or new users created.

---

## 📄 Log File

All detailed responses are saved in `results_log.txt` for review.

---

## 🛠️ API Endpoint

Current endpoint:

```
https://be.video-id.3.26.13.166.sslip.io/identify
```

---

## 🧪 Recommended Workflow

1. Organize `.mp4` files in a directory with correct names.
2. Run the script.
3. Check:

   * `results_log.txt` for raw response data.
   * `results_status.txt` for summary and test verdict.

---

## ℹ️ Tip

To minimize failure due to video issues:

* Ensure clear face visibility.
* Avoid excessive blur, low lighting, or obstruction.

---
