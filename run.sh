#!/bin/bash

set -e

# Call the venv directly: `uv run` re-syncs the env on every start, which only
# widens the window between "pod Running" and "port 8000 open".
export PATH="/app/.venv/bin:$PATH"

# LMS doesn't inject AD_SERVICE_URL (and localhost would be this very pod).
# Services there follow the pattern <namespace>-web.<namespace>, and the
# ad-service namespace differs from ours only by its suffix.
NS_FILE=/var/run/secrets/kubernetes.io/serviceaccount/namespace
if [ -f "$NS_FILE" ] && [[ "${AD_SERVICE_URL:-}" =~ ^(https?://(localhost|127\.0\.0\.1)(:[0-9]+)?/?)?$ ]]; then
    ad_ns="$(sed 's/search-service$/ad-service/' "$NS_FILE")"
    export AD_SERVICE_URL="http://${ad_ns}-web.${ad_ns}.svc.cluster.local:8000"
fi

alembic upgrade head

# The cluster runs a single container per service, so the Kafka consumer lives
# next to the API. It's kept in a restart loop so a Kafka/ad-service hiccup
# never takes /search down with it; uvicorn stays PID 1 and owns signals.
(
    while true; do
        python -m bin.consumer || true
        echo "kafka consumer exited, restarting in 5s" >&2
        sleep 5
    done
) &

exec uvicorn bin.api:app --host 0.0.0.0 --port "${PORT:-8000}"
