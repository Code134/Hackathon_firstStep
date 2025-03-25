import os
from pymongo import MongoClient
from transformers import pipeline
from datetime import datetime
import logging
from collections import Counter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("ensemble_classification_log.log"),
        logging.StreamHandler()
    ]
)

# MongoDB connection setup
client = MongoClient('mongodb://localhost:27017/')
db = client['emailsdata']  # Database name
collection = db['rawEmails']  # Primary collection
backup_collection = db['backup_rawEmails']  # Backup collection

# Define local model directories (with fixed paths)
model_paths = {
    "bart": r"E:\hackathon_25\models\facebook--bart-large-mnli",
    "distilbert": r"E:\hackathon_25\models\distilbert-base-uncased"
}

# Load models explicitly from the local paths
logging.info("Loading ensemble models from local storage...")
model_pipelines = [
    pipeline("zero-shot-classification", model=model_paths["bart"], tokenizer=model_paths["bart"], local_files_only=True),
    pipeline("zero-shot-classification", model=model_paths["distilbert"], tokenizer=model_paths["distilbert"], local_files_only=True)
]
logging.info("Models loaded successfully from local storage.")

def classify_with_ensemble(text_to_classify, candidate_labels):
    """
    Classify using an ensemble of models and return aggregated results.
    """
    predictions = []
    for model in model_pipelines:
        results = model(
            text_to_classify,
            candidate_labels=candidate_labels,
            multi_label=True
        )
        predictions.append(results)

    # Combine predictions
    aggregated_scores = Counter()
    for result in predictions:
        for label, score in zip(result["labels"], result["scores"]):
            aggregated_scores[label] += score

    # Normalize scores and rank labels
    total_scores = sum(aggregated_scores.values())
    final_scores = {label: score / total_scores for label, score in aggregated_scores.items()}
    ranked_labels = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
    
    return ranked_labels

def classify_and_update_records():
    """
    Classify and update records using the ensemble of models.
    """
    try:
        logging.info("Backing up current state of documents...")
        # Create persistent backup collection if it doesn't exist
        if 'backup_rawEmails' not in db.list_collection_names():
            logging.info("Backup collection does not exist. Creating it...")
            db.create_collection('backup_rawEmails')
            logging.info("Backup collection created successfully.")

        # Perform a backup of all documents
        documents = collection.find()
        for document in documents:
            backup_collection.update_one(
                {'_id': document['_id']},
                {'$set': {**document, 'backup_timestamp': datetime.utcnow()}},
                upsert=True
            )
        logging.info("Backup completed.")

        logging.info("Starting document classification process...")
        documents = collection.find()
        for document in documents:
            logging.debug(f"Processing document ID: {document['_id']}")

            # Combine fields for classification
            text_to_classify = f"{document.get('subject', '')} {document.get('body', '')}".lower()
            logging.debug(f"Text for classification: {text_to_classify}")

            # Ensemble classification
            candidate_labels = ["update", "request"]
            aggregated_results = classify_with_ensemble(text_to_classify, candidate_labels)
            logging.info(f"Aggregated results for document ID {document['_id']}: {aggregated_results}")

            # Update document with aggregated results
            collection.update_one(
                {'_id': document['_id']},
                {'$set': {'aggregated_classification': aggregated_results}}
            )
        logging.info("Classification process completed successfully.")
    except Exception as e:
        logging.error(f"Error during classification: {e}")

def rollback_changes():
    """
    Roll back changes by restoring data from the backup collection.
    """
    try:
        logging.info("Restoring data from backup...")
        backups = backup_collection.find()
        for backup in backups:
            original_data = {key: value for key, value in backup.items() if key != '_id' and key != 'backup_timestamp'}
            collection.update_one(
                {'_id': backup['_id']},
                {'$set': original_data}
            )
        logging.info("All changes reverted successfully.")
    except Exception as e:
        logging.error(f"Error while reverting changes: {e}")

if __name__ == "__main__":
    user_action = input("Enter 'classify' to classify records or 'rollback' to revert changes: ").strip().lower()
    if user_action == 'classify':
        classify_and_update_records()
    elif user_action == 'rollback':
        rollback_changes()
    else:
        logging.warning("Invalid input. Exiting.")