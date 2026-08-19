FROM python:3.11-slim

# Install docker-cli to interact with modernwms container via /var/run/docker.sock
RUN apt-get update && apt-get install -y docker-cli --no-install-recommends && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY sync_service.py /app/sync_service.py

EXPOSE 8082

CMD ["python3", "sync_service.py"]
