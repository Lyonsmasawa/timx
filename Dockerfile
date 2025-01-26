# Use an official Python runtime as a parent image
FROM python:3.11.4-alpine

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /usr/src/app

# Install system dependencies for WeasyPrint
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    gobject-introspection-dev \
    cairo-dev \
    pango-dev \
    gdk-pixbuf-dev \
    jpeg-dev \
    zlib-dev

RUN pip install --upgrade pip

# Copy only requirements to leverage Docker cache
COPY ./requirements.txt /usr/src/app/

# Install dependencies
RUN pip install -r requirements.txt

# create unprivileged user
# RUN adduser --disabled-password --gecos '' myuser

COPY ./entrypoint.sh /usr/src/app/entrypoint.sh

# Copy the rest of the application code
COPY . /usr/src/app/

ENTRYPOINT [ "/usr/src/app/entrypoint.sh" ]