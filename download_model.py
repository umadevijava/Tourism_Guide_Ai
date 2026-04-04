#!/usr/bin/env python
"""Download the required LLM model."""

import os
from pathlib import Path
import requests
from tqdm import tqdm

def download_model():
    """Download the Llama 3.2 1B model from Hugging Face."""
    
    model_url = "https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q5_K_M.gguf"
    model_name = "Llama-3.2-1B-Instruct-Q5_K_M.gguf"
    
    # Get the models directory
    models_dir = Path(__file__).parent / "models"
    models_dir.mkdir(exist_ok=True)
    
    model_path = models_dir / model_name
    
    # Check if model already exists
    if model_path.exists():
        print(f"✓ Model already exists at: {model_path}")
        return
    
    print(f"📥 Downloading {model_name} from Hugging Face...")
    print(f"   URL: {model_url}")
    print(f"   Size: ~3-4 GB (this may take a few minutes)")
    print()
    
    try:
        response = requests.get(model_url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Get total file size
        total_size = int(response.headers.get('content-length', 0))
        
        # Download with progress bar
        with open(model_path, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=model_name) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        
        print()
        print(f"✓ Model downloaded successfully!")
        print(f"  Location: {model_path}")
        print(f"  Size: {model_path.stat().st_size / (1024**3):.2f} GB")
        
    except Exception as e:
        print(f"✗ Download failed: {e}")
        if model_path.exists():
            model_path.unlink()
        raise

if __name__ == "__main__":
    download_model()
