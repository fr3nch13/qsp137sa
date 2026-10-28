# syntax=docker/dockerfile:1
# Shared Python/uv foundation for development and production builds.
FROM node:24-bookworm-slim AS node-toolchain

COPY frontend/run-checked.mjs /opt/linkscope/run-checked.mjs

FROM node-toolchain AS application-build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json frontend/.npmrc ./
RUN node /opt/linkscope/run-checked.mjs npm ci
COPY frontend/ ./
RUN node /opt/linkscope/run-checked.mjs npm run build

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS base

LABEL org.opencontainers.image.title="LinkScope" \
    org.opencontainers.image.description="Network resilience analysis for a European backbone network and its connected sites and data centers." \
    org.opencontainers.image.url="https://github.com/fr3nch13/qsp137sa" \
    org.opencontainers.image.documentation="https://github.com/fr3nch13/qsp137sa#readme" \
    org.opencontainers.image.source="https://github.com/fr3nch13/qsp137sa"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy

WORKDIR /app

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --create-home --home-dir /home/app app \
    && chown app:app /app

FROM base AS development

COPY --from=node-toolchain /usr/local/bin/node /usr/local/bin/node
COPY --from=node-toolchain /usr/local/lib/node_modules /usr/local/lib/node_modules

# Chromium lets Marp export the slide deck (docs/slideshow) to PDF and PPTX.
ENV CHROME_PATH=/usr/bin/chromium

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates chromium curl gh git \
    && ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx \
    && rm -rf /var/lib/apt/lists/*

USER app

# Keep the workspace available before an application server is implemented.
CMD ["sleep", "infinity"]

FROM base AS production

COPY --chown=root:root . /app
COPY --from=application-build --chown=root:root /frontend/dist /app/frontend/dist

RUN uv sync --locked --no-dev \
    && chown root:root /app

ENV PATH="/app/.venv/bin:${PATH}"

USER app

EXPOSE 2158

CMD ["gunicorn", "--bind", "0.0.0.0:2158", "--access-logfile", "-", "--no-control-socket", "linkscope.wsgi:application"]
