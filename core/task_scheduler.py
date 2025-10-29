"""
Task scheduler for Sathi AI assistant.
Manages the timing and execution of tasks/reminders.
"""

import schedule
import time
from datetime import datetime
import logging
from typing import Dict, List
import threading

from core.task_manager import fetch_tasks, update_last_run
from core.tts_output import speak_text

# Configure logging
logging.basicConfig(
    filename='data/scheduler.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def announce_task(task: Dict) -> None:
    """
    Announce a task using text-to-speech.
    Speaks the message in a clear, elderly-friendly way.
    
    Args:
        task: Dictionary containing task details
    """
    try:
        # Prepare a gentle introduction for the reminder
        intro = "Excuse me, I have a reminder for you. "
        message = intro + task['message']
        
        # Speak the message
        speak_text(message, use_male_voice=True)
        
        # Update last run time
        update_last_run(task['id'])
        
        logging.info(f"Announced task {task['id']}: {task['message']}")
        
    except Exception as e:
        logging.error(f"Error announcing task: {str(e)}")

def check_tasks() -> None:
    """
    Check current time against scheduled tasks and announce any that match.
    """
    try:
        current_time = datetime.now().strftime("%H:%M")
        tasks = fetch_tasks()
        
        for task in tasks:
            if task['time'] == current_time:
                # Check if task should run (for non-daily tasks)
                if task['repeat_daily'] or not task.get('last_run'):
                    announce_task(task)
        
    except Exception as e:
        logging.error(f"Error checking tasks: {str(e)}")

def start_scheduler() -> None:
    """
    Start the task scheduler in a separate thread.
    Checks tasks every minute.
    """
    def run_scheduler():
        # Schedule the task checker to run every minute
        schedule.every().minute.at(":00").do(check_tasks)
        
        # Run the scheduler loop
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    # Start scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logging.info("Task scheduler started")