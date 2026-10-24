# syntax=docker/dockerfile:1
# Shared Python/uv foundation for development and production builds.
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS base

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
    && apt-get install -y --no-install-recommends ca-certificates curl git \
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
