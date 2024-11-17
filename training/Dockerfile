# Use an official Python image as the base
FROM python:3.10-slim

# Set up environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*



# Set the working directory in the container
WORKDIR /app
RUN mkdir var && cd var && mkdir nfs && cd ..
ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

# Install the ultralytics library 
RUN pip install --upgrade pip && pip install ultralytics && pip install pyyaml

# Copy your script into the container
COPY . /app

# Command to run the training script
CMD ["python", "train.py" ]
