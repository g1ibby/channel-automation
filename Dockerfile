# Use a lighter base image
FROM python:3.11-alpine

# Set the working directory in the container
WORKDIR /app

# Only copy necessary files for installing dependencies
COPY pyproject.toml poetry.lock /app/

# Install poetry, project dependencies, and clean up
RUN apk --no-cache add --virtual build-deps gcc musl-dev && \
    pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev && \
    apk del build-deps

# Copy the rest of the application code
COPY . /app

# Set the command to run your application
CMD ["python", "channel_automation/__main__.py", "bot2"]
