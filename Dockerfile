FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    HF_HOME=/models/huggingface

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl libgomp1 libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 app \
    && mkdir -p /models/huggingface \
    && chown -R app:app /models

COPY requirements.txt .
RUN pip --timeout 120 --retries 10 install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu


COPY --chown=app:app src ./src
COPY --chown=app:app scripts ./scripts
COPY --chown=app:app tests ./tests
COPY --chown=app:app start.sh .
RUN chmod +x /app/start.sh

EXPOSE 8000 8501

USER app
CMD ["/app/start.sh"]
