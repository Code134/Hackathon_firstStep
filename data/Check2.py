import os
import logging
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("model_loading_log.log"),
        logging.StreamHandler()
    ]
)

# Local paths
model_paths = {
    "bart": r"E:\hackathon_25\models\facebook--bart-large-mnli",
    "distilbert": r"E:\hackathon_25\models\distilbert-base-uncased"
}

def load_local_models():
    """
    Load models from local directories.
    """
    try:
        logging.info("Attempting to load models from local paths...")

        # Load BART tokenizer and model
        logging.info(f"Loading BART model from {model_paths['bart']}...")
        tokenizer_bart = AutoTokenizer.from_pretrained(model_paths["bart"], local_files_only=True)
        model_bart = AutoModelForSequenceClassification.from_pretrained(model_paths["bart"], local_files_only=True)
        logging.info("BART model loaded successfully.")

        # Load DistilBERT tokenizer and model
        logging.info(f"Loading DistilBERT model from {model_paths['distilbert']}...")
        tokenizer_distilbert = AutoTokenizer.from_pretrained(model_paths["distilbert"], local_files_only=True)
        model_distilbert = AutoModelForSequenceClassification.from_pretrained(model_paths["distilbert"], local_files_only=True)
        logging.info("DistilBERT model loaded successfully.")

        return tokenizer_bart, model_bart, tokenizer_distilbert, model_distilbert

    except Exception as e:
        logging.error(f"Error loading models: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    load_local_models()