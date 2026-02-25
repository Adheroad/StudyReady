# 🐍 Use a fast, stable base image (RHEL-compatible)
FROM rockylinux:9

# 🧩 Set working directory
WORKDIR /app

# 🧰 Install system dependencies
RUN dnf -y install \
    python3 python3-pip python3-devel gcc git poppler-utils \
    mesa-libGL libglvnd-glx \
    && dnf clean all

# 🧩 Copy requirements
COPY Backend/requirements.txt ./requirements.txt

# 🧩 Install Python dependencies
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# ✅ Ensure Paddle backend and OCR libraries are available
RUN pip install --no-cache-dir layoutparser[paddledetection] easyocr opencv-python-headless pdf2image numpy

# 🧩 Copy backend service code
COPY Backend/services ./services

# 🧩 Switch working directory
WORKDIR /app/services

# 🧩 Expose FastAPI port
EXPOSE 8000

# 🧠 Start Uvicorn server
CMD ["python3", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
