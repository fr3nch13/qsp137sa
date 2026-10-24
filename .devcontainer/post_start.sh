#!/usr/bin/env bash
set -euo pipefail

# Start the auto-reloading development server without blocking container setup.

echo "Running post-start script..."
cd "$(dirname "${BASH_SOURCE[0]}")/.."

state_dir="${HOME}/.cache/linkscope"
mkdir -p "${state_dir}"
log_file="${state_dir}/runserver.log"

if ! exec 3>/proc/1/fd/1; then
    echo "Cannot access container stdout through /proc/1/fd/1." >&2
    exit 1
fi

# flock holds the lock for the server's lifetime, including Django's reloader.
nohup flock --nonblock --conflict-exit-code 73 "${state_dir}/runserver.lock" \
    bash -c 'set -o pipefail; uv run --locked python manage.py runserver 0.0.0.0:2158 2>&1 | tee -a "$1"' \
    bash "${log_file}" \
    >&3 2>&1 3>&- </dev/null &
server_pid=$!
exec 3>&-

for ((attempt = 0; attempt < 60; attempt++)); do
    if ! kill -0 "${server_pid}" 2>/dev/null; then
        status=0
        wait "${server_pid}" || status=$?
        if [ "${status}" -eq 73 ]; then
            echo "Development server already starting or running. Logs: ${log_file}"
            exit 0
        fi
        echo "Development server exited unexpectedly (status ${status})." >&2
        tail -n 30 "${log_file}" >&2
        exit 1
    fi
    if curl --fail --silent --output /dev/null http://127.0.0.1:2158/; then
        echo "Development server available on port 2158. Logs: ${log_file}"
        exit 0
    fi
    sleep 0.5
done

echo "Development server did not become ready within 30 seconds. Logs: ${log_file}" >&2
tail -n 30 "${log_file}" >&2
exit 1
