# Use the official Python image as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create and set the working directory
WORKDIR /app

# Copy project files
COPY . /app/

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for Django
EXPOSE 8000

# Run the app
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
