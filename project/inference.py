import sys
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

# ======================
# LABEL MAPS (IMPORTANT)
# ======================

condition_map = ["Healthy", "Biotic", "Abiotic"]

cause_map = ["None", "leaf_blast", "brown_spot"]

severity_map = ["None", "Low", "Medium", "High"]

stage_map = [
    "Germination",
    "Vegetative",
    "Flowering",
    "Fruiting",
    "PhysiologicalMaturity"
]

# ======================
# MODEL (same as training)
# ======================

class MultiHeadModel(nn.Module):
    def __init__(self):
        super().__init__()

        self.backbone = models.efficientnet_b0(weights=None)
        in_features = self.backbone.classifier[1].in_features
        self.backbone.classifier = nn.Identity()

        self.condition_head = nn.Linear(in_features, 3)
        self.cause_head = nn.Linear(in_features, 3)
        self.severity_head = nn.Linear(in_features, 4)
        self.stage_head = nn.Linear(in_features, 5)

    def forward(self, x):
        feat = self.backbone(x)

        return {
            "condition": self.condition_head(feat),
            "cause": self.cause_head(feat),
            "severity": self.severity_head(feat),
            "stage": self.stage_head(feat)
        }

# ======================
# LOAD MODEL
# ======================

model = MultiHeadModel()

model.load_state_dict(
    torch.load(
        "../training/outputs/multihead_model.pth",
        map_location="cpu"
    )
)

model.eval()

# ======================
# TRANSFORM
# ======================

transform = transforms.Compose([
    transforms.Resize((224,224)),
    transforms.ToTensor(),
    transforms.Normalize(
        [0.485,0.456,0.406],
        [0.229,0.224,0.225]
    )
])

# ======================
# INPUT IMAGE
# ======================

image_path = sys.argv[1]

image = Image.open(image_path).convert("RGB")
image = transform(image).unsqueeze(0)

# ======================
# PREDICT
# ======================

with torch.no_grad():
    outputs = model(image)

    cond = torch.argmax(outputs["condition"]).item()
    cause = torch.argmax(outputs["cause"]).item()
    sev = torch.argmax(outputs["severity"]).item()
    stage = torch.argmax(outputs["stage"]).item()

# ======================
# PRINT OUTPUT
# ======================

print(
    f"{condition_map[cond]}|"
    f"{cause_map[cause]}|"
    f"{severity_map[sev]}|"
    f"{stage_map[stage]}"
)