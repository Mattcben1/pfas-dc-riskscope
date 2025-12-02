FROM python:3.11-slim

# Set working directory
WORKDIR /app
ENV PYTHONPATH="/app:/app/src"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .
COPY public/ /app/public/

# Expose FastAPI port
EXPOSE 8080

# Start FastAPI using uvicorn
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
