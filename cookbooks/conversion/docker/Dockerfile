# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install Quart and Hypercorn
RUN pip install quart hypercorn
RUN pip install httpx
RUN pip install quart-cors
RUN pip install google-cloud-pubsub

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV QUART_APP=app:app
ENV QUART_ENV=production

# Run app.py using Hypercorn
CMD ["hypercorn", "--bind", "0.0.0.0:5000", "app:app"]
