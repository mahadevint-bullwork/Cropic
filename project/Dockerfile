FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3 python3-pip curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean

WORKDIR /app

# Copy from Cropic root
COPY project/server.js project/inference.py project/requirements.txt project/imagenet_classes.txt ./
COPY project/auto_assign.py project/export_from_cvat.py project/prepare_dataset.py ./
COPY run_pipeline.py ./
COPY training/train.py training/model.py training/dataset_loader.py ./training/
COPY project/start.sh ./

RUN pip3 install torch torchvision pillow numpy requests python-dotenv
RUN npm install express multer cors
RUN mkdir -p uploads logs
RUN chmod +x start.sh

EXPOSE 3000

CMD ["./start.sh"]