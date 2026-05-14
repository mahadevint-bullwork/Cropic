import os
import sys
import subprocess

# ======================
# PATHS
# ======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = BASE_DIR
TRAINING_DIR = os.path.join(BASE_DIR, "training")

# ======================
# HELPER
# ======================
def run(script_path, cwd):
    print(f"\n{'='*50}")
    print(f"▶ Running: {script_path}")
    print(f"{'='*50}\n")

    result = subprocess.run(
        [sys.executable, script_path],
        cwd=cwd
    )

    if result.returncode != 0:
        print(f"\n❌ Failed: {script_path}")
        sys.exit(1)

    print(f"\n✅ Done: {script_path}")

# ======================
# STEP 1 — CLEAN OLD DATA
# ======================
print("\n🧹 Cleaning old data...")

annotations_path = os.path.join(PROJECT_DIR, "annotations.xml")
dataset_path     = os.path.join(PROJECT_DIR, "dataset.json")
images_dir       = os.path.join(PROJECT_DIR, "images")

if os.path.exists(annotations_path):
    os.remove(annotations_path)
    print("  Removed annotations.xml")

if os.path.exists(dataset_path):
    os.remove(dataset_path)
    print("  Removed dataset.json")

if os.path.exists(images_dir):
    for f in os.listdir(images_dir):
        os.remove(os.path.join(images_dir, f))
    print("  Cleared images/")

# ======================
# STEP 2 — EXPORT FROM CVAT
# ======================
run(
    script_path=os.path.join(PROJECT_DIR, "export_from_cvat.py"),
    cwd=PROJECT_DIR
)

# ======================
# STEP 3 — PREPARE DATASET
# ======================
run(
    script_path=os.path.join(PROJECT_DIR, "prepare_dataset.py"),
    cwd=PROJECT_DIR
)

# ======================
# STEP 4 — TRAIN MODEL
# ======================
run(
    script_path=os.path.join(TRAINING_DIR, "train.py"),
    cwd=TRAINING_DIR
)

# ======================
# DONE
# ======================
print("\n" + "="*50)
print("🎉 Pipeline Complete!")
print("="*50)
print(f"\n✅ Annotations : {annotations_path}")
print(f"✅ Dataset     : {dataset_path}")
print(f"✅ Images      : {images_dir}")
print(f"✅ Model       : {os.path.join(TRAINING_DIR, 'outputs/best_model.pth')}")
print("\nRestart server to use new model:")
print("  cd ~/Cropic/project && node server.js")