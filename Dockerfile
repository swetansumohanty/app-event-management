FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the wait script and make it executable
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Create a startup script
RUN echo '#!/bin/bash\n\
    sleep 20\n\
    /wait-for-it.sh db\n\
    python init_db.py\n\
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload' > /start.sh && \
    chmod +x /start.sh

# Command to run the application
CMD ["/start.sh"] 