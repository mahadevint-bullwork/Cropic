import os
import torch
import torch.nn as nn
import torch.optim as optim

from torch.utils.data import DataLoader
from dataset_loader import CropDataset
from model import MultiHeadModel

# ======================
# CONFIG
# ======================

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

JSON_PATH = os.path.join(BASE_DIR, "../project/dataset.json")
IMAGE_DIR = os.path.join(BASE_DIR, "../project/images")

OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

BATCH_SIZE = 8
EPOCHS = 3
LR = 0.001

# ======================
# LOAD DATA
# ======================

dataset = CropDataset(
    json_path=JSON_PATH,
    image_dir=IMAGE_DIR
)

loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

print("Dataset size:", len(dataset))

# ======================
# MODEL
# ======================

model = MultiHeadModel().to(DEVICE)

# ======================
# LOSS + OPTIMIZER
# ======================

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=LR)

# ======================
# TRAIN
# ======================

for epoch in range(EPOCHS):

    print(f"\nEpoch {epoch+1}/{EPOCHS}")

    model.train()
    total_loss = 0

    for images, labels in loader:

        images = images.to(DEVICE)

        condition = labels["condition"].to(DEVICE)
        cause = labels["cause"].to(DEVICE)
        severity = labels["severity"].to(DEVICE)
        stage = labels["stage"].to(DEVICE)

        optimizer.zero_grad()

        outputs = model(images)

        loss_condition = criterion(outputs["condition"], condition)
        loss_cause = criterion(outputs["cause"], cause)
        loss_severity = criterion(outputs["severity"], severity)
        loss_stage = criterion(outputs["stage"], stage)

        loss = loss_condition + loss_cause + loss_severity + loss_stage

        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    print("Total Loss:", total_loss)

# ======================
# SAVE MODEL
# ======================

model_path = os.path.join(OUTPUT_DIR, "multihead_model.pth")

torch.save(model.state_dict(), model_path)

print("\n✅ Training Complete")
print("Model saved at:", model_path)