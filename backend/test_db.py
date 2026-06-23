import psycopg2

try:
    conn = psycopg2.connect("postgresql://archaeon:archaeon@localhost:5432/archaeon")
    print("✅ Database connected successfully!")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")