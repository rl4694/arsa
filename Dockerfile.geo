FROM python:3.13-slim

WORKDIR /app

# Install git and curl just in case
RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install --no-cache-dir geopy

CMD ["bash"]
