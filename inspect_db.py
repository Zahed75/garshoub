import psycopg2

conn = psycopg2.connect("dbname='syscoHQ' user='odoo' password='odoo_secure_password' host='db'")
cur = conn.cursor()

print("\n--- DATABASE INSPECTION ---")

# Check companies
cur.execute("SELECT id, name FROM res_company;")
companies = cur.fetchall()
print(f"Companies found: {companies}")

# Check users
cur.execute("SELECT id, login, company_id FROM res_users WHERE active=True;")
users = cur.fetchall()
print(f"Active Users: {users}")

# Check for actual data (Partners/Invoices)
cur.execute("SELECT count(*) FROM res_partner;")
partner_count = cur.fetchone()[0]
print(f"Total Partners (Customers/Contacts): {partner_count}")

try:
    cur.execute("SELECT count(*) FROM account_move;")
    invoice_count = cur.fetchone()[0]
    print(f"Total Invoices/Bills: {invoice_count}")
except:
    print("Invoices table not found (module not fully loaded)")

cur.close()
conn.close()
print("--- END INSPECTION ---\n")
