import psycopg2

# Connect to the blink database
conn = psycopg2.connect(
    dbname="blink",
    user="postgres",
    password="minhduc456",  # Use the password you set
    host="localhost",
    port="5432"
)

# Test the connection
cursor = conn.cursor()
cursor.execute("SELECT 1")
print("Connected to PostgreSQL, fam!")
cursor.close()
conn.close()