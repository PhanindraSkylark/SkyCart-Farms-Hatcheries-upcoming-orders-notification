# Python 3.12 + pymssql/FreeTDS (same stack as Sales Reports Email on VM).
# Build: docker build -t phanindra004/skylark-chicks-delivery-sms:latest .
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Kolkata \
    PYTHONPATH=/code \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    freetds-dev \
    freetds-bin \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY requirements.txt ./
RUN pip install --upgrade pip wheel && \
    pip install -r requirements.txt

COPY . .

CMD ["python", "scripts/delivery_worker.py"]
