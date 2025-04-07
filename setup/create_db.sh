#!/bin/bash

# Check if the container already exists
if [ "$(docker ps -aq -f name=track-vul-db)" ]; then
    echo "Container 'track-vul-db' already exists. Stopping and removing it..."
    docker stop track-vul-db
    docker rm track-vul-db
fi

# Run the Docker container
echo "Starting PostgreSQL container..."
docker run --name track-vul-db \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=admin \
  -e POSTGRES_DB=track-vul \
  -p 5434:5432 \
  -v track-vul-data:/var/lib/postgresql/data \
  -d postgres

echo "PostgreSQL container 'track-vul-db' is now running!"

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to initialize..."
until docker exec track-vul-db pg_isready -U admin -d track-vul > /dev/null 2>&1; do
  echo "Waiting for database connection..."
  sleep 1
done

echo "PostgreSQL is ready!"

# continue with more setup stuff !!