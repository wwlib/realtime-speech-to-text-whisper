"""
Example Chat Agent with Speech Integration

This demonstrates how to integrate STT and TTS into a chat-based agent.
"""

import sys
from pathlib import Path
import time
import threading

# Add parent directory to path to import speech_agent_integration
sys.path.insert(0, str(Path(__file__).parent.parent))

from speech_agent_integration import SpeechEnabledAgent


class SimpleChatAgent:
    """Example chat agent with speech capabilities."""
    
    def __init__(self):
        self.conversation_history = []
        
        # Initialize speech-enabled agent
        self.speech_agent = SpeechEnabledAgent(stt_service_type="auto")
        
        # Set up transcription handler
        self.speech_agent.set_transcription_handler(self.process_user_input)
        
        print("Chat agent initialized with speech capabilities!")
    
    def process_user_input(self, user_input: str) -> str:
        """
        Process user input and return agent response.
        
        Args:
            user_input: Transcribed text from user speech
            
        Returns:
            Agent response text (will be spoken via TTS)
        """
        print(f"User said: '{user_input}'")
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Simple response logic (replace with your actual agent logic)
        response = self.generate_response(user_input)
        
        # Add response to history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        print(f"Agent responds: '{response}'")
        return response
    
    def generate_response(self, user_input: str) -> str:
        """
        Generate agent response (replace with your actual agent logic).
        
        This is where you'd integrate with:
        - OpenAI API
        - Local LLM (ollama, etc.)
        - Rule-based responses
        - RAG system
        - etc.
        """
        user_input_lower = user_input.lower()
        
        # Simple keyword-based responses (replace with your agent)
        if "hello" in user_input_lower or "hi" in user_input_lower:
            return "Hello! How can I help you today?"
        
        elif "weather" in user_input_lower:
            return "I don't have access to current weather data, but it's always nice to talk about the weather!"
        
        elif "time" in user_input_lower:
            current_time = time.strftime("%I:%M %p")
            return f"The current time is {current_time}"
        
        elif "bye" in user_input_lower or "goodbye" in user_input_lower:
            return "Goodbye! It was nice talking with you."
        
        elif "stop" in user_input_lower or "quit" in user_input_lower:
            return "Stopping the conversation. Goodbye!"
        
        else:
            return f"I heard you say '{user_input}'. That's interesting! Tell me more."
    
    def start_conversation(self):
        """Start the speech-enabled conversation."""
        print("Starting speech-enabled chat agent...")
        print("Say 'stop' or 'quit' to end the conversation.")
        
        # Start listening for speech
        if not self.speech_agent.start_listening():
            print("Failed to start speech services")
            return
        
        # Initial greeting
        self.speech_agent.speak("Hello! I'm your speech-enabled chat agent. How can I help you today?")
        
        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
                
                # Check if user said stop/quit
                if self.conversation_history:
                    last_message = self.conversation_history[-2:]  # Get last user message
                    if len(last_message) >= 1:
                        last_user_input = last_message[0].get("content", "").lower()
                        if "stop" in last_user_input or "quit" in last_user_input:
                            print("Conversation ended by user")
                            break
        
        except KeyboardInterrupt:
            print("\nConversation interrupted by user")
        
        finally:
            self.speech_agent.stop_listening()
            print("Chat agent stopped")
    
    def text_mode(self):
        """Run in text-only mode for testing."""
        print("Running in text-only mode (no speech)")
        print("Type 'quit' to exit")
        
        self.speech_agent.speak("Hello! I'm running in text mode. Type your messages.")
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    response = "Goodbye!"
                    print(f"Agent: {response}")
                    self.speech_agent.speak(response)
                    break
                
                response = self.process_user_input(user_input)
                print(f"Agent: {response}")
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break


def main():
    """Main function to run the chat agent."""
    agent = SimpleChatAgent()
    
    print("Choose mode:")
    print("1. Speech mode (STT + TTS)")
    print("2. Text mode (TTS only)")
    
    try:
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == "1":
            agent.start_conversation()
        elif choice == "2":
            agent.text_mode()
        else:
            print("Invalid choice")
    
    except KeyboardInterrupt:
        print("\nExiting...")


if __name__ == "__main__":
    main()
