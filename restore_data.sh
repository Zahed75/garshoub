#!/bin/bash

# Configuration
DB_NAME="syscoHQ"
DUMP_DIR="syscomatic.dump"
DUMP_SQL="$DUMP_DIR/dump.sql"
FILESTORE_DIR="$DUMP_DIR/filestore"
CONTAINER_DB="odoo_postgres"
CONTAINER_APP="odoo_app"
DB_USER="odoo"

# Check for merge mode
if [ "$1" == "--merge" ]; then
    echo "==========================================="
    echo "Odoo Data Merge Mode"
    echo "==========================================="
    echo "[1/3] Clearing existing schema in 'syscoHQ'..."
    docker exec -u root odoo_postgres psql -U odoo -d syscoHQ -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
    
    echo "[2/3] Cleaning SQL dump..."
    python3 clean_dump.py syscomatic.dump/dump.sql
    
    echo "[3/3] Importing migrated data into 'syscoHQ'..."
    # The cleaned file is created as [filename].clean
    docker exec -i odoo_postgres psql -U odoo -d syscoHQ < syscomatic.dump/dump.sql.clean
    
    echo "Merge complete! Restarting Odoo..."
    exit 0
fi

echo "==========================================="
echo "Odoo Data Restoration Script"
echo "==========================================="

# Check if dump file exists
if [ ! -f "$DUMP_SQL" ]; then
    echo "Error: $DUMP_SQL not found!"
    exit 1
fi

# 1. Create database in Postgres
echo "[1/4] Creating database '$DB_NAME' in container '$CONTAINER_DB'..."
docker exec -t $CONTAINER_DB psql -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS \"$DB_NAME\";"
docker exec -t $CONTAINER_DB psql -U $DB_USER -d postgres -c "CREATE DATABASE \"$DB_NAME\";"

# 1.5 Clean the dump (Remove proprietary \restrict commands)
echo "[1.5/4] Cleaning SQL dump..."
python3 clean_dump.py

# 2. Restore SQL dump
echo "[2/4] Restoring SQL dump into '$DB_NAME'... This might take a few minutes."
# Use -i without -t for piping
docker exec -i $CONTAINER_DB psql -U $DB_USER -d "$DB_NAME" < "$DUMP_SQL"

# 3. Restore Filestore
echo "[3/4] Copying filestore to container '$CONTAINER_APP'..."
docker exec -t $CONTAINER_APP mkdir -p /var/lib/odoo/filestore/"$DB_NAME"
docker cp "$FILESTORE_DIR/." $CONTAINER_APP:/var/lib/odoo/filestore/"$DB_NAME"/

# 4. Fix permissions and structure
echo "[4/4] Fixing filestore structure and permissions..."
# 4.1 Move files out of 'checklist' folder if it exists (Odoo 19.2 vs 19.0 conflict)
docker exec -u root -t $CONTAINER_APP bash -c "if [ -d /var/lib/odoo/filestore/$DB_NAME/checklist ]; then 
    echo 'Moving files from checklist subfolder...';
    cp -rn /var/lib/odoo/filestore/$DB_NAME/checklist/* /var/lib/odoo/filestore/$DB_NAME/ 2>/dev/null;
    rm -rf /var/lib/odoo/filestore/$DB_NAME/checklist;
fi"

# 4.2 Ensure the checklist folder exists for Odoo 19.0 GC and set ownership
docker exec -u root -t $CONTAINER_APP mkdir -p /var/lib/odoo/filestore/"$DB_NAME"/checklist
docker exec -u root -t $CONTAINER_APP chown -R odoo:odoo /var/lib/odoo/filestore/"$DB_NAME"

echo "==========================================="
echo "Success! Restoration complete."
echo "Please restart your Odoo container to ensure all changes take effect:"
echo "docker-compose restart odoo"
echo "==========================================="
