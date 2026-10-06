#!/bin/bash

set -e

uv run alembic upgrade head
exec uv run uvicorn bin.api:app --host 0.0.0.0 --port "${PORT:-8000}"
