import os
import psycopg2
from psycopg2 import pool
from fastapi import HTTPException
from dotenv import load_dotenv
import uuid
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
session_store = {}
db_pool = None

def get_db_pool():
    global db_pool
    if db_pool is None:
        try:
            db_pool = psycopg2.pool.SimpleConnectionPool(
                1, 20,
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
                database=os.getenv("DB_NAME")
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Error creating database connection pool: {e}")
            raise
    return db_pool

def get_db_connection(session_token):
    if not validate_session(session_token):
        raise HTTPException(status_code=403, detail="Invalid session")
    pool = get_db_pool()
    conn = pool.getconn()
    if conn:
        logger.info("Borrowing connection from pool")
        return conn
    raise HTTPException(status_code=500, detail="Unable to get database connection")

def release_db_connection(conn):
    if conn:
        logger.info("Releasing connection back to pool")
        get_db_pool().putconn(conn)

def create_session(role):
    token = str(uuid.uuid4())
    session_store[token] = {"role": role}
    logger.info(f"Session created: {token} with role {role}")
    return token

def validate_session(session_token, required_role=None):
    session = session_store.get(session_token)
    if not session:
        return False
    if required_role and session["role"] != required_role:
        return False
    return True

def get_active_connections():
    return db_pool._used

def get_max_connections():
    return db_pool.maxconn

def get_all_sessions():
    return [{"token": k, "role": v["role"]} for k, v in session_store.items()]