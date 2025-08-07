# Database Connection Module for Marcus Discord Bot
# Handles PostgreSQL database operations, user data, and interaction history

import os
import logging
import asyncio
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger('marcus.database')

# Load environment variables
load_dotenv()
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

# Global connection pool
connection_pool = None

async def initialize_database():
    """
    Initialize the database connection pool and create tables if they don't exist
    
    Returns:
        bool: True if initialization was successful
    """
    global connection_pool
    
    try:
        # Create connection pool
        logger.info(f"Creating database connection pool to {DB_HOST}:{DB_PORT}/{DB_NAME}")
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            1, 10,
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        
        # Test connection and create tables
        await _create_tables()
        
        logger.info("Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

def get_database_connection():
    """
    Get a connection from the connection pool
    
    Returns:
        connection: PostgreSQL database connection
    """
    global connection_pool
    
    if not connection_pool:
        logger.error("Database connection pool not initialized")
        return None
        
    try:
        return connection_pool.getconn()
    except Exception as e:
        logger.error(f"Error getting connection from pool: {e}")
        return None

def release_connection(connection):
    """
    Release a connection back to the pool
    
    Args:
        connection: Connection to release
    """
    global connection_pool
    
    if connection and connection_pool:
        try:
            connection_pool.putconn(connection)
        except Exception as e:
            logger.error(f"Error releasing connection to pool: {e}")

async def _create_tables():
    """
    Create database tables if they don't exist
    """
    connection = None
    
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        
        # Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            interaction_count INTEGER DEFAULT 0
        )
        """)
        
        # Message history table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS message_history (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            channel_id BIGINT NOT NULL,
            message_content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """)
        
        # User rage levels table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_rage_levels (
            user_id BIGINT PRIMARY KEY,
            rage_level INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """)
        
        # Response history table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS response_history (
            id SERIAL PRIMARY KEY,
            message_id BIGINT,
            response_content TEXT,
            personality VARCHAR(50),
            mood VARCHAR(50),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        connection.commit()
        logger.info("Database tables created or already exist")
        
    except Exception as e:
        if connection:
            connection.rollback()
        logger.error(f"Error creating tables: {e}")
        
    finally:
        if connection:
            release_connection(connection)

async def record_user(user_id, username):
    """
    Record or update user information
    
    Args:
        user_id (int): Discord user ID
        username (str): Discord username
        
    Returns:
        bool: Success or failure
    """
    connection = None
    
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
        INSERT INTO users (user_id, username)
        VALUES (%s, %s)
        ON CONFLICT (user_id) 
        DO UPDATE SET 
            username = %s,
            last_seen = CURRENT_TIMESTAMP,
            interaction_count = users.interaction_count + 1
        """, (user_id, username, username))
        
        connection.commit()
        return True
        
    except Exception as e:
        if connection:
            connection.rollback()
        logger.error(f"Error recording user: {e}")
        return False
        
    finally:
        if connection:
            release_connection(connection)

async def record_message(user_id, channel_id, message_content):
    """
    Record a message in the database
    
    Args:
        user_id (int): Discord user ID
        channel_id (int): Discord channel ID
        message_content (str): Content of the message
        
    Returns:
        int: Message ID or None on failure
    """
    connection = None
    
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
        INSERT INTO message_history (user_id, channel_id, message_content)
        VALUES (%s, %s, %s)
        RETURNING id
        """, (user_id, channel_id, message_content))
        
        message_id = cursor.fetchone()[0]
        connection.commit()
        return message_id
        
    except Exception as e:
        if connection:
            connection.rollback()
        logger.error(f"Error recording message: {e}")
        return None
        
    finally:
        if connection:
            release_connection(connection)

async def update_rage_level(user_id, change):
    """
    Update a user's rage level
    
    Args:
        user_id (int): Discord user ID
        change (int): Amount to change the rage level by
        
    Returns:
        int: New rage level or None on failure
    """
    connection = None
    
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        
        # First ensure user exists in users table
        cursor.execute("""
        SELECT COUNT(*) FROM users WHERE user_id = %s
        """, (user_id,))
        
        if cursor.fetchone()[0] == 0:
            logger.warning(f"User {user_id} not found when updating rage level")
            return None
        
        # Update or insert rage level
        cursor.execute("""
        INSERT INTO user_rage_levels (user_id, rage_level, last_updated)
        VALUES (%s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (user_id) 
        DO UPDATE SET 
            rage_level = GREATEST(0, LEAST(100, user_rage_levels.rage_level + %s)),
            last_updated = CURRENT_TIMESTAMP
        RETURNING rage_level
        """, (user_id, max(0, min(100, change)), change))
        
        new_level = cursor.fetchone()[0]
        connection.commit()
        return new_level
        
    except Exception as e:
        if connection:
            connection.rollback()
        logger.error(f"Error updating rage level: {e}")
        return None
        
    finally:
        if connection:
            release_connection(connection)

async def get_rage_level(user_id):
    """
    Get a user's current rage level
    
    Args:
        user_id (int): Discord user ID
        
    Returns:
        int: Current rage level (0-100) or 0 if not found
    """
    connection = None
    
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
        SELECT rage_level FROM user_rage_levels WHERE user_id = %s
        """, (user_id,))
        
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return 0
            
    except Exception as e:
        logger.error(f"Error getting rage level: {e}")
        return 0
        
    finally:
        if connection:
            release_connection(connection)

async def record_response(message_id, response_content, personality, mood):
    """
    Record a bot response
    
    Args:
        message_id (int): ID of the message being responded to
        response_content (str): Content of the response
        personality (str): Active personality that generated the response
        mood (str): Current mood when response was generated
        
    Returns:
        bool: Success or failure
    """
    connection = None
    
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
        INSERT INTO response_history (message_id, response_content, personality, mood)
        VALUES (%s, %s, %s, %s)
        """, (message_id, response_content, personality, mood))
        
        connection.commit()
        return True
        
    except Exception as e:
        if connection:
            connection.rollback()
        logger.error(f"Error recording response: {e}")
        return False
        
    finally:
        if connection:
            release_connection(connection)
