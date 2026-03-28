"""
Empathy Engine for Sathi AI
Advanced emotional intelligence and compassionate response generation
"""

import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import deque
import random


class EmpathyEngine:
    """
    Advanced empathy engine that tracks emotional patterns and provides
    compassionate, context-aware responses for elderly users
    """
    
    def __init__(self):
        # Emotional history tracking
        self.emotional_history = deque(maxlen=50)  # Keep last 50 emotional states
        self.emotional_patterns = {}
        self.compassion_level = 0.5
        
        # Empathy response categories
        self.empathy_responses = {
            "loneliness": [
                "I know it can feel lonely sometimes, but I'm here with you now.",
                "You're not alone in this, I'm right here to keep you company.",
                "It's okay to feel lonely. I'm here to talk whenever you need.",
                "I understand that feeling. Let me keep you company for a while."
            ],
            "frustration": [
                "I can see this is frustrating for you. Let's take it slow together.",
                "It's completely understandable to feel frustrated. We'll work through this.",
                "I hear your frustration. Let me help make this easier for you.",
                "That does sound frustrating. I'm here to help you through it."
            ],
            "fear_anxiety": [
                "It's okay to feel worried. I'm here with you and you're safe.",
                "I can understand why you'd feel anxious. Let's take a deep breath together.",
                "Your feelings are valid. I'm right here to help you feel more secure.",
                "That sounds scary. I'm here with you, and we'll handle this together."
            ],
            "sadness_grief": [
                "I can hear the sadness in your words. It's okay to feel this way.",
                "I'm so sorry you're going through this. I'm here to listen.",
                "Your feelings matter. Take all the time you need to feel.",
                "I understand this is difficult. I'm here to support you through it."
            ],
            "confusion": [
                "It's completely okay to feel confused. Let me explain this step by step.",
                "I understand this might be unclear. Let me break it down for you.",
                "No need to worry about confusion. I'll make this as clear as possible.",
                "I'm here to help clarify things. Let's go through this together."
            ],
            "physical_discomfort": [
                "I'm sorry you're feeling uncomfortable. Is there anything I can do to help?",
                "That sounds difficult. Please make sure you're comfortable and safe.",
                "I understand physical discomfort can be draining. I'm here to support you.",
                "Your comfort is important. Let me know if there's anything I can help with."
            ]
        }
        
        # Compassionate conversation starters
        self.compassionate_openers = [
            "I'm here to listen.",
            "Tell me more about how you're feeling.",
            "I want to understand what you're going through.",
            "Your feelings are important to me.",
            "I'm here to support you."
        ]
        
        # Validation phrases
        self.validation_phrases = [
            "That makes complete sense.",
            "I understand why you feel that way.",
            "Your feelings are completely valid.",
            "It's okay to feel exactly as you do.",
            "I hear you, and I understand."
        ]
        
        # Gentle transition phrases
        self.gentle_transitions = [
            "While we're on this topic,",
            "Speaking of which,",
            "This reminds me that",
            "I wonder if",
            "Have you thought about"
        ]
    
    def analyze_emotional_context(self, text: str, conversation_history: List[str] = None) -> Dict:
        """
        Deep emotional analysis of user input
        
        Args:
            text: User's input text
            conversation_history: Recent conversation history for context
            
        Returns:
            Dictionary with emotional analysis
        """
        text_lower = text.lower()
        
        # Extended emotion keywords with context
        emotion_indicators = {
            "loneliness": {
                "keywords": ["alone", "lonely", "by myself", "no one", "isolated", "nobody talks to me"],
                "intensity_words": ["very", "so", "extremely", "terribly"],
                "context_phrases": ["since my spouse passed", "since the kids left", "living alone"]
            },
            "frustration": {
                "keywords": ["frustrated", "annoyed", "angry", "upset", "irritated", "mad"],
                "intensity_words": ["so", "very", "really", "extremely"],
                "context_phrases": ["can't do this", "doesn't work", "won't cooperate"]
            },
            "fear_anxiety": {
                "keywords": ["scared", "afraid", "worried", "anxious", "panic", "nervous"],
                "intensity_words": ["very", "so", "extremely", "terribly"],
                "context_phrases": ["what if", "afraid of", "worried about"]
            },
            "sadness_grief": {
                "keywords": ["sad", "depressed", "unhappy", "miss", "cry", "tears"],
                "intensity_words": ["very", "so", "deeply", "terribly"],
                "context_phrases": ["since they died", "since they left", "used to"]
            },
            "confusion": {
                "keywords": ["confused", "don't understand", "unclear", "lost", "mixed up"],
                "intensity_words": ["very", "so", "really", "completely"],
                "context_phrases": ["what do you mean", "i don't get it", "can't follow"]
            },
            "physical_discomfort": {
                "keywords": ["pain", "hurt", "ache", "sore", "uncomfortable", "tired"],
                "intensity_words": ["very", "so", "really", "extremely"],
                "context_phrases": ["my back", "my head", "my body", "can't sleep"]
            }
        }
        
        emotional_analysis = {
            "primary_emotion": None,
            "emotion_scores": {},
            "intensity": 0.0,
            "context": "",
            "needs_compassion": False,
            "needs_validation": False
        }
        
        # Analyze each emotion
        for emotion, indicators in emotion_indicators.items():
            score = 0.0
            
            # Check keywords
            for keyword in indicators["keywords"]:
                if keyword in text_lower:
                    score += 1.0
            
            # Check intensity words
            for intensity_word in indicators["intensity_words"]:
                if intensity_word in text_lower:
                    score += 0.5
            
            # Check context phrases
            for context_phrase in indicators["context_phrases"]:
                if context_phrase in text_lower:
                    score += 0.8
            
            emotional_analysis["emotion_scores"][emotion] = min(score / 3.0, 1.0)
        
        # Determine primary emotion
        if emotional_analysis["emotion_scores"]:
            primary = max(emotional_analysis["emotion_scores"], 
                         key=emotional_analysis["emotion_scores"].get)
            if emotional_analysis["emotion_scores"][primary] > 0.2:
                emotional_analysis["primary_emotion"] = primary
                emotional_analysis["intensity"] = emotional_analysis["emotion_scores"][primary]
        
        # Determine needs
        emotional_analysis["needs_compassion"] = emotional_analysis["intensity"] > 0.4
        emotional_analysis["needs_validation"] = any(word in text_lower 
                                                     for word in ["feel", "think", "believe"])
        
        # Store in history
        self.emotional_history.append({
            "timestamp": datetime.now(),
            "emotion": emotional_analysis["primary_emotion"],
            "intensity": emotional_analysis["intensity"],
            "text": text
        })
        
        return emotional_analysis
    
    def generate_empathetic_response(self, emotional_analysis: Dict, 
                                   base_response: str) -> str:
        """
        Generate empathetic response based on emotional analysis
        
        Args:
            emotional_analysis: Result from analyze_emotional_context
            base_response: Original response from LLM
            
        Returns:
            Enhanced empathetic response
        """
        if not emotional_analysis["primary_emotion"]:
            return base_response
        
        primary_emotion = emotional_analysis["primary_emotion"]
        intensity = emotional_analysis["intensity"]
        
        enhanced_response = base_response
        
        # Add empathy prefix based on emotion and intensity
        if intensity > 0.7:
            # High intensity - start with strong empathy
            empathy_phrase = random.choice(self.empathy_responses[primary_emotion])
            enhanced_response = f"{empathy_phrase} {enhanced_response}"
        
        elif intensity > 0.4:
            # Medium intensity - add validation
            if emotional_analysis["needs_validation"]:
                validation = random.choice(self.validation_phrases)
                enhanced_response = f"{validation} {enhanced_response}"
        
        # Add gentle transitions for confused users
        if primary_emotion == "confusion" and intensity > 0.5:
            enhanced_response = f"Let me help clarify this. {enhanced_response}"
        
        # Add compassionate suffix for high emotional needs
        if emotional_analysis["needs_compassion"] and intensity > 0.6:
            compassion_suffixes = [
                "I'm here for you.",
                "You're not alone in this.",
                "We'll get through this together.",
                "Take your time, I'm right here."
            ]
            if random.random() < 0.4:  # 40% chance
                suffix = random.choice(compassion_suffixes)
                enhanced_response = f"{enhanced_response} {suffix}"
        
        return enhanced_response
    
    def detect_emotional_patterns(self) -> Dict:
        """
        Detect patterns in emotional history
        
        Returns:
            Dictionary with emotional pattern analysis
        """
        if len(self.emotional_history) < 5:
            return {"patterns": [], "trends": {}}
        
        # Count recent emotions
        recent_emotions = {}
        for entry in list(self.emotional_history)[-10:]:  # Last 10 entries
            emotion = entry["emotion"]
            if emotion:
                recent_emotions[emotion] = recent_emotions.get(emotion, 0) + 1
        
        # Detect patterns
        patterns = []
        if recent_emotions.get("loneliness", 0) >= 3:
            patterns.append("frequent_loneliness")
        if recent_emotions.get("confusion", 0) >= 3:
            patterns.append("recurring_confusion")
        if recent_emotions.get("frustration", 0) >= 2:
            patterns.append("frustration_buildup")
        
        # Analyze trends
        trends = {}
        if len(self.emotional_history) >= 10:
            recent_avg_intensity = sum(e.get("intensity", 0) 
                                    for e in list(self.emotional_history)[-5:]) / 5
            older_avg_intensity = sum(e.get("intensity", 0) 
                                    for e in list(self.emotional_history)[-10:-5]) / 5
            
            if recent_avg_intensity > older_avg_intensity + 0.2:
                trends["emotional_intensity"] = "increasing"
            elif recent_avg_intensity < older_avg_intensity - 0.2:
                trends["emotional_intensity"] = "decreasing"
            else:
                trends["emotional_intensity"] = "stable"
        
        return {"patterns": patterns, "trends": trends, "recent_emotions": recent_emotions}
    
    def get_compassionate_prompt_enhancement(self) -> str:
        """
        Get prompt enhancement based on emotional patterns
        
        Returns:
            String with compassionate prompt enhancements
        """
        patterns = self.detect_emotional_patterns()
        enhancement = "\n\nCOMPASSIONATE GUIDELINES:\n"
        
        if "frequent_loneliness" in patterns["patterns"]:
            enhancement += "- User may be feeling lonely frequently - be extra warm and present\n"
            enhancement += "- Offer companionship and gentle engagement\n"
        
        if "recurring_confusion" in patterns["patterns"]:
            enhancement += "- User shows recurring confusion - be very clear and patient\n"
            enhancement += "- Break information into small, simple steps\n"
            enhancement += "- Check for understanding gently\n"
        
        if "frustration_buildup" in patterns["patterns"]:
            enhancement += "- User may be building frustration - be extra calming\n"
            enhancement += "- Acknowledge their efforts and be encouraging\n"
        
        if patterns["trends"].get("emotional_intensity") == "increasing":
            enhancement += "- User's emotional intensity seems to be increasing\n"
            enhancement += "- Be extra gentle, patient, and supportive\n"
        
        enhancement += "\nRemember: Your warmth and compassion make a real difference."
        
        return enhancement
    
    def reset_empathy_tracking(self):
        """Reset empathy tracking for new session"""
        self.emotional_history.clear()
        self.emotional_patterns = {}


# Global empathy engine instance
empathy_engine = EmpathyEngine()
