"""
Chat Context Manager for Sathi AI
Stores all conversation history in a single text file
Provides context to LLM for continuity
"""

from datetime import datetime
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTEXT_FILE = PROJECT_ROOT / 'data' / 'chat_context.txt'

# Ensure directory exists
CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)


def save_conversation(user_input: str, sathi_response: str):
    """
    Save a conversation exchange to the context file
    
    Args:
        user_input: What the user said
        sathi_response: Sathi's response
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(CONTEXT_FILE, 'a', encoding='utf-8') as f:
            f.write(f"\n[{timestamp}]\n")
            f.write(f"User: {user_input}\n")
            f.write(f"Sathi: {sathi_response}\n")
        
        print(f"💾 Context saved")
        
    except Exception as e:
        print(f"⚠️ Failed to save context: {e}")


def log_event(event: str):
    """
    Log system events (wake word, reminders, etc.)
    
    Args:
        event: Event description
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(CONTEXT_FILE, 'a', encoding='utf-8') as f:
            f.write(f"\n[{timestamp}] SYSTEM: {event}\n")
        
    except Exception as e:
        print(f"⚠️ Failed to log event: {e}")


def start_session():
    """Mark the start of a new session"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with open(CONTEXT_FILE, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*70}\n")
            f.write(f"NEW SESSION: {session_id}\n")
            f.write(f"Started: {timestamp}\n")
            f.write(f"{'='*70}\n")
        
        print(f"📝 Session started: {session_id}")
        return session_id
        
    except Exception as e:
        print(f"⚠️ Failed to start session: {e}")
        return None


def get_recent_context(num_exchanges=5):
    """
    Get recent conversation history for LLM context
    
    Args:
        num_exchanges: Number of recent exchanges to retrieve
    
    Returns:
        String with formatted conversation history
    """
    try:
        if not CONTEXT_FILE.exists():
            return ""
        
        with open(CONTEXT_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Extract user-sathi exchanges
        exchanges = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith('User:'):
                user_msg = line[5:].strip()
                
                # Look for Sathi response
                if i + 1 < len(lines) and lines[i + 1].strip().startswith('Sathi:'):
                    sathi_msg = lines[i + 1].strip()[6:].strip()
                    exchanges.append((user_msg, sathi_msg))
            
            i += 1
        
        # Get most recent exchanges
        recent = exchanges[-num_exchanges:] if exchanges else []
        
        # Format for LLM
        if not recent:
            return ""
        
        context = "Previous conversation:\n"
        for user_msg, sathi_msg in recent:
            context += f"User: {user_msg}\n"
            context += f"Sathi: {sathi_msg}\n"
        
        return context
        
    except Exception as e:
        print(f"⚠️ Failed to get context: {e}")
        return ""


def get_full_context():
    """
    Get all conversation history
    
    Returns:
        String with all conversation history
    """
    try:
        if not CONTEXT_FILE.exists():
            return ""
        
        with open(CONTEXT_FILE, 'r', encoding='utf-8') as f:
            return f.read()
        
    except Exception as e:
        print(f"⚠️ Failed to get full context: {e}")
        return ""


def clear_old_context(keep_last_n=50):
    """
    Keep only the last N exchanges to prevent file from growing too large
    
    Args:
        keep_last_n: Number of exchanges to keep
    """
    try:
        if not CONTEXT_FILE.exists():
            return
        
        with open(CONTEXT_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Extract exchanges
        exchanges = []
        current_exchange = []
        
        for line in lines:
            if line.startswith('[') and '] SYSTEM:' not in line and 'NEW SESSION:' not in line:
                if current_exchange:
                    exchanges.append(''.join(current_exchange))
                current_exchange = [line]
            elif line.startswith('User:') or line.startswith('Sathi:'):
                current_exchange.append(line)
            elif current_exchange:
                current_exchange.append(line)
        
        if current_exchange:
            exchanges.append(''.join(current_exchange))
        
        # Keep only last N
        kept_exchanges = exchanges[-keep_last_n:]
        
        # Write back
        with open(CONTEXT_FILE, 'w', encoding='utf-8') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{'='*70}\n")
            f.write(f"Context trimmed: {timestamp}\n")
            f.write(f"Keeping last {keep_last_n} exchanges\n")
            f.write(f"{'='*70}\n\n")
            f.writelines(kept_exchanges)
        
        print(f"🗑️ Context trimmed (kept {len(kept_exchanges)} exchanges)")
        
    except Exception as e:
        print(f"⚠️ Failed to clear context: {e}")


def get_stats():
    """
    Get statistics about chat context
    
    Returns:
        Dictionary with stats
    """
    try:
        if not CONTEXT_FILE.exists():
            return {"exchanges": 0, "sessions": 0, "size_kb": 0}
        
        with open(CONTEXT_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        user_count = content.count('User:')
        sathi_count = content.count('Sathi:')
        sessions = content.count('NEW SESSION:')
        size = len(content)
        
        return {
            "exchanges": min(user_count, sathi_count),
            "sessions": sessions,
            "size_bytes": size,
            "size_kb": round(size / 1024, 2)
        }
        
    except Exception as e:
        print(f"⚠️ Failed to get stats: {e}")
        return {"exchanges": 0, "sessions": 0, "size_kb": 0}


# Test function
if __name__ == "__main__":
    print("="*70)
    print("CHAT CONTEXT MANAGER TEST")
    print("="*70)
    
    # Start session
    start_session()
    
    # Save conversations
    save_conversation("Hello Sathi", "Hello! How can I help you today?")
    save_conversation("What time is it?", "It's 8:10 PM")
    save_conversation("Remind me to take medicine at 9 PM", 
                     "Okay, I'll remind you to take medicine at 9:00 PM")
    
    # Log event
    log_event("Reminder set: take medicine at 21:00")
    
    # Get recent context
    print("\n📜 Recent context (last 3):")
    context = get_recent_context(num_exchanges=3)
    print(context)
    
    # Get stats
    print("\n📊 Statistics:")
    stats = get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print(f"\n✅ Context file: {CONTEXT_FILE}")
    print("="*70)
