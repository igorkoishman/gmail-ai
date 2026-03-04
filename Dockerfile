FROM python:3.9-slim

WORKDIR /app

# Install system dependencies if any are needed (MySQL client libs etc)
RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt mysql-connector-python

# Copy application files
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1

# Command to run the service
CMD ["python", "main_pro.py", "--service"]
