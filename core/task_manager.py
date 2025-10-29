"""
Task Manager module for Sathi AI assistant.
Handles SQLite database operations for storing and managing tasks/reminders.
Provides functionality for task creation, retrieval, and scheduling.
"""

import sqlite3
import os
from datetime import datetime
import logging
from typing import List, Dict, Optional
import time
from pathlib import Path

# Configure logging
# Get the absolute path to the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = PROJECT_ROOT / 'data' / 'task_manager.log'

# Ensure log directory exists
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOG_PATH),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Database configuration
# Get the absolute path to the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / 'sathi_tasks.db'  # Store in project root for now

# Log the paths
logging.info(f"Project root: {PROJECT_ROOT}")
logging.info(f"Database path: {DB_PATH}")

# Log initial configuration
logging.info(f"Project root: {PROJECT_ROOT}")
logging.info(f"Database path: {DB_PATH}")
logging.info("Setting up database...")

def init_db() -> None:
    """
    Initialize the SQLite database and create the tasks table if it doesn't exist.
    """
    try:
        # Log database connection attempt
        logging.info(f"Attempting to connect to database: {DB_PATH}")
        
        # Create a new database connection
        conn = sqlite3.connect(str(DB_PATH), timeout=20)
        cursor = conn.cursor()
        
        # Create tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TEXT NOT NULL,
                message TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_run TIMESTAMP,
                repeat_daily BOOLEAN DEFAULT 1
            )
        ''')
        
        # Create tasks table with necessary fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TEXT NOT NULL,           -- HH:MM format
                message TEXT NOT NULL,        -- Elderly-friendly reminder message
                is_active BOOLEAN DEFAULT 1,  -- For soft deletion
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_run TIMESTAMP,          -- Last time this reminder was announced
                repeat_daily BOOLEAN DEFAULT 1  -- Whether task repeats daily
            )
        ''')
        
        conn.commit()
        logging.info("Database initialized successfully")
        
    except Exception as e:
        logging.error(f"Error initializing database: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def add_task(time_str: str, message: str, repeat_daily: bool = True) -> bool:
    """
    Add a new task to the database.
    
    Args:
        time_str: Time in HH:MM format
        message: Elderly-friendly reminder message
        repeat_daily: Whether the task repeats daily (default True)
    
    Returns:
        bool: True if task was added successfully
    """
    conn = None
    try:
        # Validate time format
        try:
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            logging.error(f"Invalid time format: {time_str}")
            return False
        
        # Ensure database file exists
        if not DB_PATH.exists():
            init_db()
            
        conn = sqlite3.connect(str(DB_PATH), timeout=20)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tasks (time, message, repeat_daily)
            VALUES (?, ?, ?)
        ''', (time_str, message, repeat_daily))
        
        conn.commit()
        logging.info(f"Added new task: {time_str} - {message}")
        return True
        
    except Exception as e:
        logging.error(f"Error adding task: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def fetch_tasks() -> List[Dict]:
    """
    Fetch all active tasks from the database.
    
    Returns:
        List of dictionaries containing task details
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row  # This enables column access by name
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, time, message, repeat_daily, last_run
            FROM tasks
            WHERE is_active = 1
            ORDER BY time
        ''')
        
        tasks = [dict(row) for row in cursor.fetchall()]
        logging.info(f"Fetched {len(tasks)} active tasks")
        return tasks
        
    except Exception as e:
        logging.error(f"Error fetching tasks: {str(e)}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

def update_last_run(task_id: int) -> None:
    """
    Update the last_run timestamp for a task after it has been announced.
    
    Args:
        task_id: ID of the task to update
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE tasks
            SET last_run = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (task_id,))
        
        conn.commit()
        logging.info(f"Updated last_run for task {task_id}")
        
    except Exception as e:
        logging.error(f"Error updating task last_run: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

def delete_task(task_id: int) -> bool:
    """
    Soft delete a task by setting is_active to False.
    
    Args:
        task_id: ID of the task to delete
    
    Returns:
        bool: True if task was deleted successfully
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE tasks
            SET is_active = 0
            WHERE id = ?
        ''', (task_id,))
        
        conn.commit()
        logging.info(f"Deleted task {task_id}")
        return True
        
    except Exception as e:
        logging.error(f"Error deleting task: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

# Initialize database when module is imported
init_db()