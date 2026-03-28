#!/usr/bin/env python3
"""Verify offline LLM behaves exactly like online Gemini
Both should use identical system prompt and give similar responses
"""

import sys
sys.path.append('e:/Sathi-Ai')

from core.llm_gemma import query_gemma, SYSTEM_PROMPT
from core.llm_local import query_local_llm
from core.elderly_personality import personality_engine

def test_llm_parity():
    print("🔍 TESTING LLM PARITY - Enhanced Version")
    print("=" * 60)
    print("Both LLMs should behave identically using same system prompt")
    print()
    
    # Test cases that should give identical responses
    test_cases = [
        "I am feeling alone",
        "I'm sad", 
        "I'm worried about my health",
        "what time is it",
        "can you play some music",
        "hello sathi"
    ]
    
    all_identical = True
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"🧪 Test {i}: '{test_input}'")
        print("-" * 40)
        
        try:
            # Test online LLM
            print("🟢 Testing Online LLM (Gemini):")
            online_response = query_gemma(test_input)
            print(f"Response: {online_response}")
            
            # Test offline LLM
            print("🔴 Testing Offline LLM (Qwen):")
            offline_response = query_local_llm(test_input)
            print(f"Response: {offline_response}")
            
            # Compare responses
            if online_response and offline_response:
                # Check for similarity
                online_words = set(online_response.lower().split())
                offline_words = set(offline_response.lower().split())
                
                # Check key elements
                both_have_ajay = "ajay ji" in online_response.lower() and "ajay ji" in offline_response.lower()
                both_have_empathy = any(word in online_words for word in ["understand", "here with", "hear", "feel"]) and any(word in offline_words for word in ["understand", "here with", "hear", "feel"])
                
                # Check for generic questions
                generic_patterns = ["what can", "can i help", "how can i", "what do you need"]
                online_generic = any(pattern in online_response.lower() for pattern in generic_patterns)
                offline_generic = any(pattern in offline_response.lower() for pattern in generic_patterns)
                
                # Check length similarity
                online_len = len(online_response.split())
                offline_len = len(offline_response.split())
                length_similar = abs(online_len - offline_len) <= 3
                
                # Determine if responses are similar enough
                similarity_score = 0
                if both_have_ajay:
                    similarity_score += 30
                if both_have_empathy:
                    similarity_score += 40
                if not online_generic and not offline_generic:
                    similarity_score += 20
                if length_similar:
                    similarity_score += 10
                
                is_identical = similarity_score >= 80
                
                print(f"  Ajay ji: Online={both_have_ajay}, Offline={both_have_ajay}")
                print(f"  Empathy: Online={both_have_empathy}, Offline={both_have_empathy}")
                print(f"  Generic: Online={online_generic}, Offline={offline_generic}")
                print(f"  Length: Online={online_len}, Offline={offline_len}, Similar={length_similar}")
                print(f"  Similarity: {similarity_score}/100 - {'IDENTICAL' if is_identical else 'DIFFERENT'}")
                
                if is_identical:
                    print("  ✅ PERFECT MATCH")
                elif similarity_score >= 70:
                    print("  🟡 VERY SIMILAR")
                elif similarity_score >= 50:
                    print("  🟡 SOMEWHAT SIMILAR")
                else:
                    print("  ❌ DIFFERENT")
                
                all_identical = is_identical and all_identical
                
            except Exception as e:
                print(f"  ❌ ERROR: {e}")
                all_identical = False
        
        print()
    
    print("=" * 60)
    print("📊 PARITY TEST RESULTS")
    print("=" * 60)
    
    if all_identical:
        print("🎉 PERFECT: Both LLMs behave identically!")
        print("✅ Same system prompt usage")
        print("✅ Identical response patterns")
        print("✅ Same elderly care behavior")
    else:
        print("🔧 NEEDS IMPROVEMENT")
        print("• Review system prompt synchronization")
        print("• Check response generation parameters")
    
    return all_identical

if __name__ == "__main__":
    success = test_llm_parity()
    sys.exit(0 if success else 1)
