# Use official Python slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /src

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install basic system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
RUN apt update && apt install -y git

# Copy only what's needed
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the actual src code
COPY ./src ./src

# Set default command (optional)
CMD ["python", "src/main.py"]