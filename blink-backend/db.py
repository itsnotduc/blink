# Create a connection pool for managing database connections (03/05/2025 - Duc Nguyen)

import psycopg2
from psycopg2 import pool

try:
    db_pool = psycopg2.pool.SimpleConnectionPool(
        1,  # Minimum number of connections
        20,  # Maximum number of connections
        dbname="blink",
        user="postgres",
        password="minhduc456",  # Replace with your password
        host="localhost",
        port="5432"
    )
    print("Database connection pool created successfully!")
except Exception as e:
    print(f"Error creating database connection pool: {str(e)}")
    raise

def get_db_connection():
    """Get a connection from the pool."""
    try:
        conn = db_pool.getconn()
        return conn
    except Exception as e:
        print(f"Error getting database connection: {str(e)}")
        raise

def release_db_connection(conn):
    """Release a connection back to the pool."""
    if conn:
        db_pool.putconn(conn)

def close_db_pool():
    """Close all connections in the pool."""
    if db_pool:
        db_pool.closeall()
        print("Database connection pool closed.")