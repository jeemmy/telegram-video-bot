# ── Stage 1: Base ──
FROM python:3.11-slim AS base
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg curl gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Development ──
FROM base AS development
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
CMD ["python", "bot/main.py"]

# ── Stage 3: Production ──
FROM base AS production
COPY . .
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser
CMD ["python", "bot/main.py"]
