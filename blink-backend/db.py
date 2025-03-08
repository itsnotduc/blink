# blink-backend/db.py
import psycopg2
from psycopg2 import pool
import uuid
from datetime import datetime, timedelta

# In-memory session store (for demo purposes; use Redis in production)
session_store = {}

# Track active connections
active_connections = 0
MAX_CONNECTIONS = 20

# Admin credentials (in production, store securely in environment variables or a secrets manager)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "securepassword123"  # Change this in production!

# Create a connection pool
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(
        1,  # Minimum number of connections
        MAX_CONNECTIONS,  # Maximum number of connections
        dbname="blink",
        user="postgres",
        password="minhduc456",
        host="localhost",
        port="5432"
    )
    print("Database connection pool created successfully!")
except Exception as e:
    print(f"Error creating database connection pool: {str(e)}")
    raise

def create_session(role="user"):
    """Create a new session and return a session token."""
    session_token = str(uuid.uuid4())
    # Session valid for 1 hour
    session_store[session_token] = {
        "role": role,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(hours=1)
    }
    return session_token

def validate_session(session_token, required_role=None):
    """Validate the session token and check if it has the required role."""
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
    """Return the role of the session."""
    if session_token in session_store:
        return session_store[session_token]["role"]
    return None

def get_db_connection(session_token, required_role=None):
    """Get a connection from the pool after validating the session."""
    global active_connections

    # Validate the session and role
    if not validate_session(session_token, required_role):
        raise Exception("Invalid or expired session token, or insufficient privileges")

    # Check if we can borrow a new connection
    if active_connections >= MAX_CONNECTIONS:
        raise Exception("No available connections in the pool")

    try:
        print(f"Borrowing connection from pool... (Active connections: {active_connections})")
        conn = db_pool.getconn()
        active_connections += 1
        print(f"Connection borrowed successfully. (Active connections: {active_connections})")
        return conn
    except Exception as e:
        print(f"Error getting database connection: {str(e)}")
        raise

def release_db_connection(conn):
    """Release a connection back to the pool."""
    global active_connections
    if conn:
        print(f"Releasing connection back to pool... (Active connections: {active_connections})")
        db_pool.putconn(conn)
        active_connections -= 1
        print(f"Connection released successfully. (Active connections: {active_connections})")

def close_db_pool():
    """Close all connections in the pool."""
    global active_connections
    if db_pool:
        db_pool.closeall()
        active_connections = 0
        print("Database connection pool closed.")

def get_active_connections():
    """Return the number of active connections."""
    return active_connections

def get_max_connections():
    """Return the maximum number of connections in the pool."""
    return MAX_CONNECTIONS

def get_all_sessions():
    """Return all active sessions (admin-only)."""
    return session_store