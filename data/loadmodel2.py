import os
from transformers import AutoModelForSequenceClassification, AutoTokenizer

def verify_and_download_model(model_name, base_dir):
    """
    Verify if required files are present in the directory. If not, download the model.
    """
    model_dir = os.path.join(base_dir, model_name.replace("/", "--"))  # Replace "/" with "--" for Windows compatibility
    required_files = ["config.json", "tokenizer.json", "pytorch_model.bin"]  # Typical required files

    # Check if the directory exists
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
        print(f"Created directory: {model_dir}")

    # Verify if all required files are present
    missing_files = [file for file in required_files if not os.path.exists(os.path.join(model_dir, file))]
    if missing_files:
        print(f"Missing files in '{model_dir}': {missing_files}. Downloading model...")
        AutoModelForSequenceClassification.from_pretrained(model_name, cache_dir=model_dir)
        AutoTokenizer.from_pretrained(model_name, cache_dir=model_dir)
        print(f"Model '{model_name}' downloaded successfully to '{model_dir}'.")
    else:
        print(f"All required files are present in '{model_dir}'. Skipping download.")

if __name__ == "__main__":
    # Define models and the base directory
    base_directory = r"E:\hackathon 25\models"
    models_to_verify = [
        "facebook/bart-large-mnli",
        "distilbert-base-uncased"
    ]

    # Verify and download each model if necessary
    for model_name in models_to_verify:
        verify_and_download_model(model_name, base_directory)