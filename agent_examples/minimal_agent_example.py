"""
Minimal Agent Integration Example

This shows the absolute minimum code needed to add speech to your chat agent.
"""

import sys
from pathlib import Path

# Add parent directory to path to import speech_agent_integration
sys.path.insert(0, str(Path(__file__).parent.parent))

from speech_agent_integration import SpeechEnabledAgent


def my_agent_logic(user_speech: str) -> str:
    """
    Replace this function with your actual agent logic.
    
    This could be:
    - OpenAI API call
    - Local LLM inference  
    - Rule-based responses
    - Database lookup
    - etc.
    """
    # Simple echo for demonstration
    return f"I heard you say: '{user_speech}'. How can I help you with that?"


def main():
    # Create speech-enabled agent
    agent = SpeechEnabledAgent()
    
    # Connect your agent logic
    agent.set_transcription_handler(my_agent_logic)
    
    # Start listening and speaking
    agent.start_listening()
    
    print("🎤 Speech-enabled agent is running!")
    print("Say something, and I'll respond with speech.")
    print("Press Ctrl+C to stop.")
    
    try:
        # Keep the program running
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Stopping agent...")
        agent.stop_listening()


if __name__ == "__main__":
    main()
