import torch.nn as nn
from torchvision import models

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

        # Backbone - EfficientNet B0
        self.backbone = models.efficientnet_b0(weights="IMAGENET1K_V1")
        in_features = self.backbone.classifier[1].in_features

        # Remove original classifier
        self.backbone.classifier = nn.Identity()

        # 5 Heads — one per attribute
        self.condition_head  = nn.Linear(in_features, len(CONDITION_CLASSES))
        self.cause_head      = nn.Linear(in_features, len(CAUSE_CLASSES))
        self.severity_head   = nn.Linear(in_features, len(SEVERITY_CLASSES))
        self.stage_head      = nn.Linear(in_features, len(STAGE_CLASSES))
        self.crop_type_head  = nn.Linear(in_features, len(CROP_TYPE_CLASSES))

    def forward(self, x):
        features = self.backbone(x)
        return {
            "condition":  self.condition_head(features),
            "cause":      self.cause_head(features),
            "severity":   self.severity_head(features),
            "stage":      self.stage_head(features),
            "crop_type":  self.crop_type_head(features)
        }