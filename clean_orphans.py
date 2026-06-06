import psycopg2

conn = psycopg2.connect("dbname='syscoHQ' user='odoo' password='odoo_secure_password' host='db'")
cur = conn.cursor()

print("Running NUCLEAR Cleanup (Bypassing Constraints)...")

# Disable all triggers and foreign keys for this session
cur.execute("SET session_replication_role = 'replica';")

# 1. Ensure a Company exists with ID 1
cur.execute("SELECT id FROM res_company WHERE id = 1;")
if not cur.fetchone():
    print("Forcing Company ID 1...")
    cur.execute("INSERT INTO res_partner (id, name, display_name, active) VALUES (1, 'Sysco HQ', 'Sysco HQ', true) ON CONFLICT (id) DO NOTHING;")
    cur.execute("INSERT INTO res_company (id, name, partner_id, currency_id) VALUES (1, 'Sysco HQ', 1, 1) ON CONFLICT (id) DO NOTHING;")
    cur.execute("UPDATE res_partner SET company_id = 1 WHERE id = 1;")

# 2. Ensure Admin User exists with ID 1
cur.execute("SELECT id FROM res_users WHERE id = 1;")
if not cur.fetchone():
    print("Forcing Admin User ID 1...")
    # Check if we have any user we can promote to ID 1
    cur.execute("SELECT id FROM res_users WHERE login = 'admin' OR id = 2 LIMIT 1;")
    user_row = cur.fetchone()
    if user_row:
        cur.execute("UPDATE res_users SET id = 1, active = true, login = 'admin', company_id = 1 WHERE id = %s;", (user_row[0],))
    else:
        cur.execute("""
            INSERT INTO res_users (id, login, partner_id, company_id, active, notification_type, state) 
            VALUES (1, 'admin', 1, 1, true, 'email', 'active')
            ON CONFLICT (id) DO NOTHING;
        """)

# 3. Wipe blocking metadata
cur.execute("TRUNCATE res_country_state CASCADE;")
cur.execute("DELETE FROM ir_module_module WHERE state = 'to upgrade';")
cur.execute("UPDATE ir_module_module SET state = 'installed' WHERE name = 'base';")

# 4. Fix critical missing not-null values that block startup
# We'll set 'autopost_bills' to 'never' (default) if it exists
try:
    cur.execute("UPDATE res_partner SET autopost_bills = 'never' WHERE autopost_bills IS NULL;")
except:
    conn.rollback()
    cur.execute("SET session_replication_role = 'replica';")

conn.commit()
cur.close()
conn.close()
print("Nuclear cleanup finished. Try starting Odoo now.")
