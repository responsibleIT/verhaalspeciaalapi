# Use a lightweight Python image
FROM python:3.9-slim

# Set a working directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your Flask code into the container
COPY . .

# Expose port 5000
EXPOSE 5000

# Allow overriding the port with an environment variable
ENV PORT=5000

# Run the Flask app
CMD ["python", "app.py"]
