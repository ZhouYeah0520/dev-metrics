FROM python:3.12-slim
WORKDIR /app
COPY . .
ENV PYTHONPATH=/app/src
CMD ["python", "-m", "dev_metrics", "--help"]
