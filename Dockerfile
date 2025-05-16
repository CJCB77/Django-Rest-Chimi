# The base image
FROM python:3.9-alpine3.13
# Is common to set a maintainer people can contact for a docker image
LABEL maintainer="https://johnny-coral-dev.vercel.app/"
# This prevents Python from buffering stdout/stderr, ensuring logs appear immediately
ENV PYTHONUNBUFFERED 1

# Copy requirements file in a temp location
COPY ./requirements.txt /tmp/requirements.txt
# Copy application code in to the /app directory
COPY ./app /app

# Sets the working directory as /app for subsequent commands
WORKDIR /app
# Container will listen on port 8000
EXPOSE 8000

# Run this commands in the terminal
# Creates a python environment
# Upgrades pip within that environment
# Install all requirements from your requirements.txt file 
# Cleans up the /tmp directory to reduce the image size
# Creates a non-root user "django-user" with limited permissions for securit
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    rm -rf /tmp && \
    adduser \
        --disabled-password \
        --no-create-home \
        django-user

# Adds the Python virtual environment's bin directory to the PATH        
ENV PATH="/py/bin:$PATH"

# Switches from root to the limited-privilege django-user
USER django-user