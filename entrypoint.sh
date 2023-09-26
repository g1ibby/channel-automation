#!/bin/sh

# Download wait-for-it.sh
wget -O /app/wait-for-it.sh https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh
chmod +x /app/wait-for-it.sh

# Wait for the database to be ready
/app/wait-for-it.sh db:5432 --timeout=30

# Run Alembic Migrations
alembic upgrade head

# Start your application
exec python -u channel_automation/__main__.py botprod
