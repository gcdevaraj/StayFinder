FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose the Flask port
EXPOSE 4000

# Environment variables
ENV PORT=4000
ENV PYTHONUNBUFFERED=1

# Start the application
CMD ["python", "app.py"]
