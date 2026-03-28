"""
Task System for Sathi AI Assistant

Combined task management and scheduling functionality.
Handles storage, retrieval, and timed execution of tasks and reminders.
"""

import sqlite3
import time
import logging
import schedule
import threading
from datetime import datetime
from typing import List, Dict, Any, Union
from pathlib import Path

# Import from other core modules
from core.tts_output import speak_text
from core.reminder_system import ring_for_reminder, ReminderManager

# Configure logging
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = PROJECT_ROOT / 'data' / 'task_system.log'

# Ensure log directory exists
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOG_PATH),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'  # Append mode to avoid overwriting logs
)

# Database configuration
DB_PATH = PROJECT_ROOT / 'sathi.db'  # Main Sathi AI database

# Log initial configuration
logging.info(f"Task System initialized. Project root: {PROJECT_ROOT}")
logging.info(f"Database path: {DB_PATH}")

class TaskManager:
    """Handles database operations for task management"""
    
    def __init__(self, db_path: Union[str, Path] = None):
        """Initialize TaskManager with database path"""
        self.db_path = str(db_path) if db_path else str(DB_PATH)
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a database connection"""
        return sqlite3.connect(self.db_path, timeout=20)
    
    def _init_db(self) -> None:
        """Initialize the database tables if they don't exist"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Create tasks table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        time TEXT NOT NULL,              -- Time in HH:MM format (24-hour)
                        message TEXT NOT NULL,          -- Task description
                        is_active BOOLEAN DEFAULT 1,    -- Active status
                        repeat_daily BOOLEAN DEFAULT 1, -- Whether task repeats daily
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_run TIMESTAMP,             -- Last time task was triggered
                        ring_enabled BOOLEAN DEFAULT 1  -- Whether to play ring sound
                    )
                ''')
                
                conn.commit()
                logging.info("Database tables initialized")
                
        except Exception as e:
            logging.error(f"Error initializing database: {str(e)}")
            raise
    
    def add_task(self, time_str: str, message: str, repeat_daily: bool = True, 
                ring_enabled: bool = True, custom_ringtone: str = None) -> bool:
        """
        Add a new task to the database.
        
        Args:
            time_str: Time in HH:MM format (24-hour)
            message: Task description
            repeat_daily: Whether the task repeats daily
            ring_enabled: Whether to play sound for this task
            custom_ringtone: Path to custom ringtone file
            
        Returns:
            bool: True if task was added successfully
        """
        try:
            # Validate time format
            datetime.strptime(time_str, "%H:%M")
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO tasks (time, message, repeat_daily, ring_enabled, custom_ringtone)
                    VALUES (?, ?, ?, ?, ?)
                ''', (time_str, message, repeat_daily, ring_enabled, custom_ringtone))
                
                conn.commit()
                logging.info(f"Added new task: {time_str} - {message}")
                return True
                
        except ValueError as e:
            logging.error(f"Invalid time format: {time_str}")
            return False
        except Exception as e:
            logging.error(f"Error adding task: {str(e)}")
            return False
    
    def get_tasks(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Retrieve tasks from the database.
        
        Args:
            active_only: If True, return only active tasks
            
        Returns:
            List of task dictionaries
        """
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = 'SELECT * FROM tasks'
                params = ()
                
                if active_only:
                    query += ' WHERE is_active = 1'
                
                query += ' ORDER BY time'
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logging.error(f"Error fetching tasks: {str(e)}")
            return []
    
    def update_task_last_run(self, task_id: int) -> bool:
        """
        Update the last run timestamp for a task.
        
        Args:
            task_id: ID of the task to update
            
        Returns:
            bool: True if update was successful
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE tasks 
                    SET last_run = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (task_id,))
                
                conn.commit()
                logging.debug(f"Updated last_run for task {task_id}")
                return True
                
        except Exception as e:
            logging.error(f"Error updating task last_run: {str(e)}")
            return False
    
    def delete_task(self, task_id: int, soft_delete: bool = True) -> bool:
        """
        Delete a task from the database.
        
        Args:
            task_id: ID of the task to delete
            soft_delete: If True, mark as inactive instead of deleting
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if soft_delete:
                    cursor.execute('''
                        UPDATE tasks 
                        SET is_active = 0 
                        WHERE id = ?
                    ''', (task_id,))
                else:
                    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
                
                conn.commit()
                logging.info(f"Deleted task {task_id} (soft_delete={soft_delete})")
                return True
                
        except Exception as e:
            logging.error(f"Error deleting task {task_id}: {str(e)}")
            return False


class TaskScheduler:
    """Manages scheduling and execution of tasks"""
    
    def __init__(self, task_manager: TaskManager = None):
        """Initialize the task scheduler"""
        self.task_manager = task_manager or TaskManager()
        self.reminder_manager = ReminderManager()
        self._stop_event = threading.Event()
        self._scheduler_thread = None
        
        # Check if reminder system is available
        self.reminder_system_available = hasattr(self.reminder_manager, 'fetch_reminders')
        
        logging.info("TaskScheduler initialized")
    
    def _play_custom_ringtone(self, ringtone_path: str) -> bool:
        """Play custom ringtone from file path"""
        try:
            import os
            from pathlib import Path
            
            ringtone_file = Path(ringtone_path)
            if not ringtone_file.exists():
                logging.warning(f"Custom ringtone not found: {ringtone_path}")
                return False
            
            # Try to play custom ringtone
            try:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(str(ringtone_file))
                pygame.mixer.music.play()
                logging.info(f"Playing custom ringtone: {ringtone_path}")
                return True
            except ImportError:
                # Fallback to winsound if pygame not available
                try:
                    import winsound
                    if ringtone_path.endswith('.wav'):
                        winsound.PlaySound(str(ringtone_file), winsound.SND_FILENAME)
                        logging.info(f"Playing custom WAV ringtone: {ringtone_path}")
                        return True
                    else:
                        logging.warning(f"Unsupported ringtone format: {ringtone_path}")
                        return False
                except Exception as e:
                    logging.error(f"Error playing custom ringtone: {e}")
                    return False
                    
        except Exception as e:
            logging.error(f"Error with custom ringtone: {e}")
            return False
    
    def _announce_task(self, task: Dict[str, Any]) -> None:
        """
        Announce a task using TTS with 15-second ring and stop on "thank you".
        
        Args:
            task: Task dictionary containing task details
        """
        try:
            # Play ring sound if enabled
            if task.get('ring_enabled', True):
                # Start 15-second ringing with stop capability
                self._play_ring_with_stop(task)
            
            # Update last run time
            self.task_manager.update_task_last_run(task['id'])
            
            logging.info(f"Task {task['id']} announced successfully")
            
        except Exception as e:
            logging.error(f"Error announcing task {task.get('id', 'unknown')}: {str(e)}")
    
    def _play_ring_with_stop(self, task: Dict[str, Any]) -> None:
        """Play ring sound for 15 seconds or until "thank you" is detected"""
        import threading
        from core.voice_input import record_audio, transcribe_audio
        
        ring_stopped = threading.Event()
        start_time = time.time()  # Define start_time here
        
        # Check if custom ringtone is specified in task
        custom_ringtone = task.get('custom_ringtone', None)
        
        def ring_loop():
            """Ring sound loop"""
            while not ring_stopped.is_set() and (time.time() - start_time) < 15:
                if custom_ringtone:
                    self._play_custom_ringtone(custom_ringtone)
                else:
                    ring_for_reminder(gentle=True)
                time.sleep(2)  # Ring every 2 seconds
        
        def listen_for_stop():
            """Listen for stop commands: 'thank you', 'stop ringing', etc."""
            time.sleep(1)  # Give ring a chance to start
            
            while not ring_stopped.is_set() and (time.time() - start_time) < 15:
                try:
                    # Quick audio recording to listen for stop command
                    audio_path = record_audio(duration=3, filename=None)
                    if audio_path:
                        transcription = transcribe_audio(audio_path, is_wake_word=False, delete_after=True)
                        if transcription:
                            trans_text = transcription.lower()
                            # Multiple stop phrases
                            stop_phrases = ['thank you', 'stop ringing', 'stop', 'stop it', 'quiet', 'silence', 'that\'s enough', 'ok stop', 'turn off']
                            
                            if any(phrase in trans_text for phrase in stop_phrases):
                                ring_stopped.set()
                                logging.info(f"Alarm stopped by command: '{transcription}'")
                                break
                except Exception as e:
                    logging.error(f"Error listening for stop command: {e}")
                time.sleep(1)
        
        # Start both threads
        ring_thread = threading.Thread(target=ring_loop, daemon=True)
        listen_thread = threading.Thread(target=listen_for_stop, daemon=True)
        
        ring_thread.start()
        listen_thread.start()
        
        # Wait for ringing to complete or be stopped
        ring_thread.join(timeout=16)
        listen_thread.join(timeout=16)
        
        if ring_stopped.is_set():
            # Speak confirmation when stopped by user
            speak_text("You're welcome!")
            logging.info("Alarm acknowledged and stopped by user")
        else:
            # Speak the reminder message after ringing completes
            intro = "Excuse me, I have a reminder for you. "
            # Handle both old 'message' and new 'task' column names
            task_message = task.get('message') or task.get('task', 'Reminder')
            message = intro + task_message
            logging.info(f"Announcing: {message}")
            speak_text(message)
    
    def _check_and_execute_tasks(self) -> None:
        """Check for tasks due now and execute them"""
        try:
            current_time = datetime.now().strftime("%H:%M")
            
            # Process regular tasks
            tasks = self.task_manager.get_tasks(active_only=True)
            for task in tasks:
                if task['time'] == current_time:
                    # Check if task should run (for non-daily tasks)
                    if task.get('repeat_daily', True) or not task.get('last_run'):
                        self._announce_task(task)
            
            # Process reminders if available
            if self.reminder_system_available:
                try:
                    reminders = self.reminder_manager.fetch_reminders()
                    for reminder in reminders:
                        if reminder.get('time') == current_time:
                            # Check if reminder should run
                            if reminder.get('repeat_daily', True) or not reminder.get('last_run'):
                                self._announce_task(reminder)
                except Exception as e:
                    logging.error(f"Error processing reminders: {str(e)}")
                    
        except Exception as e:
            logging.error(f"Error in task scheduler: {str(e)}")
    
    def _scheduler_loop(self) -> None:
        """Main scheduler loop to check for tasks"""
        # Schedule the task checker to run every minute at :00
        schedule.every().minute.at(":00").do(self._check_and_execute_tasks)
        
        logging.info("Task scheduler loop started")
        
        # Run the scheduler loop
        while not self._stop_event.is_set():
            schedule.run_pending()
            time.sleep(1)
    
    def start(self) -> None:
        """Start the task scheduler in a background thread"""
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            logging.warning("Scheduler is already running")
            return
        
        self._stop_event.clear()
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True,
            name="TaskScheduler"
        )
        self._scheduler_thread.start()
        logging.info("Task scheduler started")
    
    def stop(self) -> None:
        """Stop the task scheduler"""
        self._stop_event.set()
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        logging.info("Task scheduler stopped")


# Global instance for convenience
task_scheduler = TaskScheduler()

def start_scheduler() -> None:
    """Start the global task scheduler"""
    task_scheduler.start()

def stop_scheduler() -> None:
    """Stop the global task scheduler"""
    task_scheduler.stop()

def add_task(time_str: str, message: str, **kwargs) -> bool:
    """
    Add a new task (convenience function)
    
    Args:
        time_str: Time in HH:MM format (24-hour)
        message: Task description
        **kwargs: Additional arguments for TaskManager.add_task()
        
    Returns:
        bool: True if task was added successfully
    """
    manager = TaskManager()
    return manager.add_task(time_str, message, **kwargs)

def get_tasks(active_only: bool = True) -> List[Dict[str, Any]]:
    """
    Get tasks (convenience function)
    
    Args:
        active_only: If True, return only active tasks
        
    Returns:
        List of task dictionaries
    """
    manager = TaskManager()
    return manager.get_tasks(active_only=active_only)

# Initialize the database when module is imported
TaskManager()
