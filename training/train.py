import os
import sys
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from dataset_loader import CropDataset
from model import MultiHeadModel, CONDITION_CLASSES, CAUSE_CLASSES, SEVERITY_CLASSES, STAGE_CLASSES, CROP_TYPE_CLASSES

# ======================
# CONFIG
# ======================
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🖥️  Using device: {DEVICE}")

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
JSON_PATH  = os.path.join(BASE_DIR, "../dataset.json")
IMAGE_DIR  = os.path.join(BASE_DIR, "../images")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

os.makedirs(OUTPUT_DIR, exist_ok=True)

BATCH_SIZE = 8
EPOCHS     = 10
LR         = 0.001
VAL_SPLIT  = 0.2

# ======================
# LOAD DATA
# ======================
print("\n📂 Loading dataset...")

dataset = CropDataset(
    json_path=JSON_PATH,
    image_dir=IMAGE_DIR
)

total = len(dataset)
print(f"Total samples: {total}")

if total == 0:
    print("❌ No samples found. Run export_from_cvat.py and prepare_dataset.py first.")
    sys.exit(1)

# Train/val split
if total < 5:
    print("⚠️  Small dataset — using all data for both train and val")
    train_dataset = dataset
    val_dataset   = dataset
    train_size    = total
    val_size      = total
else:
    val_size      = max(1, int(total * VAL_SPLIT))
    train_size    = total - val_size
    train_dataset, val_dataset = random_split(dataset, [train_size, val_size])

print(f"Train samples : {train_size}")
print(f"Val samples   : {val_size}")

train_loader = DataLoader(
    train_dataset,
    batch_size=min(BATCH_SIZE, train_size),
    shuffle=True
)

val_loader = DataLoader(
    val_dataset,
    batch_size=min(BATCH_SIZE, val_size),
    shuffle=False
)

# ======================
# MODEL
# ======================
print("\n🧠 Loading model...")
model = MultiHeadModel().to(DEVICE)

print(f"  condition classes : {len(CONDITION_CLASSES)}")
print(f"  cause classes     : {len(CAUSE_CLASSES)}")
print(f"  severity classes  : {len(SEVERITY_CLASSES)}")
print(f"  stage classes     : {len(STAGE_CLASSES)}")
print(f"  crop_type classes : {len(CROP_TYPE_CLASSES)}")

# ======================
# LOSS + OPTIMIZER
# ======================
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=LR)
scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)

# ======================
# TRAIN
# ======================
print("\n🚀 Starting training...\n")

best_val_loss = float("inf")

for epoch in range(EPOCHS):

    # --- Train phase ---
    model.train()
    total_train_loss = 0

    for images, labels in train_loader:
        images    = images.to(DEVICE)
        condition = labels["condition"].to(DEVICE)
        cause     = labels["cause"].to(DEVICE)
        severity  = labels["severity"].to(DEVICE)
        stage     = labels["stage"].to(DEVICE)
        crop_type = labels["crop_type"].to(DEVICE)

        optimizer.zero_grad()
        outputs = model(images)

        loss = (
            criterion(outputs["condition"], condition) +
            criterion(outputs["cause"],     cause)     +
            criterion(outputs["severity"],  severity)  +
            criterion(outputs["stage"],     stage)     +
            criterion(outputs["crop_type"], crop_type)
        )

        loss.backward()
        optimizer.step()
        total_train_loss += loss.item()

    avg_train_loss = total_train_loss / len(train_loader)

    # --- Val phase ---
    model.eval()
    total_val_loss = 0

    with torch.no_grad():
        for images, labels in val_loader:
            images    = images.to(DEVICE)
            condition = labels["condition"].to(DEVICE)
            cause     = labels["cause"].to(DEVICE)
            severity  = labels["severity"].to(DEVICE)
            stage     = labels["stage"].to(DEVICE)
            crop_type = labels["crop_type"].to(DEVICE)

            outputs = model(images)

            loss = (
                criterion(outputs["condition"], condition) +
                criterion(outputs["cause"],     cause)     +
                criterion(outputs["severity"],  severity)  +
                criterion(outputs["stage"],     stage)     +
                criterion(outputs["crop_type"], crop_type)
            )

            total_val_loss += loss.item()

    avg_val_loss = total_val_loss / len(val_loader)

    scheduler.step()

    print(f"Epoch {epoch+1:02d}/{EPOCHS} | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")

    # Save best model
    if avg_val_loss < best_val_loss:
        best_val_loss = avg_val_loss
        best_path = os.path.join(OUTPUT_DIR, "best_model.pth")
        torch.save(model.state_dict(), best_path)
        print(f"  💾 Best model saved! Val Loss: {best_val_loss:.4f}")

# ======================
# SAVE FINAL MODEL
# ======================
final_path = os.path.join(OUTPUT_DIR, "multihead_model.pth")
torch.save(model.state_dict(), final_path)

print(f"\n✅ Training Complete!")
print(f"   Best model  : {OUTPUT_DIR}/best_model.pth")
print(f"   Final model : {OUTPUT_DIR}/multihead_model.pth")
print(f"   Best val loss: {best_val_loss:.4f}")