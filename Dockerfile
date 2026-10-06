FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_DEV=1 \
    UV_FROZEN=1 \
    PYTHONPATH=/app

# uv goes to /usr/local/bin so it is on PATH for any UID, not just root.
RUN pip install --no-cache-dir uv

# The cluster runs pods as UID 1000 (runAsNonRoot), so build and run as that user.
RUN addgroup --system --gid 1000 appuser \
    && adduser --system --uid 1000 --home /home/appuser --ingroup appuser appuser

WORKDIR /app
RUN chown appuser:appuser /app
USER appuser

COPY --chown=appuser:appuser pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY --chown=appuser:appuser . .

RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["bash", "./run.sh"]
