# Start from a base Python image with PyTorch installed. PyTorch images are large, so choose the appropriate base.
FROM pytorch/pytorch:latest

# Set a working directory inside the container
WORKDIR /app

# Copy your Python scripts and PowerShell script into the container
COPY . /app

# Install system dependencies (if any)
# For example, if you need to install dependencies for opencv-python
RUN apt-get update && apt-get install -y libgl1-mesa-glx ffmpeg && rm -rf /var/lib/apt/lists/*

# Upgrade pip to ensure we can install the latest packages
RUN pip install --upgrade pip

# Install Python dependencies
# Include any other specific package versions if necessary
RUN pip install doctr[torch] PyMuPDF

# Expose port 5000 for your application (if it's a web service)
EXPOSE 5000

# Use a shell form of CMD to ensure the container stays alive, making it easier to exec into
CMD ["sleep", "infinity"]
