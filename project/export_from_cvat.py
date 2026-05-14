import os
import requests
import zipfile
import time
from dotenv import dotenv_values

# ======================
# CONFIG
# ======================
config = dotenv_values(os.path.join(os.path.dirname(__file__), ".env"))

CVAT_URL = config["CVAT_URL"]
USERNAME = config["CVAT_USERNAME"]
PASSWORD = config["CVAT_PASSWORD"]
PROJECT_ID = config["CVAT_PROJECT_ID"]

OUTPUT_DIR = os.path.join(os.path.dirname(__file__))
ANNOTATIONS_PATH = os.path.join(OUTPUT_DIR, "annotations.xml")
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")

os.makedirs(IMAGES_DIR, exist_ok=True)

# Clear old annotations
if os.path.exists(ANNOTATIONS_PATH):
    os.remove(ANNOTATIONS_PATH)
# ======================
# LOGIN
# ======================
print("🔐 Logging in to CVAT...")

session = requests.Session()

# First get CSRF token
session.get(f"{CVAT_URL}/api/auth/login")
csrftoken = session.cookies.get("csrftoken", "")

login_res = session.post(
    f"{CVAT_URL}/api/auth/login",
    json={"username": USERNAME, "password": PASSWORD},
    headers={
        "X-CSRFToken": csrftoken,
        "Referer": CVAT_URL
    }
)

if login_res.status_code != 200:
    print("❌ Login failed:", login_res.text)
    exit(1)

# Update CSRF token after login
csrftoken = session.cookies.get("csrftoken", csrftoken)
session.headers.update({
    "X-CSRFToken": csrftoken,
    "Referer": CVAT_URL
})

print("✅ Logged in!")
# ======================
# GET ALL TASKS IN PROJECT
# ======================
print(f"\n📋 Fetching tasks for project {PROJECT_ID}...")

tasks_res = session.get(
    f"{CVAT_URL}/api/tasks",
    params={"project_id": PROJECT_ID, "page_size": 100}
)

tasks = tasks_res.json()["results"]
print(f"Found {len(tasks)} tasks")

# ======================
# EXPORT ANNOTATIONS + IMAGES
# ======================
all_annotations = []

for task in tasks:
    task_id = task["id"]
    task_name = task["name"]
    print(f"\n📦 Exporting task {task_id}: {task_name}")

    # Step 1 — Initiate export
    export_res = session.post(
        f"{CVAT_URL}/api/tasks/{task_id}/dataset/export",
        params={"format": "CVAT for images 1.1", "save_images": "False"}
    )

    if export_res.status_code not in [200, 201, 202]:
        print(f"  ❌ Failed to initiate export: {export_res.status_code} {export_res.text[:200]}")
        continue

    rq_id = export_res.json().get("rq_id")
    print(f"  ⏳ Export initiated, rq_id: {rq_id}")

    # Step 2 — Poll until ready
    result_url = None
    for attempt in range(20):
        time.sleep(3)
        status_res = session.get(f"{CVAT_URL}/api/requests/{rq_id}")
        status_data = status_res.json()
        status = status_data.get("status")
        print(f"  Status: {status}")

        if status == "finished":
            result_url = status_data.get("result_url")
            break
        elif status == "failed":
            print(f"  ❌ Export failed: {status_data}")
            break

    if not result_url:
        print(f"  ❌ Could not get result URL for task {task_id}")
        continue

    # Step 3 — Download
    print(f"  ⬇️ Downloading annotations...")
    download_res = session.get(result_url)

    zip_path = os.path.join(OUTPUT_DIR, f"task_{task_id}.zip")
    with open(zip_path, "wb") as f:
        f.write(download_res.content)

    # Step 4 — Extract XML
    with zipfile.ZipFile(zip_path, "r") as z:
        for name in z.namelist():
            print(f"  Found in zip: {name}")
            if name.endswith(".xml"):
                with z.open(name) as xml_file:
                    content = xml_file.read()
                    with open(ANNOTATIONS_PATH, "ab") as out:
                        out.write(content)
                print(f"  ✅ Annotations saved")

    os.remove(zip_path)

    # Step 5 — Download images
    print(f"  🖼️ Downloading images...")
    img_res = session.post(
        f"{CVAT_URL}/api/tasks/{task_id}/dataset/export",
        params={"format": "CVAT for images 1.1", "save_images": "True"}
    )

    if img_res.status_code not in [200, 201, 202]:
        print(f"  ❌ Failed to initiate image export")
        continue

    rq_id_img = img_res.json().get("rq_id")

    result_url_img = None
    for attempt in range(20):
        time.sleep(3)
        status_res = session.get(f"{CVAT_URL}/api/requests/{rq_id_img}")
        status_data = status_res.json()
        status = status_data.get("status")
        print(f"  Image export status: {status}")

        if status == "finished":
            result_url_img = status_data.get("result_url")
            break
        elif status == "failed":
            print(f"  ❌ Image export failed")
            break

    if not result_url_img:
        print(f"  ❌ Could not get image result URL")
        continue

    img_download_res = session.get(result_url_img)
    img_zip_path = os.path.join(OUTPUT_DIR, f"images_{task_id}.zip")
    with open(img_zip_path, "wb") as f:
        f.write(img_download_res.content)

    with zipfile.ZipFile(img_zip_path, "r") as z:
        for name in z.namelist():
            if not name.endswith("/"):
                filename = os.path.basename(name)
                if filename:
                    with z.open(name) as src, open(os.path.join(IMAGES_DIR, filename), "wb") as dst:
                        dst.write(src.read())
        print(f"  ✅ Images extracted")

    os.remove(img_zip_path)

print("\n✅ Export complete!")
print(f"Annotations: {ANNOTATIONS_PATH}")
print(f"Images: {IMAGES_DIR}")