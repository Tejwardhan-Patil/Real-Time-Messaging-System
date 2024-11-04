# Base image for Python
FROM python:3.9-slim

# Set environment variables for the container
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any necessary dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the necessary port
EXPOSE 8080

# Define the default command to run the application
CMD ["python", "MessageQueue.py"]