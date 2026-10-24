# syntax=docker/dockerfile:1
# Shared Python/uv foundation for development and production builds.
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

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl gh git \
    && rm -rf /var/lib/apt/lists/*

USER app

# Keep the workspace available before an application server is implemented.
CMD ["sleep", "infinity"]

FROM base AS production

COPY --chown=root:root . /app

RUN uv sync --locked --no-dev \
    && chown root:root /app

ENV PATH="/app/.venv/bin:${PATH}"

USER app

EXPOSE 2158

CMD ["gunicorn", "--bind", "0.0.0.0:2158", "--access-logfile", "-", "--no-control-socket", "linkscope.wsgi:application"]
