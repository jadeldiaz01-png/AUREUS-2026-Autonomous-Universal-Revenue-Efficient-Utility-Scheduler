FROM python:3.12-slim@sha256:0d5d4d8f8b5f2f43b44a6c1db9ebdfe9e69b4acdbfba9f0b12b6c37eab4a47c8
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .
USER 65532:65532
EXPOSE 8000
CMD ["uvicorn", "aureus.api:app", "--host", "0.0.0.0", "--port", "8000"]
