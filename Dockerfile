# syntax=docker/dockerfile:1.7

FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Minimal runtime dependencies and certificates.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy runtime code only (dev artifacts are excluded by .dockerignore)
COPY . .

# Runtime writable paths for read-only rootfs deployments.
RUN mkdir -p /data /tmp \
    && useradd --create-home --uid 65532 --shell /usr/sbin/nologin botuser \
    && chown -R 65532:65532 /app /data /tmp

USER 65532:65532

ENV BOT_DB_PATH=/data/bot_state.db

ENTRYPOINT ["python", "bot.py"]
CMD ["doctor"]
