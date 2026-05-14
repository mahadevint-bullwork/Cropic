import os
import re
import xml.etree.ElementTree as ET
import json

# ======================
# CONFIG
# ======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANNOTATIONS_PATH = os.path.join(BASE_DIR, "annotations.xml")
OUTPUT_PATH = os.path.join(BASE_DIR, "dataset.json")

# ======================
# PARSE XML (handle multiple task XMLs concatenated)
# ======================
print("📄 Parsing annotations.xml...")

with open(ANNOTATIONS_PATH, "r") as f:
    content = f.read()

# Wrap multiple XML docs into one root
content = re.sub(r'<\?xml[^?]*\?>', '', content)
content = re.sub(r'<annotations>', '', content)
content = re.sub(r'</annotations>', '', content)
content = f"<?xml version='1.0'?><annotations>{content}</annotations>"

root = ET.fromstring(content)

data = []

for image in root.findall("image"):
    img_name = image.get("name")

    for box in image.findall("box"):
        if box.get("label") != "paddy":
            continue

        item = {
            "image": img_name,
            "crop_type": "paddy",
            "condition": "Unknown",
            "cause": "None",
            "severity": "None",
            "stage": "Unknown",
            "confidence": "Certain"
        }

        for attr in box.findall("attribute"):
            name = attr.get("name")
            value = attr.text

            if name == "condition_type":
                item["condition"] = value
            elif name == "cause":
                item["cause"] = value
            elif name == "severity":
                item["severity"] = value
            elif name == "growth_stage":
                item["stage"] = value
            elif name == "annotator_confidence":
                item["confidence"] = value
            elif name == "crop_type":
                item["crop_type"] = value

        data.append(item)

# ======================
# FILTER - only Certain annotations
# ======================
print(f"Total annotations: {len(data)}")
data = [d for d in data if d["confidence"] == "Certain"]
print(f"After filtering uncertain: {len(data)}")

# ======================
# SAVE
# ======================
with open(OUTPUT_PATH, "w") as f:
    json.dump(data, f, indent=4)

print(f"\n✅ dataset.json created at {OUTPUT_PATH}")
print(f"Total samples: {len(data)}")

if data:
    print(f"\nSample entry:")
    print(json.dumps(data[0], indent=4))