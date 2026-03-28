"""
API Quota Manager for Sathi AI
Handles quota limits and provides graceful fallbacks
"""

import time
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUOTA_FILE = PROJECT_ROOT / 'data' / 'api_quota.json'

# Ensure directory exists
QUOTA_FILE.parent.mkdir(parents=True, exist_ok=True)


class QuotaManager:
    """Manages API quota and provides fallback responses"""
    
    def __init__(self, daily_limit=20):
        self.daily_limit = daily_limit
        self.quota_data = self.load_quota_data()
        
    def load_quota_data(self):
        """Load quota tracking data"""
        if QUOTA_FILE.exists():
            try:
                with open(QUOTA_FILE, 'r') as f:
                    data = json.load(f)
                    # Ensure all required fields exist
                    return {
                        "date": data.get("date", datetime.now().strftime("%Y-%m-%d")),
                        "requests_made": data.get("requests_made", 0),
                        "last_request_time": data.get("last_request_time", None),
                        "quota_exceeded": data.get("quota_exceeded", False),
                        "daily_limit": data.get("daily_limit", self.daily_limit),
                        "total_requests_ever": data.get("total_requests_ever", 0),
                        "first_use_date": data.get("first_use_date", datetime.now().strftime("%Y-%m-%d")),
                        "api_errors": data.get("api_errors", 0),
                        "local_llm_fallbacks": data.get("local_llm_fallbacks", 0)
                    }
            except:
                pass
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "requests_made": 0,
            "last_request_time": None,
            "quota_exceeded": False,
            "daily_limit": self.daily_limit,
            "total_requests_ever": 0,
            "first_use_date": datetime.now().strftime("%Y-%m-%d"),
            "api_errors": 0,
            "local_llm_fallbacks": 0
        }
    
    def save_quota_data(self):
        """Save quota tracking data"""
        try:
            with open(QUOTA_FILE, 'w') as f:
                json.dump(self.quota_data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save quota data: {e}")
    
    def check_quota(self):
        """Check if we have quota available"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Reset if new day
        if self.quota_data["date"] != today:
            self.quota_data["date"] = today
            self.quota_data["requests_made"] = 0
            self.quota_data["quota_exceeded"] = False
            self.quota_data["last_request_time"] = None
            self.save_quota_data()
        
        # Use daily_limit from JSON data (allows dynamic limits)
        daily_limit = self.quota_data.get("daily_limit", self.daily_limit)
        
        # Check if we've exceeded quota - update flag based on actual usage
        if self.quota_data["requests_made"] >= daily_limit:
            self.quota_data["quota_exceeded"] = True
            return False
        else:
            # Clear flag if we have quota available
            if self.quota_data["quota_exceeded"]:
                self.quota_data["quota_exceeded"] = False
                self.save_quota_data()
        
        return True
    
    def record_request(self):
        """Record an API request"""
        self.quota_data["requests_made"] += 1
        self.quota_data["total_requests_ever"] += 1
        self.quota_data["last_request_time"] = datetime.now().isoformat()
        self.save_quota_data()
    
    def record_api_error(self):
        """Record an API error"""
        self.quota_data["api_errors"] += 1
        self.save_quota_data()
    
    def record_local_fallback(self):
        """Record a local LLM fallback"""
        self.quota_data["local_llm_fallbacks"] += 1
        self.save_quota_data()
    
    def get_quota_status(self):
        """Get current quota status"""
        today = datetime.now().strftime("%Y-%m-%d")
        daily_limit = self.quota_data.get("daily_limit", self.daily_limit)
        
        if self.quota_data["date"] != today:
            return f"📊 Quota: 0/{daily_limit} (reset today)"
        
        remaining = max(0, daily_limit - self.quota_data["requests_made"])
        status = "🔴 Quota Exceeded" if remaining == 0 else "🟢 Available"
        
        return f"📊 Quota: {self.quota_data['requests_made']}/{daily_limit} ({remaining} remaining) - {status}"
    
    def get_fallback_response(self, user_input):
        """Get response when quota is exceeded - tries local LLM first, then falls back to static responses"""
        from .elderly_personality import personality_engine
        
        # Record that we're using fallback
        self.record_local_fallback()
        
        # Try local LLM first
        try:
            from .llm_local import query_local_llm, get_model_status
            
            print(f"Local LLM status: {get_model_status()}")
            local_response = query_local_llm(user_input)
            
            if local_response:
                print("✅ Using local LLM response")
                return local_response
            else:
                print("⚠️ Local LLM failed, using static fallback")
                
        except ImportError:
            print("⚠️ Local LLM module not available, using static fallback")
        except Exception as e:
            print(f"⚠️ Local LLM error: {e}, using static fallback")
        
        # Static fallback responses (original code)
        emotions = personality_engine.detect_emotion(user_input)
        user_lower = user_input.lower()
        
        if any(word in user_lower for word in ["time", "what time", "current time"]):
            try:
                from datetime import datetime
                now = datetime.now()
                time_str = now.strftime("%I:%M %p")
                if time_str.startswith('0'):
                    time_str = time_str[1:]
                return f"The current time is {time_str}. I'm sorry I couldn't provide a more detailed response due to service limits."
            except:
                return "I'm having trouble with the AI service right now, but I can tell you it's daytime. Please try again later for the exact time."
        
        if any(word in user_lower for word in ["date", "what date", "today's date"]):
            try:
                from datetime import datetime
                now = datetime.now()
                date_str = now.strftime("%B %d, %Y")
                return f"Today is {date_str}. I'm sorry I couldn't provide more details due to service limits."
            except:
                return "I'm having trouble with the AI service right now. Please try again later for the date."
        
        # Emotional support responses
        if emotions.get("sad", 0) > 0.3 or "lonely" in user_lower:
            return "I understand you're feeling down. I'm here with you, though I'm having some technical difficulties right now. Your feelings matter, and I'm listening. Please try again in a little while."
        
        if emotions.get("anxious", 0) > 0.3 or "worried" in user_lower:
            return "I hear that you're worried. It's okay to feel that way. I'm having some connection issues at the moment, but I want you to know you're safe. We can talk more when the service is available."
        
        if emotions.get("confused", 0) > 0.3 or "confused" in user_lower:
            return "I understand you're feeling confused. I'm sorry I'm having trouble connecting right now, but I want to help. Please try again in a little while, and we'll work through this together."
        
        # Default caring response
        return "I'm sorry, I'm having trouble connecting to the AI service right now due to usage limits. Please try again in a little while. I'm here to help you when the service is available."
    
    def handle_quota_exceeded(self, full_prompt_or_user_input):
        """Handle quota exceeded situation - receives full prompt with system instructions"""
        self.quota_data["quota_exceeded"] = True
        self.save_quota_data()
        
        # Check if this is a full prompt (contains system instructions) or just user input
        if "You are Sathi" in full_prompt_or_user_input:
            # This is a full prompt with system instructions
            print("🔴 Using offline LLM with full system prompt")
            return self.get_fallback_response_with_prompt(full_prompt_or_user_input)
        else:
            # This is just user input - use original fallback
            print("🔴 Using offline LLM with user input only")
            return self.get_fallback_response(full_prompt_or_user_input)
    
    def get_fallback_response_with_prompt(self, full_prompt):
        """Get response using local LLM with full system prompt"""
        from .elderly_personality import personality_engine
        
        # Record that we're using fallback
        self.record_local_fallback()
        
        # Try local LLM with full system prompt
        try:
            from .llm_local import query_local_llm, get_model_status
            
            print(f"Local LLM status: {get_model_status()}")
            local_response = query_local_llm(full_prompt)  # Pass full prompt with system instructions
            
            if local_response:
                print("✅ Using local LLM response with system prompt")
                return local_response
            else:
                print("⚠️ Local LLM failed, using static fallback")
                
        except ImportError:
            print("⚠️ Local LLM module not available, using static fallback")
        except Exception as e:
            print(f"⚠️ Local LLM error: {e}, using static fallback")
        
        # Extract user input from full prompt for static fallback
        user_input = full_prompt.split("User: ")[-1] if "User: " in full_prompt else full_prompt
        return self.get_fallback_response(user_input)


# Global quota manager
quota_manager = QuotaManager(daily_limit=20)


def can_make_api_request():
    """Check if we can make an API request"""
    return quota_manager.check_quota()


def record_api_request():
    """Record that we made an API request"""
    quota_manager.record_request()


def handle_quota_error(full_prompt_or_user_input):
    """Handle quota exceeded error - receives full prompt with system instructions"""
    return quota_manager.handle_quota_exceeded(full_prompt_or_user_input)


def get_quota_info():
    """Get quota information"""
    return quota_manager.get_quota_status()


def get_quota_details():
    """Get detailed quota information"""
    daily_limit = quota_manager.quota_data.get("daily_limit", quota_manager.daily_limit)
    return {
        "daily_limit": daily_limit,
        "requests_made": quota_manager.quota_data["requests_made"],
        "remaining": max(0, daily_limit - quota_manager.quota_data["requests_made"]),
        "date": quota_manager.quota_data["date"],
        "quota_exceeded": quota_manager.quota_data["quota_exceeded"],
        "last_request_time": quota_manager.quota_data["last_request_time"],
        "total_requests_ever": quota_manager.quota_data.get("total_requests_ever", 0),
        "first_use_date": quota_manager.quota_data.get("first_use_date", datetime.now().strftime("%Y-%m-%d")),
        "api_errors": quota_manager.quota_data.get("api_errors", 0),
        "local_llm_fallbacks": quota_manager.quota_data.get("local_llm_fallbacks", 0)
    }


def print_quota_status():
    """Print detailed quota status for user"""
    details = get_quota_details()
    print("📊 GEMINI API QUOTA STATUS")
    print(f"📅 Date: {details['date']}")
    print(f"📈 Requests Made: {details['requests_made']}")
    print(f"📉 Daily Limit: {details['daily_limit']}")
    print(f"🆓 Remaining: {details['remaining']}")
    print(f"🚦 Status: {'🔴 Quota Exceeded' if details['quota_exceeded'] else '🟢 Available'}")
    print(f"📊 Total Requests Ever: {details['total_requests_ever']}")
    print(f"🎯 First Use Date: {details['first_use_date']}")
    print(f"❌ API Errors: {details['api_errors']}")
    print(f"🤖 Local LLM Fallbacks: {details['local_llm_fallbacks']}")
    if details['last_request_time']:
        print(f"⏰ Last Request: {details['last_request_time']}")


if __name__ == "__main__":
    # Test quota manager
    print("="*50)
    print("📊 API QUOTA MANAGER TEST")
    print("="*50)
    
    print(get_quota_info())
    print(f"Can make request: {can_make_api_request()}")
    
    # Test fallback response
    test_inputs = [
        "What time is it?",
        "I'm feeling lonely",
        "I'm confused about this",
        "Tell me about the weather"
    ]
    
    for test_input in test_inputs:
        print(f"\nUser: {test_input}")
        fallback = handle_quota_error(test_input)
        print(f"Sathi: {fallback}")
    
    print("\n" + "="*50)
