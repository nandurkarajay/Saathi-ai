"""
Professional UI Styles for Sathi AI
Clean, elegant command-line interface without excessive symbols
"""

class Colors:
    """ANSI color codes for professional terminal output"""
    HEADER = '\033[95m'      # Bright magenta
    BLUE = '\033[94m'        # Bright blue
    CYAN = '\033[96m'        # Bright cyan
    GREEN = '\033[92m'       # Bright green
    YELLOW = '\033[93m'      # Bright yellow
    RED = '\033[91m'         # Bright red
    ENDC = '\033[0m'         # End color
    BOLD = '\033[1m'         # Bold text
    DIM = '\033[2m'          # Dim text

class UI:
    """Professional UI styling methods"""
    
    @staticmethod
    def header(text):
        """Elegant header with subtle styling"""
        width = len(text) + 8
        border = "─" * width
        print(f"\n{Colors.DIM}{border}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}  {text}  {Colors.ENDC}")
        print(f"{Colors.DIM}{border}{Colors.ENDC}\n")
    
    @staticmethod
    def section(title):
        """Clean section separator"""
        print(f"\n{Colors.CYAN}─── {title} ───{Colors.ENDC}\n")
    
    @staticmethod
    def status(message, status_type="info"):
        """Status message with appropriate color"""
        colors = {
            "info": Colors.BLUE,
            "success": Colors.GREEN,
            "warning": Colors.YELLOW,
            "error": Colors.RED
        }
        color = colors.get(status_type, Colors.BLUE)
        print(f"{color}• {message}{Colors.ENDC}")
    
    @staticmethod
    def conversation_header():
        """Clean conversation mode header"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}Conversation Mode Active{Colors.ENDC}")
        print(f"{Colors.DIM}You can now talk freely without saying 'Hey Sathi'{Colors.ENDC}")
        print(f"{Colors.DIM}Say 'goodbye', 'exit', or 'stop' to end conversation{Colors.ENDC}\n")
    
    @staticmethod
    def listening():
        """Clean listening indicator"""
        print(f"{Colors.BLUE}Listening...{Colors.ENDC}")
    
    @staticmethod
    def user_message(text):
        """User message display"""
        print(f"{Colors.GREEN}You: {text}{Colors.ENDC}")
    
    @staticmethod
    def sathi_message(text):
        """Sathi response display"""
        print(f"{Colors.CYAN}Sathi: {text}{Colors.ENDC}")
    
    @staticmethod
    def wake_word_detected():
        """Clean wake word detection"""
        print(f"{Colors.GREEN}Wake word detected{Colors.ENDC}")
    
    @staticmethod
    def sleep_mode_header():
        """Clean sleep mode header"""
        print(f"\n{Colors.YELLOW}Sleep Mode Activated{Colors.ENDC}")
        print(f"{Colors.DIM}I'm listening but won't respond{Colors.ENDC}")
        print(f"{Colors.DIM}Say 'Hey Sathi' to wake me up{Colors.ENDC}\n")
    
    @staticmethod
    def sleep_listening():
        """Sleep mode listening indicator"""
        print(f"{Colors.DIM}Sleep mode... (listening for wake word){Colors.ENDC}")
    
    @staticmethod
    def emergency_alert():
        """Emergency alert display"""
        print(f"{Colors.RED}Emergency email sent to family members{Colors.ENDC}")
    
    @staticmethod
    def error(message):
        """Error message display"""
        print(f"{Colors.RED}Error: {message}{Colors.ENDC}")
    
    @staticmethod
    def info(message):
        """Info message display"""
        print(f"{Colors.BLUE}Info: {message}{Colors.ENDC}")
    
    @staticmethod
    def success(message):
        """Success message display"""
        print(f"{Colors.GREEN}Success: {message}{Colors.ENDC}")
    
    @staticmethod
    def warning(message):
        """Warning message display"""
        print(f"{Colors.YELLOW}Warning: {message}{Colors.ENDC}")
    
    @staticmethod
    def divider():
        """Simple divider"""
        print(f"\n{Colors.DIM}{'─' * 40}{Colors.ENDC}\n")
    
    @staticmethod
    def turn_indicator(turn_number):
        """Clean turn indicator"""
        print(f"\n{Colors.DIM}Turn {turn_number}{Colors.ENDC}")
    
    @staticmethod
    def welcome_message():
        """Professional welcome message"""
        UI.header("Sathi AI - Elderly Care Companion")
        UI.status("System ready and listening for your voice", "info")
        print(f"{Colors.DIM}Say 'Hey Sathi' to activate conversation{Colors.ENDC}\n")
