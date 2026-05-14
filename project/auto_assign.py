import os
import time
import json
import subprocess
import requests
from dotenv import dotenv_values

# ======================
# CONFIG
# ======================
config = dotenv_values(os.path.join(os.path.dirname(__file__), ".env"))

CVAT_URL = config["CVAT_URL"]
USERNAME = config["CVAT_USERNAME"]
PASSWORD = config["CVAT_PASSWORD"]
PROJECT_ID = int(config["CVAT_PROJECT_ID"])

# Role mapping
ANNOTATOR  = "annotator_1"
REVIEWER   = "Nikhil_Kashyap"
MAINTAINER = "Sriharsha"

POLL_INTERVAL = 120  # seconds (2 minutes)

# Pipeline script path
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
PIPELINE_SCRIPT = os.path.join(BASE_DIR, "../run_pipeline.py")

# Fix 1 — Persist triggered tasks to file so survives restarts
TRIGGERED_FILE  = os.path.join(BASE_DIR, "logs/triggered_tasks.json")

# Track original annotator per job — {job_id: annotator_id}
ANNOTATOR_TRACK_FILE = os.path.join(BASE_DIR, "logs/job_annotators.json")

def load_triggered_tasks():
    if os.path.exists(TRIGGERED_FILE):
        with open(TRIGGERED_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_triggered_tasks(tasks):
    with open(TRIGGERED_FILE, "w") as f:
        json.dump(list(tasks), f)

def load_job_annotators():
    if os.path.exists(ANNOTATOR_TRACK_FILE):
        with open(ANNOTATOR_TRACK_FILE, "r") as f:
            return json.load(f)
    return {}

def save_job_annotators(job_annotators):
    with open(ANNOTATOR_TRACK_FILE, "w") as f:
        json.dump(job_annotators, f)

# Load on startup
pipeline_triggered_tasks = load_triggered_tasks()
job_annotators = load_job_annotators()

# ======================
# LOGIN
# ======================
def login():
    session = requests.Session()
    session.get(f"{CVAT_URL}/api/auth/login")
    csrftoken = session.cookies.get("csrftoken", "")
    session.post(
        f"{CVAT_URL}/api/auth/login",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"X-CSRFToken": csrftoken, "Referer": CVAT_URL}
    )
    csrftoken = session.cookies.get("csrftoken", csrftoken)
    session.headers.update({"X-CSRFToken": csrftoken, "Referer": CVAT_URL})
    return session

# ======================
# GET USER ID
# ======================
def get_user_id(session, username):
    res = session.get(f"{CVAT_URL}/api/users", params={"search": username})
    users = res.json().get("results", [])
    for user in users:
        if user["username"] == username:
            return user["id"]
    return None

# ======================
# GET ALL JOBS IN PROJECT
# ======================
def get_jobs(session):
    res = session.get(
        f"{CVAT_URL}/api/jobs",
        params={"project_id": PROJECT_ID, "page_size": 100}
    )
    return res.json().get("results", [])

# ======================
# REASSIGN JOB
# ======================
def reassign_job(session, job_id, assignee_id, stage):
    res = session.patch(
        f"{CVAT_URL}/api/jobs/{job_id}",
        json={"assignee": assignee_id, "stage": stage},
        headers={"Content-Type": "application/json"}
    )
    return res.status_code

# ======================
# TRIGGER PIPELINE
# ======================
def trigger_pipeline(task_id):
    print(f"\n🚀 Triggering pipeline for task {task_id}...")
    try:
        result = subprocess.run(
            ["python3", PIPELINE_SCRIPT],
            cwd=os.path.dirname(PIPELINE_SCRIPT)
        )
        if result.returncode == 0:
            print(f"✅ Pipeline completed successfully!")
            restart_server()
        else:
            print(f"❌ Pipeline failed!")
    except Exception as e:
        print(f"❌ Pipeline error: {e}")

# ======================
# Fix 2 — RESTART SERVER
# ======================
def restart_server():
    print(f"\n🔄 Restarting prediction server...")
    try:
        subprocess.run(["pkill", "-f", "node server.js"], cwd=BASE_DIR)
        time.sleep(2)
        subprocess.Popen(
            ["node", "server.js"],
            cwd=BASE_DIR,
            stdout=open(os.path.join(BASE_DIR, "logs/server.log"), "a"),
            stderr=subprocess.STDOUT
        )
        print(f"✅ Server restarted!")
    except Exception as e:
        print(f"❌ Server restart error: {e}")

# ======================
# MAIN LOOP
# ======================
def main():
    print("🤖 Auto-assign script started!")
    print(f"   Annotator  : {ANNOTATOR}")
    print(f"   Reviewer   : {REVIEWER}")
    print(f"   Maintainer : {MAINTAINER}")
    print(f"   Polling every {POLL_INTERVAL} seconds\n")

    session = login()
    print("✅ Logged in to CVAT\n")

    # Get user IDs
    annotator_id  = get_user_id(session, ANNOTATOR)
    reviewer_id   = get_user_id(session, REVIEWER)
    maintainer_id = get_user_id(session, MAINTAINER)

    print(f"User IDs:")
    print(f"  {ANNOTATOR}  : {annotator_id}")
    print(f"  {REVIEWER}   : {reviewer_id}")
    print(f"  {MAINTAINER} : {maintainer_id}\n")

    while True:
        try:
            print(f"🔍 Checking jobs... ({time.strftime('%H:%M:%S')})")

            session = login()

            jobs = get_jobs(session)
            print(f"   Found {len(jobs)} jobs")

            for job in jobs:
                job_id        = job["id"]
                task_id       = job.get("task_id")
                state         = job.get("state", "")
                stage         = job.get("stage", "")
                assignee      = job.get("assignee")
                assignee_id   = assignee["id"] if assignee else None
                assignee_name = assignee["username"] if assignee else "unassigned"

                print(f"   Job {job_id}: stage={stage} state={state} assignee={assignee_name}")

                # annotator completed → track annotator + assign to reviewer
                if state == "completed" and stage == "annotation" and assignee_id == annotator_id:
                    # Track who annotated this job
                    job_annotators[str(job_id)] = assignee_id
                    save_job_annotators(job_annotators)
                    print(f"   ➡️  Job {job_id}: Assigning to reviewer {REVIEWER}")
                    status = reassign_job(session, job_id, reviewer_id, "validation")
                    print(f"   ✅ Done! Status: {status}")

                # reviewer approved → assign to maintainer
                elif state == "completed" and stage == "validation" and assignee_id == reviewer_id:
                    print(f"   ➡️  Job {job_id}: Assigning to maintainer {MAINTAINER}")
                    status = reassign_job(session, job_id, maintainer_id, "acceptance")
                    print(f"   ✅ Done! Status: {status}")

                # maintainer accepted → trigger pipeline
                elif state == "completed" and stage == "acceptance" and assignee_id == maintainer_id:
                    if task_id not in pipeline_triggered_tasks:
                        print(f"   🎯 Job {job_id} accepted by maintainer!")
                        pipeline_triggered_tasks.add(task_id)
                        save_triggered_tasks(pipeline_triggered_tasks)
                        trigger_pipeline(task_id)

                # reviewer rejected → back to original annotator
                elif state == "rejected" and stage == "validation":
                    original_annotator_id = job_annotators.get(str(job_id))
                    if original_annotator_id:
                        print(f"   ❌ Job {job_id}: Rejected by reviewer! Reassigning to original annotator")
                        status = reassign_job(session, job_id, original_annotator_id, "annotation")
                        print(f"   ✅ Done! Status: {status}")

                # maintainer rejected → back to original annotator
                elif state == "rejected" and stage == "acceptance":
                    original_annotator_id = job_annotators.get(str(job_id))
                    if original_annotator_id:
                        print(f"   ❌ Job {job_id}: Rejected by maintainer! Reassigning to original annotator")
                        status = reassign_job(session, job_id, original_annotator_id, "annotation")
                        print(f"   ✅ Done! Status: {status}")

        except Exception as e:
            print(f"❌ Error: {e}")
            try:
                session = login()
            except:
                pass

        print(f"   Sleeping {POLL_INTERVAL} seconds...\n")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()