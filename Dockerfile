FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set output to local persistent storage if run via docker run -v
VOLUME /app/output

CMD ["python", "main.py", "--config", "config.yaml"]
