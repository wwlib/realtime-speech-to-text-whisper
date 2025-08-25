#!/usr/bin/env python3
"""
Script to download Piper TTS models for speech synthesis.
Downloads a high-quality English voice model.
"""

import os
import urllib.request
import sys
from pathlib import Path

# Model information
MODELS = {
    "en_US-lessac-medium": {
        "model_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
        "description": "High-quality US English voice (Lessac)"
    },
    "en_US-amy-medium": {
        "model_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx.json",
        "description": "Clear US English voice (Amy)"
    },
    "en_US-ryan-high": {
        "model_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/high/en_US-ryan-high.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/high/en_US-ryan-high.onnx.json",
        "description": "High-quality male US English voice (Ryan)"
    }
}

def download_file(url, filepath):
    """Download a file with progress indication."""
    print(f"Downloading {os.path.basename(filepath)}...")
    
    def progress_hook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100, (downloaded * 100) // total_size)
            sys.stdout.write(f"\r  Progress: {percent}% ({downloaded // 1024 // 1024} MB)")
            sys.stdout.flush()
    
    try:
        urllib.request.urlretrieve(url, filepath, progress_hook)
        print()  # New line after progress
        print(f"  ✓ Downloaded: {filepath}")
        return True
    except Exception as e:
        print(f"\n  ✗ Error downloading {filepath}: {e}")
        return False

def download_model(model_name, model_info, models_dir):
    """Download a specific model and its config."""
    print(f"\n--- Downloading {model_name} ---")
    print(f"Description: {model_info['description']}")
    
    model_file = os.path.join(models_dir, f"{model_name}.onnx")
    config_file = os.path.join(models_dir, f"{model_name}.onnx.json")
    
    success = True
    
    # Download model file
    if not os.path.exists(model_file):
        success &= download_file(model_info['model_url'], model_file)
    else:
        print(f"  ✓ Model file already exists: {model_file}")
    
    # Download config file
    if not os.path.exists(config_file):
        success &= download_file(model_info['config_url'], config_file)
    else:
        print(f"  ✓ Config file already exists: {config_file}")
    
    return success

def main():
    """Main function to download Piper TTS models."""
    print("Piper TTS Model Downloader")
    print("=" * 40)
    
    # Create models directory
    models_dir = "models"
    os.makedirs(models_dir, exist_ok=True)
    print(f"Models directory: {os.path.abspath(models_dir)}")
    
    # Show available models
    print("\nAvailable models:")
    for i, (name, info) in enumerate(MODELS.items(), 1):
        print(f"  {i}. {name} - {info['description']}")
    
    # Get user choice
    while True:
        try:
            choice = input(f"\nSelect model to download (1-{len(MODELS)}, 'all' for all models, 'q' to quit): ").strip().lower()
            
            if choice == 'q':
                print("Exiting...")
                return
            elif choice == 'all':
                # Download all models
                success_count = 0
                for model_name, model_info in MODELS.items():
                    if download_model(model_name, model_info, models_dir):
                        success_count += 1
                
                print(f"\n{'='*40}")
                print(f"Downloaded {success_count}/{len(MODELS)} models successfully")
                if success_count > 0:
                    print(f"Models saved to: {os.path.abspath(models_dir)}")
                break
            else:
                choice_num = int(choice)
                if 1 <= choice_num <= len(MODELS):
                    model_name = list(MODELS.keys())[choice_num - 1]
                    model_info = MODELS[model_name]
                    
                    if download_model(model_name, model_info, models_dir):
                        print(f"\n{'='*40}")
                        print(f"✓ Successfully downloaded {model_name}")
                        print(f"Model files saved to: {os.path.abspath(models_dir)}")
                        
                        # Update tts_service.py if using default model
                        if model_name == "en_US-lessac-medium":
                            print("\nThis is the default model configured in tts_service.py")
                        else:
                            print(f"\nTo use this model, update tts_service.py:")
                            print(f"  self.model_path = os.path.join(self.models_dir, \"{model_name}.onnx\")")
                            print(f"  self.config_path = os.path.join(self.models_dir, \"{model_name}.onnx.json\")")
                    break
                else:
                    print("Invalid choice. Please try again.")
        except ValueError:
            print("Invalid choice. Please enter a number, 'all', or 'q'.")
        except KeyboardInterrupt:
            print("\nExiting...")
            return

if __name__ == "__main__":
    main()
