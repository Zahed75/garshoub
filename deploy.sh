#!/bin/bash
# Fix-everything deployment script
echo "Starting Odoo 19 Production Stabilization..."

# 1. Get latest code
git pull origin main

# 2. Stop containers without destroying volumes (protect database & filestore)
echo "Cleaning old environment..."
docker-compose down

# 3. Rebuild with no cache to ensure package structure is correct
echo "Building Odoo image..."
docker-compose build --no-cache

# 4. Start everything
echo "Starting containers..."
docker-compose up -d

echo "----------------------------------------"
echo "Deployment triggered!"
echo "Check progress with: docker logs -f odoo_app"
echo "----------------------------------------"