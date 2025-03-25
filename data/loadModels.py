import os
from transformers import AutoModel, AutoTokenizer

def download_models():
    # Define models to download
    models_to_download = [
        "distilbert-base-uncased",
        "facebook/bart-large-mnli"
    ]

    # Get the current script directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Define the parallel 'models' directory path
    models_dir = os.path.join(current_dir, "../models")

    # Resolve absolute path and create the 'models' directory if it doesn't exist
    models_dir = os.path.abspath(models_dir)
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        print(f"Created directory: {models_dir}")
    else:
        print(f"Directory already exists: {models_dir}")

    # Download and save each model
    for model_name in models_to_download:
        print(f"Downloading model '{model_name}' into '{models_dir}'...")
        AutoModel.from_pretrained(model_name, cache_dir=models_dir)
        AutoTokenizer.from_pretrained(model_name, cache_dir=models_dir)
        print(f"Model '{model_name}' downloaded and saved locally.")

if __name__ == "__main__":
    download_models()