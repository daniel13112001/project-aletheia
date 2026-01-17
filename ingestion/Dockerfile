FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy everything from project root
COPY . .

RUN pip install --no-cache-dir -r ingestion/requirements.txt

ENTRYPOINT ["python", "-m", "ingestion.ingest"]
CMD []
