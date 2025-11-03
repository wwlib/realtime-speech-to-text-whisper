from abc import ABC, abstractmethod
import threading


class BaseTranscriptionService(ABC):
    """Abstract base class for all transcription services"""
    
    def __init__(self, manager):
        self.manager = manager
        self.stop_event = threading.Event()
    
    @abstractmethod
    def run(self, loop):
        """Main transcription loop - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def stop(self):
        """Stop the service gracefully - must be implemented by subclasses"""
        pass
