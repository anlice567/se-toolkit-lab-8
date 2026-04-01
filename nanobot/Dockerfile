# Multi-stage build for nanobot gateway
ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}astral/uv:python3.14-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Install all packages in dependency order (non-editable, no workspace refs)
RUN uv pip install "nanobot-ai @ https://github.com/HKUDS/nanobot/archive/e7d371ec1e6531b28898ec2c869ef338e8dd46ec.zip"

COPY --from=workspace nanobot-websocket-channel/nanobot-channel-protocol /tmp/nanobot-channel-protocol
RUN uv pip install /tmp/nanobot-channel-protocol

COPY --from=workspace nanobot-websocket-channel/mcp-webchat /tmp/mcp-webchat
RUN uv pip install /tmp/mcp-webchat

COPY --from=workspace nanobot-websocket-channel/nanobot-webchat /tmp/nanobot-webchat
RUN uv pip install /tmp/nanobot-webchat

COPY --from=workspace mcp/mcp-lms /tmp/mcp-lms
RUN uv pip install /tmp/mcp-lms

# Copy nanobot source from local context (build context is ./nanobot)
COPY . /app/nanobot
RUN uv pip install /app/nanobot

# --- Runtime stage ---
ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}python:3.14.2-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8

ARG APP_UID=1000
ARG APP_GID=1000

RUN if [ "${APP_UID}" != "0" ]; then \
        groupadd --system --gid "${APP_GID}" appgroup && \
        useradd --system --gid "${APP_GID}" --uid "${APP_UID}" --create-home appuser; \
    else \
        echo "Running as root"; \
    fi

COPY --from=builder --chown=appuser:appgroup /usr/local /usr/local

USER ${APP_UID:-0}
WORKDIR /app

CMD ["python", "/app/nanobot/entrypoint.py"]
