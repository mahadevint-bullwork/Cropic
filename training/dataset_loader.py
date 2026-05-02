import json
import os
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms

class CropDataset(Dataset):
    def __init__(self, json_path, image_dir):

        with open(json_path) as f:
            self.data = json.load(f)

        self.image_dir = image_dir

        # Convert labels → numbers
        self.condition_map = {
            "Healthy": 0,
            "Biotic": 1,
            "Abiotic": 2,
            "Unknown": 0
        }

        self.cause_map = {
            "None": 0,
            "leaf_blast": 1,
            "brown_spot": 2,
            "Unknown": 0
        }

        self.severity_map = {
            "None": 0,
            "Low": 1,
            "Medium": 2,
            "High": 3,
            "Unknown": 0
        }

        self.stage_map = {
            "Germination": 0,
            "Vegetative": 1,
            "Flowering": 2,
            "Fruiting": 3,
            "PhysiologicalMaturity": 4,
            "Unknown": 0
        }

        self.transform = transforms.Compose([
            transforms.Resize((224,224)),
            transforms.ToTensor(),
            transforms.Normalize(
                [0.485,0.456,0.406],
                [0.229,0.224,0.225]
            )
        ])

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):

        item = self.data[idx]

        img_path = os.path.join(self.image_dir, item["image"])
        image = Image.open(img_path).convert("RGB")
        image = self.transform(image)

        labels = {
            "condition": self.condition_map.get(item["condition"], 0),
            "cause": self.cause_map.get(item["cause"], 0),
            "severity": self.severity_map.get(item["severity"], 0),
            "stage": self.stage_map.get(item["stage"], 0)
        }

        return image, labels