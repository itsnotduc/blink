import psycopg2
from psycopg2 import pool
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Database configuration from .env
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# Admin credentials from .env
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# In-memory session store (use Redis in production)
session_store = {}

# Track active connections
active_connections = 0
MAX_CONNECTIONS = 20

# Create a connection pool
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(
        1,  # Minimum connections
        MAX_CONNECTIONS,  # Maximum connections
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    print("Database connection pool created successfully!")
except Exception as e:
    print(f"Error creating database connection pool: {str(e)}")
    raise

# Rest of the code remains unchanged...
def create_session(role="user"):
    session_token = str(uuid.uuid4())
    session_store[session_token] = {
        "role": role,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(hours=1)
    }
    return session_token

def validate_session(session_token, required_role=None):
    if session_token not in session_store:
        return False
    session = session_store[session_token]
    if datetime.now() > session["expires_at"]:
        del session_store[session_token]
        return False
    if required_role and session["role"] != required_role:
        return False
    return True

def get_session_role(session_token):
    if session_token in session_store:
        return session_store[session_token]["role"]
    return None

def get_db_connection(session_token, required_role=None):
    global active_connections
    if not validate_session(session_token, required_role):
        raise Exception("Invalid or expired session token, or insufficient privileges")
    if active_connections >= MAX_CONNECTIONS:
        raise Exception("No available connections in the pool")
    try:
        print(f"Borrowing connection from pool... (Active: {active_connections})")
        conn = db_pool.getconn()
        active_connections += 1
        print(f"Connection borrowed successfully. (Active: {active_connections})")
        return conn
    except Exception as e:
        print(f"Error getting database connection: {str(e)}")
        raise

def release_db_connection(conn):
    global active_connections
    if conn:
        print(f"Releasing connection back to pool... (Active: {active_connections})")
        db_pool.putconn(conn)
        active_connections -= 1
        print(f"Connection released successfully. (Active: {active_connections})")

def close_db_pool():
    global active_connections
    if db_pool:
        db_pool.closeall()
        active_connections = 0
        print("Database connection pool closed.")

def get_active_connections():
    return active_connections

def get_max_connections():
    return MAX_CONNECTIONS

def get_all_sessions():
    return session_store