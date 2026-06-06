import psycopg2
import sys

def fix_database(db_name, db_user, db_password, db_host, base_url):
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host
        )
        conn.autocommit = True
        cur = conn.cursor()

        print(f"Fixing database: {db_name}")

        # 1. Update web.base.url
        cur.execute("""
            UPDATE ir_config_parameter 
            SET value = %s 
            WHERE key = 'web.base.url';
        """, (base_url,))
        print(f"Updated web.base.url to {base_url}")

        # 2. Freeze web.base.url
        cur.execute("""
            INSERT INTO ir_config_parameter (key, value) 
            VALUES ('web.base.url.freeze', 'True')
            ON CONFLICT (key) DO UPDATE SET value = 'True';
        """)
        print("Set web.base.url.freeze to True")

        # 3. Clear assets (force regeneration)
        cur.execute("DELETE FROM ir_attachment WHERE name LIKE '/web/assets/%';")
        print("Cleared asset attachments")

        # 4. Check admin user
        cur.execute("SELECT id, login, active FROM res_users WHERE id = 2 OR login = 'admin';")
        admin = cur.fetchone()
        if admin:
            print(f"Admin user found: ID={admin[0]}, Login={admin[1]}, Active={admin[2]}")
            if not admin[2]:
                cur.execute("UPDATE res_users SET active = True WHERE id = %s;", (admin[0],))
                print("Activated admin user")
        else:
            print("Warning: Admin user not found!")

        cur.close()
        conn.close()
        print("Database fix completed successfully.")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Parameters for syscoHQ
    fix_database(
        db_name="syscoHQ",
        db_user="odoo",
        db_password="odoo_secure_password",
        db_host="db",
        base_url="https://hq.syscomatic.com"
    )


