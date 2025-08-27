import platform
import subprocess


def is_apple_silicon():
    """Detect if running on Apple Silicon Mac"""
    if platform.system() != "Darwin":
        return False
    try:
        result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], 
                              capture_output=True, text=True)
        return "Apple" in result.stdout
    except:
        return False


def get_recommended_stt_service():
    """Return the recommended STT service for this platform"""
    if is_apple_silicon():
        return "coreml"
    else:
        return "faster_whisper"
