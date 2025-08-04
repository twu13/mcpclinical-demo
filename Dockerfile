############### builder: deps only ###############
FROM ghcr.io/astral-sh/uv:0.8.3-python3.12-bookworm-slim AS builder

WORKDIR /app
COPY pyproject.toml uv.lock ./

# Install dependencies (project code added later)
RUN uv sync --locked --no-install-project --compile-bytecode

############### final image ###############
FROM python:3.12-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    ca-certificates \
    make \
    && rm -rf /var/lib/apt/lists/*

# Install ngrok
RUN curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | gpg --dearmor > /etc/apt/trusted.gpg.d/ngrok.gpg && \
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" > /etc/apt/sources.list.d/ngrok.list && \
    apt-get update && apt-get install -y ngrok && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Bring in the ready virtualenv
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy project files
COPY *.py .
COPY icon/ icon/
COPY support/ support/
COPY Makefile .
COPY README.md .

# Expose ports for Streamlit and MCP server
EXPOSE 8501 8000 4040

# Create entrypoint script
RUN echo '#!/bin/bash\n\
if [ -n "$NGROK_AUTHTOKEN" ]; then\n\
  ngrok config add-authtoken $NGROK_AUTHTOKEN\n\
fi\n\
make dev\n' > /app/entrypoint.sh && \
chmod +x /app/entrypoint.sh

# Start the application in development mode
ENTRYPOINT ["/app/entrypoint.sh"]