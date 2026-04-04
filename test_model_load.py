#!/usr/bin/env python
"""Debug script to test model loading."""

from pathlib import Path
from llama_cpp import Llama

model_path = Path("D:\\rag-chatbot-main (1)\\rag-chatbot-main\\models\\Llama-3.2-1B-Instruct-Q5_K_M.gguf")

print(f"Model path: {model_path}")
print(f"File exists: {model_path.exists()}")
if model_path.exists():
    print(f"File size: {model_path.stat().st_size / (1024**3):.2f} GB")

print("\n📥 Attempting to load model...")
print("This may take a minute...")

try:
    llm = Llama(
        model_path=str(model_path),
        n_ctx=4096,
        n_threads=8,
        n_gpu_layers=50,
        verbose=True
    )
    print("\n✓ Model loaded successfully!")
    
    # Test inference
    print("\n📝 Testing basic inference...")
    response = llm("Say 'Hello, World!' and nothing else.", max_tokens=20)
    print(f"Response: {response}")
    
except Exception as e:
    print(f"\n✗ Error loading model:")
    print(f"  Type: {type(e).__name__}")
    print(f"  Message: {e}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()
