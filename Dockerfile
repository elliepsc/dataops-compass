FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY dataops_assistant/ ./dataops_assistant/
COPY data/ ./data/

WORKDIR /app/dataops_assistant

EXPOSE 5000

CMD ["python", "app.py"]
