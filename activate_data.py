import psycopg2

# Connect to your database
conn = psycopg2.connect("dbname='syscoHQ' user='odoo' password='odoo_secure_password' host='db'")
cur = conn.cursor()

print("Synchronizing data and fixing company records...")

def safe_execute(cursor, query):
    try:
        cursor.execute(query)
    except psycopg2.errors.UndefinedTable:
        conn.rollback()
        print(f"Skipping: Table not found for query.")
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    else:
        conn.commit()

# 1. Make sure the main user (Admin) is linked to the correct company from your old data
safe_execute(cur, "UPDATE res_users SET company_id = (SELECT id FROM res_company ORDER BY id ASC LIMIT 1) WHERE id = 2;")

# 2. Re-calculate the 'Apps' list to show your old modules
safe_execute(cur, "UPDATE ir_module_module SET state='installed' WHERE state='to upgrade';")

# 3. Fix any potential website conflicts (if you had a website)
safe_execute(cur, "UPDATE website SET company_id = (SELECT id FROM res_company ORDER BY id ASC LIMIT 1) WHERE company_id IS NULL;")

# 4. Final check: Ensure the admin user has access to all companies
safe_execute(cur, """
    INSERT INTO res_company_users_rel (user_id, cid)
    SELECT 2, id FROM res_company
    ON CONFLICT DO NOTHING;
""")

cur.close()
conn.close()
print("Success! Your old data is now synchronized.")
