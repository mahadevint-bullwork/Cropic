import os
import xml.etree.ElementTree as ET
import shutil
import random

xml_path = "annotations.xml"
images_dir = "images"
output_dir = "dataset"

split_ratio = 0.8

tree = ET.parse(xml_path)
root = tree.getroot()

data = []

for image in root.findall("image"):
    img_name = image.get("name")

    box = image.find("box")
    if box is None:
        continue

    condition = None
    cause = None

    for attr in box.findall("attribute"):
        if attr.get("name") == "condition_type":
            condition = attr.text
        if attr.get("name") == "cause":
            cause = attr.text

    # 🔥 LABEL LOGIC
    if condition == "Healthy":
        label = "healthy"
    elif condition == "Biotic":
        label = cause
    elif condition == "Abiotic":
        label = cause
    else:
        continue

    data.append((img_name, label))

# shuffle
random.shuffle(data)

split_index = int(len(data) * split_ratio)

train_data = data[:split_index]
val_data = data[split_index:]

def copy_data(dataset, split_name):
    for img_name, label in dataset:
        dest = os.path.join(output_dir, split_name, label)
        os.makedirs(dest, exist_ok=True)

        src = os.path.join(images_dir, img_name)
        dst = os.path.join(dest, img_name)

        shutil.copy(src, dst)

copy_data(train_data, "train")
copy_data(val_data, "val")

print("✅ Dataset created")