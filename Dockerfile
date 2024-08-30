# Use the official Python image from the Docker Hub
FROM python:3.11-alpine

# Set the working directory in the container
WORKDIR /app

ENV PYTHONUNBUFFERED 1

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .
