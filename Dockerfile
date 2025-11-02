FROM fedora:42

WORKDIR /app

RUN dnf -y upgrade && dnf -y install \
    python3 \
    python3-pip \
    tesseract \
    tesseract-langpack-eng \
    poppler-utils \
    coreutils \
    util-linux \
    findutils \
    which \
    && dnf clean all

COPY Backend/requrement.txt .
RUN pip install --no-cache-dir -r requrement.txt

COPY Backend/services ./services

EXPOSE 8000
WORKDIR /app/services

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
