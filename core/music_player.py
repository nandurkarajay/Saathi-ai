"""
Local Offline Music Player Module for Sathi AI
Handles bhajan/song playback for elderly users with simple voice commands
"""

import os
import re
import subprocess
import time
import signal
import logging
import threading
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False

# Global pygame availability flag for the class
_GLOBAL_PYGAME_AVAILABLE = PYGAME_AVAILABLE

@dataclass
class MusicResponse:
    """Container for music player responses"""
    spoken_text: str
    display_text: str
    success: bool = True
    song_found: bool = True

# Configure logging
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SONGS_DIR = PROJECT_ROOT / 'songs'
LOG_PATH = PROJECT_ROOT / 'data' / 'music_player.log'

# Ensure directories exist
SONGS_DIR.mkdir(exist_ok=True)
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOG_PATH),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class MusicPlayer:
    """Local offline music player for bhajans and songs"""
    
    # Music request trigger patterns
    MUSIC_PATTERNS = [
        r'play\s+(?:song|music|bhajan)',
        r'play\s+\w+(?:\s+\w+)*',  # "play [song_name]" with multiple words
        r'start\s+(?:music|song|bhajan)',
        r'(?:song|music|bhajan)\s+play',
        r'play\s+the\s+(?:song|bhajan)',
        r'^\s*music\s*$',  # Just "music" by itself
        r'^\s*song\s*$',  # Just "song" by itself
        r'^\s*bhajan\s*$',  # Just "bhajan" by itself
        r'^\s*the\s+music\s*$',  # "the music" by itself
        r'^\s*the\s+song\s*$',  # "the song" by itself
        r'^\s*the\s+bhajan\s*$',  # "the bhajan" by itself
        r'^\s*and\s+music\s*$',  # "and music" by itself
        # Add patterns for song names without "play" (for elderly users who might forget)
        r'^(?:sur|mazhi)\s+\w+(?:\s+\w+)*',  # Song names starting with known words
        r'^\s*\w+\s+(?:niragas|pandhrichi)\s+\w+\s*$',  # More specific song patterns
    ]
    
    # Stop command patterns
    STOP_PATTERNS = [
        r'stop\s+(?:music|song|bhajan)',
        r'stop\s+playing',
        r'pause\s+(?:music|song|bhajan)',
        r'silence',
        r'quiet',
        r'shut\s+up',
        r'stop',  # Just "stop" by itself
        r'pause',  # Just "pause" by itself
    ]
    
    # Words to remove from song names
    FILTER_WORDS = {
        'play', 'song', 'songs', 'music', 'bhajan', 'bhajans', 
        'the', 'a', 'an', 'start', 'please', 'can', 'you', 'me',
        'to', 'want', 'would', 'like', 'hear', 'listen'
    }
    
    def __init__(self):
        self.current_process = None
        self.is_playing = False
        self.logger = logging.getLogger(__name__)
        self._available_songs = None
        self._songs_last_updated = 0
        self._pygame_mixer = None
        
        # Initialize pygame mixer if available
        if _GLOBAL_PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
                self._pygame_mixer = pygame.mixer
                self.logger.info("Pygame mixer initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize pygame mixer: {e}")
                self._pygame_mixer = None
        
    def is_stop_request(self, text: str) -> bool:
        """Check if the text is a stop music request"""
        text_lower = text.lower().strip().rstrip('.!?')  # Remove trailing punctuation
        
        # If music is currently playing, be very lenient with stop detection
        if self.is_playing:
            # When music is playing, ANY stop-like word should trigger stop
            stop_keywords = ['stop', 'pause', 'silence', 'quiet', 'end', 'off', 'music', 'song', 'bhajan']
            # But only if it's a short command (not a complex sentence)
            words = text_lower.split()
            if len(words) <= 2:  # Short commands like "stop music", "music", "stop"
                return any(keyword in text_lower for keyword in stop_keywords)
        
        return any(re.search(pattern, text_lower) for pattern in self.STOP_PATTERNS)
    
    def is_music_request(self, text: str) -> bool:
        """Check if the text is a music playback request"""
        text_lower = text.lower().strip().rstrip('.!?')  # Remove trailing punctuation
        
        # If music is currently playing, be more restrictive about new music requests
        if self.is_playing:
            # When music is playing, don't allow just "music" to start new music
            # This prevents "music" from being interpreted as "play music" when stopping
            if text_lower in ['music', 'song', 'bhajan']:
                return False
        
        return any(re.search(pattern, text_lower) for pattern in self.MUSIC_PATTERNS)
    
    def extract_song_name(self, text: str) -> Optional[str]:
        """Extract and normalize song name from user input"""
        text_lower = text.lower().strip()
        
        # Remove stop words and filter words
        words = text_lower.split()
        filtered_words = [
            word for word in words 
            if word not in self.FILTER_WORDS and word.isalnum()
        ]
        
        if not filtered_words:
            return None
            
        # Join with underscores and normalize
        song_name = '_'.join(filtered_words)
        
        # Clean up multiple underscores and trailing/leading underscores
        song_name = re.sub(r'_+', '_', song_name).strip('_')
        
        return song_name if song_name else None
    
    def get_available_songs(self) -> List[str]:
        """Get list of available songs with caching for performance"""
        current_time = time.time()
        
        # Cache songs for 30 seconds to avoid repeated disk access
        if (self._available_songs is None or 
            current_time - self._songs_last_updated > 30):
            
            try:
                song_files = []
                for ext in ['*.mp3', '*.wav', '*.m4a', '*.flac', '*.ogg']:
                    song_files.extend(SONGS_DIR.glob(ext))
                    # Don't scan uppercase separately - glob is case-insensitive on Windows
                
                # Extract song names without extension and remove duplicates
                song_names = [
                    f.stem.lower().replace(' ', '_') 
                    for f in song_files
                ]
                self._available_songs = list(dict.fromkeys(song_names))  # Remove duplicates while preserving order
                self._songs_last_updated = current_time
                
                self.logger.info(f"Found {len(self._available_songs)} songs: {self._available_songs}")
                
            except Exception as e:
                self.logger.error(f"Error scanning songs directory: {e}")
                self._available_songs = []
        
        return self._available_songs
    
    def find_best_match(self, song_name: str) -> Optional[str]:
        """Find best matching song using partial matching"""
        available_songs = self.get_available_songs()
        
        if not available_songs:
            return None
        
        song_name_lower = song_name.lower()
        
        # Exact match first
        if song_name_lower in available_songs:
            return song_name_lower
        
        # Partial matching - find songs that contain the search term
        matches = []
        for song in available_songs:
            if song_name_lower in song or song in song_name_lower:
                matches.append(song)
        
        # If multiple matches, prefer the shortest (most specific)
        if matches:
            best_match = min(matches, key=len)
            self.logger.info(f"Partial match: '{song_name}' -> '{best_match}'")
            return best_match
        
        # Fuzzy matching - check for substring matches
        best_score = 0
        best_match = None
        
        for song in available_songs:
            score = self._calculate_similarity(song_name_lower, song)
            if score > best_score and score > 0.6:  # 60% similarity threshold
                best_score = score
                best_match = song
        
        if best_match:
            self.logger.info(f"Fuzzy match: '{song_name}' -> '{best_match}' (score: {best_score:.2f})")
        
        return best_match
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate simple similarity score between two strings"""
        # Convert to character sets for basic similarity
        set1 = set(str1.replace('_', ''))
        set2 = set(str2.replace('_', ''))
        
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def stop_music(self) -> bool:
        """Stop currently playing music"""
        if not self.is_playing:
            return False
        
        try:
            # Stop pygame music if playing
            if self._pygame_mixer:
                if self._pygame_mixer.music.get_busy():
                    self._pygame_mixer.music.stop()
                    self.logger.info("Pygame music stopped")
            
            # Stop subprocess if running
            if self.current_process:
                self.current_process.terminate()
                try:
                    self.current_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.current_process.kill()
                    self.current_process.wait()
                self.current_process = None
            
            self.is_playing = False
            self.logger.info("Music stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping music: {e}")
            self.is_playing = False
            self.current_process = None
            return False
    
    def play_song(self, song_name: str) -> MusicResponse:
        """Play a song by name"""
        try:
            # Stop any currently playing song
            if self.is_playing:
                self.stop_music()
            
            # Find the best matching song
            matched_song = self.find_best_match(song_name)
            
            if not matched_song:
                self.logger.warning(f"No song found for: {song_name}")
                return MusicResponse(
                    spoken_text="Sorry, I could not find that song",
                    display_text=f"❌ Song not found: {song_name}",
                    success=True,
                    song_found=False
                )
            
            # Find the actual file
            song_file = None
            for ext in ['mp3', 'wav', 'm4a', 'flac', 'ogg']:
                potential_file = SONGS_DIR / f"{matched_song}.{ext}"
                if potential_file.exists():
                    song_file = potential_file
                    break
            
            if not song_file:
                self.logger.error(f"Song file not found for: {matched_song}")
                return MusicResponse(
                    spoken_text="Sorry, I could not find that song file",
                    display_text=f"❌ Song file not found: {matched_song}",
                    success=True,
                    song_found=False
                )
            
            # Try pygame first (best for cross-platform)
            if self._pygame_mixer:
                try:
                    self._pygame_mixer.music.load(str(song_file))
                    self._pygame_mixer.music.play()
                    self.is_playing = True
                    
                    # Start a thread to monitor when music finishes
                    def monitor_music():
                        while self._pygame_mixer.music.get_busy():
                            time.sleep(0.5)
                        self.is_playing = False
                    
                    monitor_thread = threading.Thread(target=monitor_music, daemon=True)
                    monitor_thread.start()
                    
                    display_name = matched_song.replace('_', ' ').title()
                    self.logger.info(f"Started playing: {display_name} using pygame")
                    
                    return MusicResponse(
                        spoken_text=f"Playing {display_name}",
                        display_text=f"🎵 Playing: {display_name}",
                        success=True,
                        song_found=True
                    )
                    
                except Exception as e:
                    self.logger.error(f"Pygame playback failed: {e}")
            
            # Try different audio players based on availability
            player_commands = [
                ['powershell', '-Command', f'Add-Type -AssemblyName System.Media; (New-Object System.Media.SoundPlayer "{song_file}").PlaySync();'],  # Windows built-in
                ['mpg123', '-q', str(song_file)],  # mpg123 (preferred)
                ['ffplay', '-nodisp', '-autoexit', str(song_file)],  # ffplay
                ['vlc', '--intf', 'dummy', '--play-and-exit', str(song_file)],  # VLC
                ['mplayer', '-really-quiet', str(song_file)],  # MPlayer
            ]
            
            for cmd in player_commands:
                try:
                    # Check if player is available
                    subprocess.run(['where', cmd[0]], capture_output=True, check=True)
                    
                    # Start the player
                    self.current_process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    
                    self.is_playing = True
                    
                    # Format song name for display (replace underscores with spaces)
                    display_name = matched_song.replace('_', ' ').title()
                    
                    self.logger.info(f"Started playing: {display_name} using {cmd[0]}")
                    
                    return MusicResponse(
                        spoken_text=f"Playing {display_name}",
                        display_text=f"🎵 Playing: {display_name}",
                        success=True,
                        song_found=True
                    )
                    
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue  # Try next player
            
            # No audio player found
            self.logger.error("No audio player found (mpg123, ffplay, vlc, mplayer)")
            return MusicResponse(
                spoken_text="Sorry, no audio player is available on this system",
                display_text="❌ No audio player found. Please install mpg123.",
                success=False,
                song_found=True
            )
            
        except Exception as e:
            self.logger.error(f"Error playing song: {e}")
            return MusicResponse(
                spoken_text="Sorry, I had trouble playing that song",
                display_text=f"❌ Error playing song: {str(e)}",
                success=False,
                song_found=True
            )
    
    def get_first_available_song(self) -> Optional[str]:
        """Get the first available song from the songs directory"""
        try:
            for ext in ['*.mp3', '*.wav', '*.m4a', '*.flac', '*.ogg']:
                song_files = list(SONGS_DIR.glob(ext))
                song_files.extend(SONGS_DIR.glob(ext.upper()))
                
                if song_files:
                    # Sort by name and return the first one
                    song_files.sort(key=lambda x: x.name.lower())
                    first_song = song_files[0]
                    song_name = first_song.stem.lower().replace(' ', '_')
                    self.logger.info(f"First available song: {song_name}")
                    return song_name
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting first available song: {e}")
            return None
    
    def get_status(self) -> Dict:
        """Get current player status"""
        return {
            'is_playing': self.is_playing,
            'available_songs': len(self.get_available_songs()),
            'songs_directory': str(SONGS_DIR)
        }

# Global music player instance
music_player = MusicPlayer()

def is_music_request(text: str) -> bool:
    """Check if text is a music request (convenience function)"""
    return music_player.is_music_request(text)

def is_stop_request(text: str) -> bool:
    """Check if text is a stop request (convenience function)"""
    return music_player.is_stop_request(text)

def handle_music(text: str, speak_func=None) -> bool:
    """
    Main handler function for music requests
    
    Args:
        text: User's input text
        speak_func: Function to speak responses (optional)
        
    Returns:
        bool: True if music request was handled, False otherwise
    """
    try:
        # Handle stop requests first
        if is_stop_request(text):
            if music_player.stop_music():
                response = MusicResponse(
                    spoken_text="Music stopped",
                    display_text="⏹️ Music stopped"
                )
            else:
                response = MusicResponse(
                    spoken_text="No music is playing",
                    display_text="ℹ️ No music is currently playing"
                )
            
            if speak_func:
                speak_func(response.spoken_text)
            return True  # IMPORTANT: Return here so we don't continue to music requests
        
        # Handle play requests (only if stop was not detected)
        if is_music_request(text):
            song_name = music_player.extract_song_name(text)
            
            if not song_name:
                # Check if this is a generic "play music" request
                text_lower = text.lower().strip()
                generic_music_phrases = ['play music', 'play song', 'start music', 'play the music', 'play the song']
                
                if any(phrase in text_lower for phrase in generic_music_phrases):
                    # Play the first available song
                    first_song = music_player.get_first_available_song()
                    if first_song:
                        response = music_player.play_song(first_song)
                        # Update response to indicate it's the first song
                        display_name = first_song.replace('_', ' ').title()
                        response.spoken_text = f"Playing {display_name}"
                        response.display_text = f"🎵 Playing: {display_name}"
                    else:
                        response = MusicResponse(
                            spoken_text="Sorry, I couldn't find any songs",
                            display_text="❌ No songs found in the songs directory"
                        )
                else:
                    response = MusicResponse(
                        spoken_text="Which song would you like to hear?",
                        display_text="❌ Please specify a song name"
                    )
            else:
                response = music_player.play_song(song_name)
            
            if speak_func:
                speak_func(response.spoken_text)
            return True
        
        return False
        
    except Exception as e:
        logging.error(f"Error in handle_music: {e}")
        error_response = MusicResponse(
            spoken_text="Sorry, I had trouble with the music player",
            display_text=f"❌ Music player error: {str(e)}"
        )
        
        if speak_func:
            speak_func(error_response.spoken_text)
        return True

# Convenience functions
def get_music_status() -> Dict:
    """Get current music player status"""
    return music_player.get_status()

def stop_all_music() -> bool:
    """Stop all music playback"""
    return music_player.stop_music()

def list_available_songs() -> List[str]:
    """Get list of available song names"""
    return music_player.get_available_songs()
