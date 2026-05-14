import os
import json
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms

# ======================
# LABEL MAPS
# ======================

CONDITION_MAP = {
    "Healthy": 0,
    "Biotic": 1,
    "Abiotic": 2,
    "Unknown": 3
}

CAUSE_MAP = {
    "None": 0,
    "bacterial_leaf_blight": 1,
    "bacterial_leaf_streak": 2,
    "leaf_blast": 3,
    "neck_blast": 4,
    "brown_spot": 5,
    "sheath_blight": 6,
    "sheath_rot": 7,
    "tungro": 8,
    "false_smut": 9,
    "insect_damage": 10,
    "Unknown": 11
}

SEVERITY_MAP = {
    "None": 0,
    "Low": 1,
    "Medium": 2,
    "High": 3,
    "Unknown": 4
}

STAGE_MAP = {
    "Germination": 0,
    "Vegetative": 1,
    "Flowering": 2,
    "Fruiting": 3,
    "PhysiologicalMaturity": 4,
    "Unknown": 5
}

CROP_TYPE_MAP = {
    "paddy": 0,
    "chilli": 1,
    "wheat": 2,
    "rice": 3,
    "tomato": 4,
    "Unknown": 5
}
# ======================
# DATASET
# ======================

class CropDataset(Dataset):
    def __init__(self, json_path, image_dir):
        with open(json_path) as f:
            self.data = json.load(f)

        self.image_dir = image_dir

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                [0.485, 0.456, 0.406],
                [0.229, 0.224, 0.225]
            )
        ])

        print(f"✅ Dataset loaded: {len(self.data)} samples")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]

        # Load image
        img_path = os.path.join(self.image_dir, item["image"])
        image = Image.open(img_path).convert("RGB")
        image = self.transform(image)

        # Labels
        labels = {
            "condition": CONDITION_MAP.get(item["condition"], 3),
            "cause":     CAUSE_MAP.get(item["cause"], 11),
            "severity":  SEVERITY_MAP.get(item["severity"], 4),
            "stage":     STAGE_MAP.get(item["stage"], 5),
            "crop_type": CROP_TYPE_MAP.get(item.get("crop_type", "paddy"), 0)
        }

        return image, labels