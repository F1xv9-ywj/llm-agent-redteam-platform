FROM python:3.11.13-slim@sha256:9e4c8c26dd6ee0b0ed3d4bbfd8046c33ca7f1c3f16f5d52c8de7b31a79709230
WORKDIR /app
RUN useradd --create-home --uid 10001 redsentinel
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir .
USER redsentinel
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"
CMD ["uvicorn", "redsentinel.app:app", "--host", "0.0.0.0", "--port", "8000"]
