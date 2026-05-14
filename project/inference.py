import sys
import os
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

# ======================
# LABEL MAPS
# ======================

CONDITION_CLASSES = ["Healthy", "Biotic", "Abiotic", "Unknown"]

CAUSE_CLASSES = [
    "None",
    "bacterial_leaf_blight",
    "bacterial_leaf_streak",
    "leaf_blast",
    "neck_blast",
    "brown_spot",
    "sheath_blight",
    "sheath_rot",
    "tungro",
    "false_smut",
    "insect_damage",
    "Unknown"
]

SEVERITY_CLASSES = ["None", "Low", "Medium", "High", "Unknown"]

STAGE_CLASSES = [
    "Germination",
    "Vegetative",
    "Flowering",
    "Fruiting",
    "PhysiologicalMaturity",
    "Unknown"
]

CROP_TYPE_CLASSES = ["paddy", "chilli", "wheat", "rice", "tomato", "Unknown"]
# ======================
# MODEL
# ======================

class MultiHeadModel(nn.Module):
    def __init__(self):
        super().__init__()

        self.backbone = models.efficientnet_b0(weights=None)
        in_features = self.backbone.classifier[1].in_features
        self.backbone.classifier = nn.Identity()

        self.condition_head  = nn.Linear(in_features, len(CONDITION_CLASSES))
        self.cause_head      = nn.Linear(in_features, len(CAUSE_CLASSES))
        self.severity_head   = nn.Linear(in_features, len(SEVERITY_CLASSES))
        self.stage_head      = nn.Linear(in_features, len(STAGE_CLASSES))
        self.crop_type_head  = nn.Linear(in_features, len(CROP_TYPE_CLASSES))

    def forward(self, x):
        feat = self.backbone(x)
        return {
            "condition":  self.condition_head(feat),
            "cause":      self.cause_head(feat),
            "severity":   self.severity_head(feat),
            "stage":      self.stage_head(feat),
            "crop_type":  self.crop_type_head(feat)
        }

# ======================
# LOAD MODEL
# ======================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "training/outputs/best_model.pth")

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = MultiHeadModel()

if not os.path.exists(MODEL_PATH):
    print("ERROR: Model not found. Train the model first.")
    sys.exit(1)

model.load_state_dict(
    torch.load(MODEL_PATH, map_location=DEVICE)
)
model.to(DEVICE)
model.eval()

# ======================
# TRANSFORM
# ======================

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        [0.485, 0.456, 0.406],
        [0.229, 0.224, 0.225]
    )
])

# ======================
# INPUT IMAGE
# ======================

if len(sys.argv) < 2:
    print("ERROR: No image path provided")
    sys.exit(1)

image_path = sys.argv[1]

if not os.path.exists(image_path):
    print(f"ERROR: Image not found: {image_path}")
    sys.exit(1)

image = Image.open(image_path).convert("RGB")
image = transform(image).unsqueeze(0).to(DEVICE)

# ======================
# PREDICT
# ======================

with torch.no_grad():
    outputs = model(image)

    cond      = torch.argmax(outputs["condition"]).item()
    cause     = torch.argmax(outputs["cause"]).item()
    sev       = torch.argmax(outputs["severity"]).item()
    stage     = torch.argmax(outputs["stage"]).item()
    crop_type = torch.argmax(outputs["crop_type"]).item()

# ======================
# PRINT OUTPUT
# format: condition|cause|severity|stage|crop_type
# ======================

print(
    f"{CONDITION_CLASSES[cond]}|"
    f"{CAUSE_CLASSES[cause]}|"
    f"{SEVERITY_CLASSES[sev]}|"
    f"{STAGE_CLASSES[stage]}|"
    f"{CROP_TYPE_CLASSES[crop_type]}"
)