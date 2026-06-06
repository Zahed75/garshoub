import psycopg2

# Connect to your restored database
conn = psycopg2.connect("dbname='syscoHQ' user='odoo' password='odoo_secure_password' host='db'")
cur = conn.cursor()

print("Updating module versions to allow migration...")
# 1. Lower the version numbers so Odoo 19.0 thinks it can 'upgrade' them
cur.execute("UPDATE ir_module_module SET latest_version = '1.0.0' WHERE state = 'installed';")

# 2. Mark all installed modules for upgrade
cur.execute("UPDATE ir_module_module SET state = 'to upgrade' WHERE state = 'installed';")

conn.commit()
cur.close()
conn.close()
print("Success! Your modules are now ready to be re-activated with your old data.")
