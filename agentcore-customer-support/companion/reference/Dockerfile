FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 UV_NO_PROGRESS=1 DOCKER_CONTAINER=1 \
    AWS_REGION=us-east-1 AWS_DEFAULT_REGION=us-east-1
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
ENV PATH="/app/.venv/bin:$PATH"
COPY main.py ./
RUN useradd -m -u 1000 bedrock_agentcore
USER bedrock_agentcore
EXPOSE 8080
CMD ["python", "-m", "main"]
