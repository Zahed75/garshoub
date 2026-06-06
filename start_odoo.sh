#!/bin/bash

# Activate the virtual environment
source venv/bin/activate

# Start Odoo with the specified configuration file
# Note: If this is the first time you are running it, you may need to initialize the database
# by appending '-d odooZayanori -i base' to the command below.
python -m odoo -c odoo.conf -d odooZayanori
