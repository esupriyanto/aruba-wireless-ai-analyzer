FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi>=0.104.0 \
    uvicorn[standard]>=0.24.0 \
    httpx>=0.25.0 \
    pyyaml>=6.0

# Copy Hermes agent config and tools
COPY agent_config.yaml .
COPY prompts/ prompts/
COPY tools/ tools/

# Create non-root user
RUN adduser --disabled-password --gecos '' hermes && chown -R hermes:hermes /app
USER hermes

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

CMD ["uvicorn", "tools.hermes_server:app", "--host", "0.0.0.0", "--port", "8080"]
