from pymongo import MongoClient
from transformers import pipeline
import logging
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("data_generation_and_processing_log.log"),
        logging.StreamHandler()
    ]
)

# MongoDB connection setup
logging.info("Connecting to MongoDB...")
client = MongoClient('mongodb://localhost:27017/')  # Adjust MongoDB URI as needed
db = client['emailsdata']  # Replace with your database name
raw_collection = db['rawEmails']
training_collection = db['trainingEmails']
testing_collection = db['testingEmails']
logging.info("Connected to MongoDB.")

# Load DistilBERT model pipeline
logging.info("Loading DistilBERT model pipeline for semantic classification...")
classifier = pipeline("zero-shot-classification", model="distilbert-base-uncased")
logging.info("Model pipeline loaded successfully.")

# Define candidate labels for classification
candidate_labels = ["update", "request"]

# Categories of email content
def generate_email_content(email_type):
    """
    Generate synthetic email content for training and testing datasets.
    """
    update_text = [
        "Can you update me on the status of my application?",
        "Please let me know if there are any updates regarding my leave request.",
        "I need updates on the progress of my previous task submission.",
        "Kindly share the current status of my pending work items."
    ]
    new_request_text = [
        "I would like to apply for a new process initiation.",
        "Please approve my vacation request for the coming month.",
        "Can you initiate the document verification for my new project?",
        "This is a formal request for project extension approval."
    ]
    combined_text = [
        "Can you update me on the previous task and also approve my new project request?",
        "I need updates on my application status and please process my travel request.",
        "Kindly confirm the progress on prior assignments and also start the new task I mentioned."
    ]
    multiple_requests_text = [
        "Please provide an update on my application, and also approve my leave. In addition, I need feedback on my latest submission.",
        "Can you update the status on my project, schedule a meeting, and allocate resources for the new project I mentioned?",
        "Let me know about the previous progress, plus I need help with the procurement process and a new leave application."
    ]

    if email_type == "update":
        return random.choice(update_text)
    elif email_type == "request":
        return random.choice(new_request_text)
    elif email_type == "combined":
        return random.choice(combined_text)
    elif email_type == "multiple":
        return random.choice(multiple_requests_text)

def analyze_attachments(email):
    """
    Analyze email attachments and compute their data.
    """
    attachments = email.get("attachments", [])
    total_attachment_size = sum(att.get("size", 0) for att in attachments)  # Assume size is in bytes
    num_images = sum(1 for att in attachments if att.get("type") == "image")
    return total_attachment_size, num_images

def classify_and_process_emails():
    """
    Classify emails from MongoDB, process attachments, and update records with categories and attachment analysis.
    """
    try:
        emails = raw_collection.find()
        for email in emails:
            email_id = email["_id"]
            subject = email.get("subject", "")
            body = email.get("body", "")
            text_to_analyze = f"{subject} {body}".strip()
            logging.info(f"Processing email ID {email_id}...")

            # Classify email
            results = classifier(text_to_analyze, candidate_labels=candidate_labels, multi_label=True)
            best_label = results["labels"][0]
            logging.info(f"Classification for email ID {email_id}: {best_label}")

            # Analyze attachments
            total_size, num_images = analyze_attachments(email)
            logging.info(f"Attachment analysis for email ID {email_id}: {total_size} bytes, {num_images} images")

            # Update email record in the database
            raw_collection.update_one(
                {"_id": email_id},
                {
                    "$set": {
                        "category": best_label,
                        "attachment_size": total_size,
                        "num_images": num_images
                    }
                }
            )
            logging.info(f"Updated email ID {email_id} with category, attachment size, and image count.")

        logging.info("Email classification and processing completed successfully.")

    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)

def generate_training_and_testing_data():
    """
    Generate training and testing datasets and insert them into MongoDB without deleting old data.
    """
    try:
        # Generate training data
        logging.info("Generating training data...")
        training_emails = []
        for _ in range(200):
            email_type = random.choices(
                ["update", "request", "combined", "multiple"],
                weights=[0.4, 0.4, 0.1, 0.1]
            )[0]
            subject = f"Training Email: {email_type.capitalize()}"
            body = generate_email_content(email_type)
            training_emails.append({"subject": subject, "body": body, "type": email_type})
        training_collection.insert_many(training_emails)
        logging.info("Training data generation completed.")

        # Generate testing data
        logging.info("Generating testing data...")
        testing_emails = []
        for _ in range(1000):
            email_type = random.choices(
                ["update", "request", "combined", "multiple"],
                weights=[0.5, 0.3, 0.1, 0.1]
            )[0]
            subject = f"Testing Email: {email_type.capitalize()}"
            body = generate_email_content(email_type)
            testing_emails.append({"subject": subject, "body": body, "type": email_type})
        testing_collection.insert_many(testing_emails)
        logging.info("Testing data generation completed.")

    except Exception as e:
        logging.error(f"An error occurred during data generation: {e}", exc_info=True)

if __name__ == "__main__":
    # Classify and process existing emails
    classify_and_process_emails()

    # Generate synthetic training and testing data
    generate_training_and_testing_data()