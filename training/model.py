import torch.nn as nn
from torchvision import models

class MultiHeadModel(nn.Module):
    def __init__(self):
        super().__init__()

        # Backbone
        self.backbone = models.efficientnet_b0(weights="IMAGENET1K_V1")
        in_features = self.backbone.classifier[1].in_features

        # Remove original classifier
        self.backbone.classifier = nn.Identity()

        # Heads (IMPORTANT: sizes must match your mappings)
        self.condition_head = nn.Linear(in_features, 3)   # Healthy, Biotic, Abiotic
        self.cause_head = nn.Linear(in_features, 3)       # None, leaf_blast, brown_spot
        self.severity_head = nn.Linear(in_features, 4)    # None, Low, Medium, High
        self.stage_head = nn.Linear(in_features, 5)       # 5 stages

    def forward(self, x):
        features = self.backbone(x)

        return {
            "condition": self.condition_head(features),
            "cause": self.cause_head(features),
            "severity": self.severity_head(features),
            "stage": self.stage_head(features)
        }