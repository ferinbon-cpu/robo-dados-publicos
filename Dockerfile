FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 ROBO_DRIVE_AUTH=oauth-env
WORKDIR /app
COPY . /app
CMD ["python3", "main.py", "run", "--auth", "oauth-env"]
