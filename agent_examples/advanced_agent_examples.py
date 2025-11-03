"""
Advanced Chat Agent Integration Examples

This shows how to integrate STT/TTS with various popular chat frameworks.
"""

import sys
from pathlib import Path
import asyncio
import threading
import time
from typing import Optional, List, Dict, Any

# Add parent directory to path to import speech_agent_integration
sys.path.insert(0, str(Path(__file__).parent.parent))

from speech_agent_integration import SpeechEnabledAgent


class OpenAISpeechAgent:
    """Example integration with OpenAI API."""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        self.conversation_history = []
        
        # Initialize speech
        self.speech_agent = SpeechEnabledAgent()
        self.speech_agent.set_transcription_handler(self.process_with_openai)
        
        # Try to import OpenAI
        try:
            import openai
            self.openai_client = openai.OpenAI(api_key=api_key)
        except ImportError:
            print("OpenAI package not installed. Run: pip install openai")
            self.openai_client = None
    
    def process_with_openai(self, user_input: str) -> str:
        """Process user input with OpenAI API."""
        if not self.openai_client:
            return "OpenAI not available. Please install openai package."
        
        try:
            # Add user message to history
            self.conversation_history.append({"role": "user", "content": user_input})
            
            # Get response from OpenAI
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                max_tokens=150,
                temperature=0.7
            )
            
            assistant_response = response.choices[0].message.content
            
            # Add to history
            self.conversation_history.append({"role": "assistant", "content": assistant_response})
            
            # Keep conversation history manageable
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            return assistant_response
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return "Sorry, I encountered an error processing your request."
    
    def start(self):
        """Start the OpenAI speech agent."""
        self.speech_agent.start_listening()
        self.speech_agent.speak("Hello! I'm powered by OpenAI. How can I help you?")


class OllamaSpeechAgent:
    """Example integration with Ollama (local LLM)."""
    
    def __init__(self, model: str = "gemma3", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.conversation_history = []
        
        # Initialize speech
        self.speech_agent = SpeechEnabledAgent()
        self.speech_agent.set_transcription_handler(self.process_with_ollama)
    
    def process_with_ollama(self, user_input: str) -> str:
        """Process user input with Ollama."""
        try:
            import requests
            
            # Build conversation context
            context = "\n".join([
                f"User: {msg['content']}" if msg['role'] == 'user' else f"Assistant: {msg['content']}"
                for msg in self.conversation_history[-10:]  # Last 10 messages
            ])
            
            prompt = f"{context}\nUser: {user_input}\nAssistant:"
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 100
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_response = result.get("response", "").strip()
                
                # Update conversation history
                self.conversation_history.append({"role": "user", "content": user_input})
                self.conversation_history.append({"role": "assistant", "content": assistant_response})
                
                return assistant_response
            else:
                return "Sorry, I couldn't process your request right now."
                
        except Exception as e:
            print(f"Ollama API error: {e}")
            return "Sorry, I encountered an error. Is Ollama running?"
    
    def start(self):
        """Start the Ollama speech agent."""
        self.speech_agent.start_listening()
        self.speech_agent.speak("Hello! I'm powered by Ollama. How can I help you?")


class RAGSpeechAgent:
    """Example integration with RAG (Retrieval Augmented Generation)."""
    
    def __init__(self, knowledge_base: List[str]):
        self.knowledge_base = knowledge_base
        self.conversation_history = []
        
        # Initialize speech
        self.speech_agent = SpeechEnabledAgent()
        self.speech_agent.set_transcription_handler(self.process_with_rag)
        
        # Simple keyword-based retrieval (replace with proper vector search)
        self.build_simple_index()
    
    def build_simple_index(self):
        """Build a simple keyword index (replace with vector embeddings)."""
        self.keyword_index = {}
        
        for i, doc in enumerate(self.knowledge_base):
            words = doc.lower().split()
            for word in words:
                if word not in self.keyword_index:
                    self.keyword_index[word] = []
                self.keyword_index[word].append(i)
    
    def retrieve_relevant_docs(self, query: str, top_k: int = 3) -> List[str]:
        """Retrieve relevant documents (simple keyword matching)."""
        query_words = query.lower().split()
        doc_scores = {}
        
        for word in query_words:
            if word in self.keyword_index:
                for doc_idx in self.keyword_index[word]:
                    doc_scores[doc_idx] = doc_scores.get(doc_idx, 0) + 1
        
        # Sort by score and return top_k
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        return [self.knowledge_base[doc_idx] for doc_idx, _ in sorted_docs[:top_k]]
    
    def process_with_rag(self, user_input: str) -> str:
        """Process user input with RAG."""
        try:
            # Retrieve relevant documents
            relevant_docs = self.retrieve_relevant_docs(user_input)
            
            if relevant_docs:
                # Simple response generation (replace with LLM)
                context = "\n".join(relevant_docs)
                response = f"Based on my knowledge: {relevant_docs[0][:200]}..."
            else:
                response = "I don't have specific information about that topic."
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": response})
            
            return response
            
        except Exception as e:
            print(f"RAG processing error: {e}")
            return "Sorry, I encountered an error processing your request."
    
    def start(self):
        """Start the RAG speech agent."""
        self.speech_agent.start_listening()
        self.speech_agent.speak("Hello! I can answer questions based on my knowledge base.")


class AsyncSpeechAgent:
    """Example of async integration for frameworks like FastAPI."""
    
    def __init__(self):
        self.conversation_history = []
        self.speech_agent = SpeechEnabledAgent()
        self.response_queue = asyncio.Queue()
        
        # Set up async transcription handler
        self.speech_agent.set_transcription_handler(self.handle_transcription)
    
    def handle_transcription(self, user_input: str):
        """Handle transcription in sync context, queue for async processing."""
        # Put transcription in async queue
        try:
            loop = asyncio.get_event_loop()
            loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self.process_async(user_input))
            )
        except RuntimeError:
            # If no event loop, create one
            asyncio.run(self.process_async(user_input))
    
    async def process_async(self, user_input: str) -> str:
        """Process user input asynchronously."""
        try:
            # Simulate async processing (database lookup, API call, etc.)
            await asyncio.sleep(0.1)  # Simulate async work
            
            # Generate response
            response = f"I heard you say: '{user_input}'. Processing asynchronously!"
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": response})
            
            # Speak the response
            self.speech_agent.speak(response)
            
            return response
            
        except Exception as e:
            print(f"Async processing error: {e}")
            error_response = "Sorry, I encountered an error processing your request."
            self.speech_agent.speak(error_response)
            return error_response
    
    async def start_async(self):
        """Start the async speech agent."""
        self.speech_agent.start_listening()
        self.speech_agent.speak("Hello! I'm running in async mode.")
        
        # Keep the async loop running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.speech_agent.stop_listening()


# Example usage functions
def demo_openai_agent():
    """Demo OpenAI integration."""
    api_key = input("Enter your OpenAI API key: ").strip()
    if api_key:
        agent = OpenAISpeechAgent(api_key)
        agent.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            agent.speech_agent.stop_listening()


def demo_ollama_agent():
    """Demo Ollama integration."""
    model = input("Enter Ollama model name (default: gemma3): ").strip() or "gemma3"
    agent = OllamaSpeechAgent(model)
    agent.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        agent.speech_agent.stop_listening()


def demo_rag_agent():
    """Demo RAG integration."""
    # Sample knowledge base
    knowledge_base = [
        "Python is a high-level programming language known for its simplicity and readability.",
        "Machine learning is a subset of artificial intelligence that enables computers to learn without explicit programming.",
        "Natural language processing helps computers understand and generate human language.",
        "Speech recognition converts spoken words into text using acoustic models and language models.",
        "Text-to-speech synthesis converts written text into spoken words using voice models."
    ]
    
    agent = RAGSpeechAgent(knowledge_base)
    agent.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        agent.speech_agent.stop_listening()


async def demo_async_agent():
    """Demo async integration."""
    agent = AsyncSpeechAgent()
    await agent.start_async()


if __name__ == "__main__":
    print("Advanced Speech Agent Integration Examples")
    print("1. OpenAI Agent")
    print("2. Ollama Agent") 
    print("3. RAG Agent")
    print("4. Async Agent")
    
    choice = input("Choose demo (1-4): ").strip()
    
    if choice == "1":
        demo_openai_agent()
    elif choice == "2":
        demo_ollama_agent()
    elif choice == "3":
        demo_rag_agent()
    elif choice == "4":
        asyncio.run(demo_async_agent())
    else:
        print("Invalid choice")
