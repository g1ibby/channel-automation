# Builder Stage
FROM python:3.11-alpine as builder

WORKDIR /app

COPY pyproject.toml poetry.lock /app/

RUN apk --no-cache add --virtual build-deps gcc musl-dev && \
    pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

# Final Stage
FROM python:3.11-alpine

WORKDIR /app
ENV PYTHONPATH=/app

# Copy only the installed Python packages
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . /app

CMD ["python", "-u", "channel_automation/__main__.py", "bot"]
