from .transcription_service import TranscriptionService
from .coreml_transcription_service import CoreMLTranscriptionService
from .platform_detector import get_recommended_stt_service


def create_stt_service(manager, service_type=None):
    """Create appropriate STT service based on platform or explicit choice
    
    Args:
        manager: ConnectionManager instance
        service_type: "faster_whisper", "coreml", or None for auto-detect
    
    Returns:
        BaseTranscriptionService instance
    """
    if service_type is None:
        service_type = get_recommended_stt_service()
    
    print(f"Creating STT service: {service_type}")
    
    if service_type == "coreml":
        try:
            return CoreMLTranscriptionService(manager)
        except ImportError as e:
            print(f"CoreML not available ({e}), falling back to faster-whisper")
            return TranscriptionService(manager)
        except Exception as e:
            print(f"Error creating CoreML service ({e}), falling back to faster-whisper")
            return TranscriptionService(manager)
    else:
        return TranscriptionService(manager)
