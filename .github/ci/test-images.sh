#!/usr/bin/env bash
# Smoke-test both built images before the production image can be published.
set -euo pipefail

development="linkscope-development-${GITHUB_RUN_ID:-local}"
production="linkscope-production-${GITHUB_RUN_ID:-local}"
export DJANGO_SECRET_KEY
DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')"

cleanup() {
    local status=$?
    trap - EXIT
    for container in "${development}" "${production}"; do
        if docker container inspect "${container}" >/dev/null 2>&1; then
            docker logs "${container}"
            docker rm --force "${container}" >/dev/null
        fi
    done
    exit "${status}"
}
trap cleanup EXIT

for image in linkscope:development linkscope:production; do
    test "$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.title"}}' "${image}")" = "LinkScope"
    test "$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.description"}}' "${image}")" = \
        "Network resilience analysis for a European backbone network and its connected sites and data centers."
done

wait_for_http() {
    local container=$1
    local port=$2
    local code
    for ((attempt = 0; attempt < 60; attempt++)); do
        if [ "$(docker inspect --format '{{.State.Running}}' "${container}")" != true ]; then
            echo "${container} stopped before becoming ready." >&2
            return 1
        fi
        code="$(curl --silent --output /dev/null --write-out '%{http_code}' \
            --max-time 2 "http://127.0.0.1:${port}/")" || code=000
        if [ "${code}" = 200 ]; then
            echo "${container} returned HTTP 200."
            return 0
        fi
        sleep 1
    done
    echo "${container} did not return HTTP 200 within 60 attempts." >&2
    return 1
}

docker run --detach --name "${development}" \
    --mount "type=bind,source=${PWD},target=/app,readonly" \
    --env DJANGO_SECRET_KEY --env UV_PROJECT_ENVIRONMENT=/tmp/linkscope-venv \
    --publish 127.0.0.1:2158:2158 linkscope:development
docker exec "${development}" gh --version
docker exec "${development}" uv sync --locked
docker exec "${development}" uv run --locked python manage.py check
docker exec "${development}" uv run --locked python manage.py test linkscope
docker exec "${development}" bash .devcontainer/post_start.sh
docker exec "${development}" bash .devcontainer/post_start.sh
wait_for_http "${development}" 2158
docker exec "${development}" test -s /home/app/.cache/linkscope/runserver.log

docker run --detach --name "${production}" --env DJANGO_SECRET_KEY \
    --publish 127.0.0.1:2159:2158 linkscope:production
wait_for_http "${production}" 2159
docker exec "${production}" python manage.py check
docker exec "${production}" python manage.py test linkscope
docker exec "${production}" python -c '
import os
from pathlib import Path
assert os.getuid() == 10001
assert Path.home() == Path("/home/app")
assert not os.access("/app", os.W_OK)
assert not Path("/app/.env").exists()
assert not Path("/app/.git").exists()
import django
from topohub.providers.sndlib import SNDlibGenerator
'
