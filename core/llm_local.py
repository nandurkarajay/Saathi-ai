"""
Local LLM Module for Sathi AI
Handles Qwen model for offline fallback when Gemini quota is exceeded
"""

import os
import sys
from pathlib import Path
from typing import Optional
import time

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from .config import (
    LOCAL_LLM_MODEL_PATH,
    LOCAL_LLM_ENABLED,
    LOCAL_LLM_MAX_TOKENS,
    LOCAL_LLM_TEMPERATURE,
    LOCAL_LLM_CONTEXT_LENGTH,
    LOCAL_LLM_N_THREADS,
    LOCAL_LLM_BATCH_SIZE
)
from .elderly_personality import personality_engine


class LocalLLMManager:
    """Manages local Qwen model for offline inference"""
    
    def __init__(self):
        self.model = None
        self.model_loaded = False
        self.last_used = None
        self.load_timeout = 30  # seconds
        
    def is_available(self) -> bool:
        """Check if local LLM is available and configured"""
        if not LOCAL_LLM_ENABLED:
            return False
        
        if not LOCAL_LLM_MODEL_PATH.exists():
            print(f"[LOCAL LLM] Model file not found: {LOCAL_LLM_MODEL_PATH}")
            return False
        
        return True
    
    def load_model(self) -> bool:
        """Load the Qwen model into memory"""
        if self.model_loaded:
            return True
        
        if not self.is_available():
            return False
        
        try:
            print("[LOCAL LLM] Loading Qwen model...")
            start_time = time.time()
            
            # Try to import llama-cpp-python
            try:
                from llama_cpp import Llama
            except ImportError:
                print("[LOCAL LLM] ERROR: llama-cpp-python not installed")
                print("[LOCAL LLM] Install with: pip install llama-cpp-python")
                return False
            
            # Load the model
            import os
            import sys
            # Suppress stderr to hide llama_context message
            with open(os.devnull, 'w') as devnull:
                old_stderr = sys.stderr
                sys.stderr = devnull
                try:
                    self.model = Llama(
                        model_path=str(LOCAL_LLM_MODEL_PATH),
                        n_ctx=LOCAL_LLM_CONTEXT_LENGTH,
                        n_threads=LOCAL_LLM_N_THREADS,
                        n_batch=LOCAL_LLM_BATCH_SIZE,
                        verbose=False  # Reduce technical messages
                    )
                finally:
                    sys.stderr = old_stderr
            
            self.model_loaded = True
            load_time = time.time() - start_time
            print(f"[LOCAL LLM] Model loaded successfully in {load_time:.1f}s")
            return True
            
        except Exception as e:
            print(f"[LOCAL LLM] Failed to load model: {e}")
            self.model = None
            self.model_loaded = False
            return False
    
    def unload_model(self):
        """Unload model to free memory"""
        if self.model:
            del self.model
            self.model = None
            self.model_loaded = False
            print("[LOCAL LLM] Model unloaded to free memory")
    
    def generate_response(self, prompt: str, max_retries: int = 2) -> Optional[str]:
        """Generate response using local Qwen model"""
        if not self.is_available():
            return None
        
        # Load model if not loaded
        if not self.model_loaded:
            if not self.load_model():
                return None
        
        try:
            print("[LOCAL LLM] Generating response...")
            start_time = time.time()
            
            # Generate response with STANDARD parameters to match Gemini behavior
            response = self.model(
                prompt,
                max_tokens=LOCAL_LLM_MAX_TOKENS,      # 150 tokens for short responses
                temperature=LOCAL_LLM_TEMPERATURE,    # 0.5 for consistency like Gemini
                stop=["User:", "Sathi:", "Ajay:", "\n\n", "Human:", "Assistant:", "I am", "I'm", "What can", "Can I", "How can", "what do you need", "help me with"],  # Enhanced stop tokens
                echo=False,  # Don't repeat prompt
                top_p=0.9,  # Add top_p for better coherence like Gemini
                repeat_penalty=1.3,  # Reduce repetition like Gemini
                frequency_penalty=0.3,  # Reduce word repetition like Gemini
                presence_penalty=0.2,  # Encourage new topics like Gemini
                typical_p=0.9,  # Focus on likely responses like Gemini
            )
            
            # Extract text from response
            if response and 'choices' in response and len(response['choices']) > 0:
                generated_text = response['choices'][0]['text'].strip()
                
                # Clean up the response
                generated_text = self._clean_response(generated_text)
                
                generation_time = time.time() - start_time
                print(f"[LOCAL LLM] Response generated in {generation_time:.1f}s")
                
                self.last_used = time.time()
                return generated_text
            else:
                print("[LOCAL LLM] No response generated")
                return None
                
        except Exception as e:
            print(f"[LOCAL LLM] Generation failed: {e}")
            
            # Retry once
            if max_retries > 0:
                print("[LOCAL LLM] Retrying...")
                return self.generate_response(prompt, max_retries - 1)
            
            return None
    
    def _clean_response(self, text: str) -> str:
        """Clean up generated response to match Sathi personality exactly"""
        if not text:
            return "I'm here with you, Ajay ji."  # Default empathetic response
        
        # Remove conversation markers and artifacts
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip conversation markers and empty lines
            if line and not line.startswith(('User:', 'Sathi:', 'Assistant:', 'Human:', 'Ajay:', 'AI:', 'You are')):
                cleaned_lines.append(line)
        
        # Join lines into natural conversation
        cleaned = ' '.join(cleaned_lines)
        
        # Ensure it follows new system prompt rules (1-2 sentences, max 25 words)
        words = cleaned.split()
        
        # CRITICAL: Ensure "Ajay ji" is present
        if "Ajay ji" not in cleaned:
            cleaned = f"Ajay ji, {cleaned}"  # Force add Ajay ji
        elif "ajay ji" in cleaned.lower():  # Check for lowercase version
            cleaned = cleaned.replace("ajay ji", "Ajay ji")  # Fix capitalization
        
        # Ensure minimum length (at least 5 words)
        if len(words) < 5:
            cleaned = f"I understand, Ajay ji. I'm here to help you."
        
        # Ensure maximum length (25 words)
        if len(words) > 25:
            # Cut to first 25 words and end at sentence boundary
            cleaned = ' '.join(words[:25])
            if cleaned[-1] not in '.!?':
                cleaned += '.'
        
        # Remove excessive repetition
        if len(words) > 3:
            unique_words = []
            prev_word = ""
            for word in words[:25]:  # Only check first 25 words
                if word.lower() != prev_word.lower():
                    unique_words.append(word)
                    prev_word = word
                elif len(unique_words) < 2:  # Allow minimal repetition
                    unique_words.append(word)
            cleaned = ' '.join(unique_words[:25])  # Ensure max 25 words
        
        # Ensure proper punctuation
        if cleaned:
            if cleaned[-1] not in '.!?':
                cleaned += '.'
            # Remove multiple punctuation
            cleaned = cleaned.replace('..', '.').replace('!!', '!').replace('??', '?')
        
        return cleaned.strip()


# Global local LLM manager
local_llm_manager = LocalLLMManager()


def query_local_llm(full_prompt_or_user_input: str) -> Optional[str]:
    """
    Query local Qwen model with full prompt or user input
    
    Args:
        full_prompt_or_user_input: Either full prompt with system instructions or just user input
        
    Returns:
        str: The AI's response, or None if unavailable
    """
    if not local_llm_manager.is_available():
        print("[LOCAL LLM] Local LLM not available")
        return None
    
    # Check if this is a full prompt (contains system instructions) or just user input
    if "You are Sathi" in full_prompt_or_user_input:
        # This is already a full prompt with system instructions - use directly
        print("[LOCAL LLM] Using full prompt with system instructions")
        full_prompt = full_prompt_or_user_input
    else:
        # This is just user input - use MAIN system prompt directly
        print("[LOCAL LLM] Using main system prompt from Gemini")
        # Import the main system prompt
        from core.llm_gemma import SYSTEM_PROMPT
        full_prompt = SYSTEM_PROMPT
    
    # Generate response
    response = local_llm_manager.generate_response(full_prompt)
    
    if response:
        # Clean response but NO personality enhancement - let system prompt do the work
        cleaned_response = local_llm_manager._clean_response(response)
        print("[LOCAL LLM] Using system prompt response (no hardcoded enhancement)")
        return cleaned_response
    
    return response


def preload_model():
    """Preload the local model for faster responses"""
    if local_llm_manager.is_available():
        local_llm_manager.load_model()


def unload_model():
    """Unload the local model to free memory"""
    local_llm_manager.unload_model()


def get_model_status():
    """Get current model status"""
    if not LOCAL_LLM_ENABLED:
        return "🔴 Local LLM disabled"
    
    if not LOCAL_LLM_MODEL_PATH.exists():
        return f"🔴 Model file not found: {LOCAL_LLM_MODEL_PATH}"
    
    if local_llm_manager.model_loaded:
        return "🟢 Local LLM loaded and ready"
    
    return "🟡 Local LLM available but not loaded"


if __name__ == "__main__":
    # Test local LLM
    print("="*60)
    print("🤖 LOCAL LLM TEST")
    print("="*60)
    
    print(f"Model status: {get_model_status()}")
    print(f"Model path: {LOCAL_LLM_MODEL_PATH}")
    print(f"Model exists: {LOCAL_LLM_MODEL_PATH.exists()}")
    
    if local_llm_manager.is_available():
        print("\nTesting model loading...")
        if local_llm_manager.load_model():
            print("✅ Model loaded successfully")
            
            # Test a simple query
            test_queries = [
                "Hello, how are you?",
                "What time is it?",
                "I'm feeling a bit lonely today"
            ]
            
            for query in test_queries:
                print(f"\nUser: {query}")
                response = query_local_llm(query)
                print(f"Sathi: {response}")
                print("-" * 40)
            
            # Unload model
            unload_model()
        else:
            print("❌ Failed to load model")
    else:
        print("❌ Local LLM not available")
    
    print("\n" + "="*60)
