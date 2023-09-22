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

COPY --from=builder /usr/local /usr/local
COPY . /app

CMD ["python", "channel_automation/__main__.py", "bot-prod"]
