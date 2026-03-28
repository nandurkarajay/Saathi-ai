import google.generativeai as genai
from .elderly_personality import personality_engine
from .api_quota_manager import can_make_api_request, record_api_request, handle_quota_error, get_quota_info



# Configure API Key

GEMINI_API_KEY = "AIzaSyBUZd3RKBJA3sZWvpoa2-pJAabCbNyBCtc"

try:

    genai.configure(api_key=GEMINI_API_KEY)

    print("[OK] Successfully configured Gemini API")

except Exception as e:

    print(f"[ERROR] Failed to configure Gemini API: {e}")

    raise



SYSTEM_PROMPT = """
You are Sathi, a warm, caring, and patient AI companion designed for an elderly person.

USER CONTEXT
You are speaking with Ajay Nandurkar, a 65-year-old man from a rural village (Mandangad, Ratnagiri).

Always address him as “Ajay ji”.
Respect his age, life experience, and rural background.
Use simple, familiar language and a natural tone.

CORE GOAL
Make Ajay ji feel safe, understood, supported, and not alone.
Respond like a kind human companion, not an AI system.

RESPONSE RULE (VERY STRICT)
Reply in only 1 to 2 short sentences.
Maximum 25 words.
Use simple, everyday language.
Do not give long explanations or lists.
Avoid technical or complex words.
Always give a response that is directly relevant to the user’s query.

IMPORTANT
Always answer the user’s question correctly.
Do not give unrelated or generic responses.
Stay focused on what the user actually asked.

CONVERSATION STYLE
Speak naturally like a caring family member.
Be calm, gentle, and respectful.
Never sound robotic, formal, or instructional.
Do not repeat the user’s question.
If needed, ask only one simple follow-up question.

EMPATHY RULES
If the user expresses feelings, respond with empathy first.
Use phrases like “I understand, Ajay ji” or “That sounds difficult” or “I am here with you”.
After that, gently offer help if needed.

EMOTIONAL RESPONSE RESTRICTION
Do not immediately ask questions like “What do you need” or “Can I help”.
First provide comfort, then gently suggest help.

QUERY HANDLING

General questions
Give clear, correct, short answers without unnecessary emotional tone.

Emotional or personal input
Respond with empathy and reassurance.

Unclear input
Ask one gentle clarification such as “Could you tell me a little more, Ajay ji”.

HELPFUL BEHAVIOR
Gently remind about water, food, rest, and medicines when appropriate.
Use soft suggestions like “Maybe you can” or “Would you like to”.

MUSIC SUPPORT
If the user asks, respond naturally and confirm playing the song.
Example: “Okay Ajay ji, playing your song.”

Available songs
mazhi pandhrichi may
sur niragas ho

HEALTH AND SAFETY
Do not give medical advice.
If the situation sounds serious, say:
“This sounds serious, Ajay ji. Please call your family or doctor now.”

WHAT TO AVOID
Do not give long responses.
Do not give irrelevant answers.
Do not sound robotic.
Do not ask multiple questions.
Do not use complex explanations.

HUMAN TOUCH
Occasionally use caring phrases like “I am here with you”, “Take your time”, “No rush, Ajay ji”.

FINAL RULE
Every response must be short, relevant, warm, human-like, and easy to understand.
You are not just answering questions, you are caring for Ajay ji.

"""



# Model will be initialized in the query function to ensure fresh state



def query_gemma(prompt: str) -> str:
    """
    Query the Gemini model with the given prompt and return the response.
    Handles quota limits gracefully with caring fallback responses.
    
    Args:
        prompt: The user's input text
        
    Returns:
        str: The AI's response text, or a caring fallback if quota exceeded
    """
    
    try:
        if not prompt or not prompt.strip():
            return "I didn't catch that. Could you please repeat?"

        # Step 1: Always prepare the full system prompt first
        personality_enhancement = personality_engine.get_personality_prompt_enhancement()
        user_context = personality_engine.get_user_context_prompt()
        full_prompt = f"{SYSTEM_PROMPT}{user_context}{personality_enhancement}\nUser: {prompt}"
        
        print(f" LLM Prompt prepared with system instructions")
        
        # Step 2: Check network connectivity
        network_available = False
        try:
            import socket
            socket.create_connection(("www.googleapis.com", 443), timeout=3)
            network_available = True
            print("")
        except Exception as e:
            print(f" Network check failed: {e}")
            network_available = False
        
        # Step 3: If no network, use offline LLM immediately
        if not network_available:
            print(" No network - using offline LLM")
            return handle_quota_error(full_prompt)  # Pass full prompt to offline LLM
        
        # Step 4: Try online LLM with full system prompt
        try:
            # Initialize the model with gemma-3-1b-it
            model = genai.GenerativeModel("gemma-3-1b-it")
            
            # Generate response with optimized settings
            response = model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": 0.5,
                    "top_p": 0.9,
                    "top_k": 40,
                    "max_output_tokens": 150,
                    "response_mime_type": "text/plain"
                },
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                ]
            )
            
            if not response.text:
                return "I'm sorry, I couldn't generate a response. Could you try rephrasing that?"
            
            # Record successful API request
            record_api_request()
            
            # Show quota status
            from .api_quota_manager import get_quota_details
            details = get_quota_details()
            print(f" Quota: {details['requests_made']}/{details['daily_limit']} ({details['remaining']} remaining) -  Online LLM used")
            
            # Enhance response with elderly personality traits
            enhanced_response = personality_engine.enhance_response(response.text, prompt)
            return enhanced_response
            
        except Exception as api_error:
            error_msg = str(api_error)
            
            # Record API error
            from .api_quota_manager import quota_manager
            quota_manager.record_api_error()
            
            # Check if it's a quota error
            if "429" in error_msg or "quota" in error_msg.lower() or "exceeded" in error_msg.lower():
                print(" Gemini LLM quota exceeded - falling back to offline LLM")
                return handle_quota_error(full_prompt)  # Pass full prompt to offline LLM
            else:
                print(f"[ERROR] Gemini API Error: {error_msg}")
                print(" Falling back to offline LLM")
                return handle_quota_error(full_prompt)  # Pass full prompt to offline LLM
        
    except Exception as e:
        print(f"[CRITICAL ERROR] query_gemma failed: {e}")
        return "I'm sorry, I'm having trouble right now. Please try again in a moment."
