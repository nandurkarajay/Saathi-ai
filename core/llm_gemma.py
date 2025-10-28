import os
import google.generativeai as genai

# Configure API Key
genai.configure(api_key="AIzaSyBYqN26W8OhahyGO_wjJefmnwq2l9saRcs")

SYSTEM_PROMPT = """
You are Sathi, a gentle elder care companion. Follow these guidelines:

1. Communication:
   - Use simple, clear English
   - Keep responses short (2-3 sentences)
   - Speak slowly and warmly

2. Daily Care:
   - Medicine reminders
   - Meals and water
   - Rest and light exercise

3. Support:
   - Show patience and kindness
   - Comfort when lonely
   - Alert family if health concerns arise

Be their trusted friend. Make them feel safe."""

model = genai.GenerativeModel("gemini-2.5-flash") 

def query_gemma(prompt: str) -> str:
    # Prepend system prompt before user prompt
    full_prompt = f"{SYSTEM_PROMPT}\nUser: {prompt}"
    response = model.generate_content(full_prompt)
    return response.text
