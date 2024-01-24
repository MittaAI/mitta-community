# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Update app-get
RUN apt-get update && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Update pip
RUN pip install --upgrade pip

# Copy the current directory contents into the container at /app
COPY . /app

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable for Flask to run in production mode
ENV FLASK_ENV=production

# Run app.py using Gunicorn on port 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
