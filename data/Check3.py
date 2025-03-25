from pymongo import MongoClient
from transformers import pipeline
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("email_sorting_log.log"),
        logging.StreamHandler()
    ]
)

# Load DistilBERT model pipeline
logging.info("Loading DistilBERT model pipeline for semantic classification...")
classifier = pipeline("zero-shot-classification", model="distilbert-base-uncased")
logging.info("Model pipeline loaded successfully.")

# MongoDB connection setup
logging.info("Connecting to MongoDB...")
client = MongoClient('mongodb://localhost:27017/')  # Update the URI as per your MongoDB setup
db = client['emailsdata']  # Replace with your database name
collection = db['rawEmails']  # Replace with your collection name
logging.info("Connected to MongoDB.")

# Define candidate labels
candidate_labels = ["update", "request"]

def classify_and_update_emails():
    """
    Fetch emails from MongoDB, classify them, and update their records with categories.
    """
    try:
        # Fetch all emails from the collection
        emails = collection.find()
        for email in emails:
            email_id = email["_id"]
            text_to_analyze = f"{email.get('subject', '')} {email.get('body', '')}".strip()
            logging.info(f"Classifying email ID {email_id}: {text_to_analyze}")

            # Perform classification
            results = classifier(text_to_analyze, candidate_labels=candidate_labels, multi_label=True)
            logging.info(f"Classification results for email ID {email_id}: {results}")

            # Assign the label with the highest score
            best_label = results["labels"][0]

            # Update the email record with the assigned category
            collection.update_one(
                {"_id": email_id},
                {"$set": {"category": best_label}}
            )
            logging.info(f"Updated email ID {email_id} with category: {best_label}")

        logging.info("Email classification and updates completed successfully.")

    except Exception as e:
        logging.error(f"An error occurred during email classification: {e}", exc_info=True)

if __name__ == "__main__":
    classify_and_update_emails()