"""
Helper script to download the model if it doesn't exist.
Used in Streamlit Cloud or when model is stored externally.
"""
import os
import urllib.request
from pathlib import Path

def download_model(url: str, output_path: str = "artifacts/bacteria_classifier.pt"):
    """Download model from URL if it doesn't exist locally."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if output_path.exists():
        print(f"Model already exists at {output_path}, skipping download.")
        return
    
    print(f"Downloading model from {url}...")
    try:
        urllib.request.urlretrieve(url, str(output_path))
        print(f"Model downloaded successfully to {output_path}")
    except Exception as e:
        print(f"Error downloading model: {e}")
        raise

if __name__ == "__main__":
    # Example: download from GitHub Releases
    # Replace with actual URL after uploading to Releases
    MODEL_URL = os.getenv("MODEL_URL", "")
    if MODEL_URL:
        download_model(MODEL_URL)
    else:
        print("MODEL_URL environment variable not set. Skipping download.")
