# Uses slim buster for development
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Upgrade pip, setuptools, and wheel, and install required Python packages
RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install easyocr

# Install Quart and Hypercorn
RUN pip install --no-cache-dir quart httpx werkzeug hypercorn quart_cors

# Copy the Python requirements file and test scripts into the container
COPY . /app/

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV OCR_APP=app:app
ENV OCR_ENV=production

# Run app.py using Hypercorn
CMD ["hypercorn", "--bind", "0.0.0.0:5000", "app:app"]
