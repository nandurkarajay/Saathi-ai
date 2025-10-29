"""
Simple Flask web interface for family members/admins to manage tasks.
"""

from flask import Flask, request, render_template, redirect, url_for, flash
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.task_manager import add_task, fetch_tasks, delete_task

app = Flask(__name__)
app.secret_key = 'sathi_admin_secret_key'  # Required for flash messages

@app.route('/')
def index():
    """Display the task management interface and list of tasks."""
    tasks = fetch_tasks()
    return render_template('admin.html', tasks=tasks)

@app.route('/add_task', methods=['POST'])
def handle_add_task():
    """Handle the form submission for adding a new task."""
    time = request.form.get('time')
    message = request.form.get('message')
    repeat_daily = bool(request.form.get('repeat_daily'))
    
    if not time or not message:
        flash('Please provide both time and message', 'error')
        return redirect(url_for('index'))
    
    if add_task(time, message, repeat_daily):
        flash('Task added successfully!', 'success')
    else:
        flash('Error adding task. Please check the time format (HH:MM).', 'error')
    
    return redirect(url_for('index'))

@app.route('/delete_task/<int:task_id>')
def handle_delete_task(task_id):
    """Handle task deletion."""
    if delete_task(task_id):
        flash('Task deleted successfully!', 'success')
    else:
        flash('Error deleting task', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("\n💻 Starting Sathi Admin Interface...")
    print("🌐 Open your web browser and go to: http://localhost:5000")
    print("📝 You can add and manage tasks for the elderly user there\n")
    app.run(debug=True, port=5000)