import psycopg2
import os

def fix_attachments(db_name, db_user, db_password, db_host):
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host
        )
        conn.autocommit = True
        cur = conn.cursor()

        print("Checking for broken attachments...")
        
        # 1. Specifically targeting the problematic flags and checklist files
        # It's safer to delete them from DB so Odoo recreates them during -u all
        cur.execute("DELETE FROM ir_attachment WHERE res_model = 'res.lang';")
        print("Deleted res.lang attachments (will be recreated from XML)")

        # 2. Update attachments that have 'checklist/' prefix in their path
        # We moved these to the root in restore_data.sh, so we update the DB to match
        cur.execute("""
            UPDATE ir_attachment 
            SET store_fname = SUBSTRING(store_fname FROM 11) 
            WHERE store_fname LIKE 'checklist/%';
        """)
        print("Updated paths for attachments previously in 'checklist/' folder.")

        # 3. Clean up the checklist table if it exists (internal Odoo table that might be corrupted)
        cur.execute("DELETE FROM ir_attachment WHERE store_fname LIKE 'checklist/%';") # Double check
        
        cur.close()
        conn.close()
        print("Attachment fix completed.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_attachments(
        db_name="syscoHQ",
        db_user="odoo",
        db_password="odoo_secure_password",
        db_host="db"
    )
