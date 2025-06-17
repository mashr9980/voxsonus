FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# ENV WORKERS=$(expr $(nproc) \* 2 + 1)
# Default command
CMD ["sh", "-c", "gunicorn app.main:app -k uvicorn.workers.UvicornWorker --workers 25 --bind 0.0.0.0:8000"]
