"""
Elderly Personality Module for Sathi AI
Implements caring, patient, and emotion-aware personality traits for elderly users
"""

import re
import random
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from .empathy_engine import empathy_engine


class ElderlyPersonality:
    """
    Personality engine that adds caring, patient, and emotion-aware traits
    specifically designed for elderly users
    """
    
    def __init__(self):
        self.emotional_state = {
            "mood": "neutral",
            "anxiety_level": 0.0,
            "comfort_level": 0.5,
            "trust_level": 0.5,
            "last_interaction": None
        }
        
        # User specific context
        self.user_context = {
            "name": "Ajay Nandurkar",
            "age": 65,
            "location": "Mandangad village, Ratnagiri district",
            "background": "rural village",
            "preferred_address": ["Ajay", "Ajay ji"]
        }
        
        self.conversation_patterns = {
            "repetitions": defaultdict(int),
            "topics": defaultdict(list),
            "response_times": [],
            "confusion_indicators": []
        }
        
        # Emotion indicators in text
        self.emotion_keywords = {
            "sad": ["sad", "unhappy", "depressed", "lonely", "miss", "cry", "tears"],
            "anxious": ["worried", "anxious", "scared", "afraid", "nervous", "panic"],
            "confused": ["confused", "don't understand", "unclear", "what do you mean", "lost"],
            "happy": ["happy", "glad", "good", "great", "wonderful", "pleased"],
            "frustrated": ["frustrated", "annoyed", "angry", "upset", "mad"],
            "tired": ["tired", "exhausted", "fatigue", "sleepy", "weak"],
            "pain": ["pain", "hurt", "ache", "sore", "uncomfortable"]
        }
        
        # Caring response templates
        self.caring_templates = {
            "comforting": [
                "I'm here with you, dear.",
                "You're safe, I'm listening.",
                "Take your time, I'm right here.",
                "That sounds difficult, I understand."
            ],
            "reassuring": [
                "Everything will be alright.",
                "You're doing just fine.",
                "It's okay to feel this way.",
                "I'm here to help you through this."
            ],
            "patient": [
                "Take all the time you need.",
                "There's no rush at all.",
                "We can go as slow as you like.",
                "I'm here, no need to hurry."
            ],
            "encouraging": [
                "You're doing wonderfully.",
                "That's very good, keep going.",
                "I'm proud of you.",
                "You're managing very well."
            ]
        }
        
        # Patience phrases for repeated questions
        self.patience_responses = [
            "Of course, let me help you with that again.",
            "I'm happy to explain that once more.",
            "No problem at all, let me go through it again.",
            "I don't mind repeating, it's important to understand.",
            "Let me try explaining it a different way.",
            "Of course, repetition helps us learn."
        ]
    
    def detect_emotion(self, text: str) -> Dict[str, float]:
        """
        Detect emotions in user's text input
        
        Args:
            text: User's input text
            
        Returns:
            Dictionary with emotion scores
        """
        text = text.lower()
        emotions = {}
        
        for emotion, keywords in self.emotion_keywords.items():
            score = 0.0
            for keyword in keywords:
                if keyword in text:
                    score += 1.0
            emotions[emotion] = min(score / len(keywords), 1.0)
        
        return emotions
    
    def update_emotional_state(self, emotions: Dict[str, float]):
        """Update the user's emotional state based on detected emotions"""
        if emotions.get("sad", 0) > 0.3:
            self.emotional_state["mood"] = "sad"
            self.emotional_state["comfort_level"] = max(0, self.emotional_state["comfort_level"] - 0.1)
        
        if emotions.get("anxious", 0) > 0.3:
            self.emotional_state["anxiety_level"] = min(1.0, self.emotional_state["anxiety_level"] + 0.1)
            self.emotional_state["comfort_level"] = max(0, self.emotional_state["comfort_level"] - 0.1)
        
        if emotions.get("confused", 0) > 0.3:
            self.conversation_patterns["confusion_indicators"].append(datetime.now())
            self.emotional_state["comfort_level"] = max(0, self.emotional_state["comfort_level"] - 0.05)
        
        if emotions.get("happy", 0) > 0.3:
            self.emotional_state["mood"] = "happy"
            self.emotional_state["comfort_level"] = min(1.0, self.emotional_state["comfort_level"] + 0.1)
            self.emotional_state["trust_level"] = min(1.0, self.emotional_state["trust_level"] + 0.05)
        
        self.emotional_state["last_interaction"] = datetime.now()
    
    def detect_repetition(self, text: str) -> bool:
        """
        Detect if the user is repeating themselves
        
        Args:
            text: Current user input
            
        Returns:
            True if repetition is detected
        """
        text_clean = re.sub(r'[^\w\s]', '', text.lower()).strip()
        
        # Check against recent topics
        recent_topics = self.conversation_patterns["topics"]
        current_time = datetime.now()
        
        for topic, timestamps in recent_topics.items():
            # Check if this topic was discussed in the last 10 minutes
            recent_timestamps = [ts for ts in timestamps if current_time - ts < timedelta(minutes=10)]
            if recent_timestamps and self._similarity(text_clean, topic) > 0.8:
                self.conversation_patterns["repetitions"][topic] += 1
                return True
        
        # Add current text to topics
        recent_topics[text_clean].append(current_time)
        return False
    
    def _similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def enhance_response(self, base_response: str, user_input: str) -> str:
        """
        Enhance the base response with personality traits
        
        Args:
            base_response: Original response from LLM
            user_input: User's input text
            
        Returns:
            Enhanced response with personality
        """
        emotions = self.detect_emotion(user_input)
        self.update_emotional_state(emotions)
        
        # Get empathetic analysis first
        emotional_analysis = empathy_engine.analyze_emotional_context(user_input)
        
        # Apply empathy engine enhancement
        enhanced = empathy_engine.generate_empathetic_response(emotional_analysis, base_response)
        
        # Add caring prefixes based on emotional state
        if emotions.get("sad", 0) > 0.3:
            comfort_phrase = random.choice(self.caring_templates["comforting"])
            enhanced = f"{comfort_phrase} {enhanced}"
        
        elif emotions.get("anxious", 0) > 0.3:
            reassure_phrase = random.choice(self.caring_templates["reassuring"])
            enhanced = f"{reassure_phrase} {enhanced}"
        
        elif emotions.get("confused", 0) > 0.3:
            enhanced = f"Let me explain this clearly. {enhanced}"
        
        # Add patience for repetitions
        if self.detect_repetition(user_input):
            patience_phrase = random.choice(self.patience_responses)
            enhanced = f"{patience_phrase} {enhanced}"
        
        # Add gentle suffixes for better connection
        if self.emotional_state["comfort_level"] < 0.5:
            gentle_suffixes = ["I'm here with you.", "You're not alone.", "Take your time."]
            if random.random() < 0.3:  # 30% chance to add gentle suffix
                suffix = random.choice(gentle_suffixes)
                enhanced = f"{enhanced} {suffix}"
        
        # Ensure response doesn't get too long
        if len(enhanced) > len(base_response) * 2.5:
            enhanced = base_response  # Fallback to original if too long
        
        return enhanced
    
    def get_user_context_prompt(self) -> str:
        """
        Get user context information for the system prompt
        """
        context = f"\n\nUSER SPECIFIC CONTEXT:\n"
        context += f"- Name: {self.user_context['name']}\n"
        context += f"- Age: {self.user_context['age']} years old\n"
        context += f"- Location: {self.user_context['location']}\n"
        context += f"- Background: {self.user_context['background']}\n"
        context += f"- Address as: {', '.join(self.user_context['preferred_address'])}\n"
        context += f"- Be mindful of rural village lifestyle and cultural context\n"
        context += f"- Consider age-appropriate communication and patience\n"
        return context

    def get_personality_prompt_enhancement(self) -> str:
        """
        Get additional prompt text to enhance the base system prompt
        with elderly personality traits
        """
        current_mood = self.emotional_state["mood"]
        comfort_level = self.emotional_state["comfort_level"]
        
        enhancement = "\n\nCURRENT PERSONALITY SETTINGS:\n"
        
        if comfort_level < 0.3:
            enhancement += "- User seems uncomfortable, be extra gentle and patient\n"
            enhancement += "- Use shorter sentences and simpler words\n"
            enhancement += "- Offer reassurance frequently\n"
        
        elif current_mood == "sad":
            enhancement += "- User seems sad, be extra comforting\n"
            enhancement += "- Acknowledge their feelings gently\n"
            enhancement += "- Offer warm companionship\n"
        
        elif self.emotional_state["anxiety_level"] > 0.5:
            enhancement += "- User seems anxious, be very calming\n"
            enhancement += "- Use soothing and reassuring tone\n"
            enhancement += "- Avoid overwhelming with information\n"
        
        if len(self.conversation_patterns["confusion_indicators"]) > 3:
            enhancement += "- User has shown confusion recently\n"
            enhancement += "- Break down information into small steps\n"
            enhancement += "- Check for understanding gently\n"
        
        # Add compassionate guidelines from empathy engine
        compassionate_guidance = empathy_engine.get_compassionate_prompt_enhancement()
        enhancement += compassionate_guidance
        
        enhancement += "\nRemember: You are a warm, patient companion. Make them feel safe and cared for."
        
        return enhancement
    
    def reset_session(self):
        """Reset conversation patterns for a new session"""
        self.conversation_patterns = {
            "repetitions": defaultdict(int),
            "topics": defaultdict(list),
            "response_times": [],
            "confusion_indicators": []
        }
        self.emotional_state["last_interaction"] = datetime.now()


# Global instance
personality_engine = ElderlyPersonality()
