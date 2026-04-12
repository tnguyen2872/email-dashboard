# Start from an official Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements first — Docker caches this layer
# so rebuilds are faster if code changes but dependencies don't
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Tell Docker this app listens on port 5000
EXPOSE 5000

# Default command — run the Flask dashboard
CMD ["python", "app.py"]