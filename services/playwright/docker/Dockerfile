# Use the official Playwright Python image
FROM mcr.microsoft.com/playwright/python:v1.30.0-focal

# Set the working directory in the container
WORKDIR /app

# Upgrade pip, setuptools, and wheel, and install required Python packages
RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install openai openai[datalib] tenacity

# Install Quart and Hypercorn
RUN pip install --no-cache-dir quart httpx werkzeug hypercorn quart_cors

# Install all browsers supported by this version of Playwright
RUN playwright install

# Copy the Python requirements file and test scripts into the container
COPY . /app/

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV QUART_APP=app:app
ENV QUART_ENV=production

# Run app.py using Hypercorn
CMD ["hypercorn", "--bind", "0.0.0.0:5000", "app:app"]
