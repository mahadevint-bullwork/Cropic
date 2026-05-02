import xml.etree.ElementTree as ET
import json

tree = ET.parse("annotations.xml")
root = tree.getroot()

data = []

for image in root.findall("image"):
    box = image.find("box")
    if box is None:
        continue

    item = {
        "image": image.get("name"),
        "condition": "Unknown",
        "cause": "Unknown",
        "severity": "Unknown",
        "stage": "Unknown"
    }

    for attr in box.findall("attribute"):
        name = attr.attrib["name"]
        value = attr.text

        if name == "condition_type":
            item["condition"] = value
        elif name == "cause":
            item["cause"] = value
        elif name == "severity":
            item["severity"] = value
        elif name == "growth_stage":
            item["stage"] = value

    data.append(item)

with open("dataset.json", "w") as f:
    json.dump(data, f, indent=4)

print("✅ dataset.json created")