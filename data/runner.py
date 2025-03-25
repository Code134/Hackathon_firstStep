import torch
from pymongo import MongoClient
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Load your fine-tuned model and tokenizer from the saved directory.
model_path = "email_classifier_llm"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)

def classify_email(email_text, max_length=128):
    """
    Tokenizes the input text, performs inference using the model,
    and returns the predicted label.
    """
    inputs = tokenizer(
        email_text,
        return_tensors="pt",
        truncation=True,
        padding="max_length",
        max_length=max_length
    )
    
    with torch.no_grad():
        outputs = model(**inputs)
    
    logits = outputs.logits
    predicted_class_id = logits.argmax(dim=1).item()
    
    # Map model output to a label.
    label_mapping = {0: "duplicate", 1: "update", 2: "request"}
    return label_mapping[predicted_class_id]

# Connect to MongoDB.
client = MongoClient("mongodb://localhost:27017")
db = client["emailsdata"]
collection = db["backup_rawEmails"]

# Iterate over each email document.
for doc in collection.find():
    subject = doc.get("subject", "")
    body = doc.get("body", "")
    # Combine subject and body to create the text input.
    email_text = f"{subject} {body}"
    
    # Classify the email.
    predicted_label = classify_email(email_text)
    
    # Update the document with the predicted label.
    collection.update_one(
        {"_id": doc["_id"]},
        {"$set": {"predicted_label": predicted_label}}
    )
    
    print(f"Updated document {doc['_id']} with predicted label: {predicted_label}")

print("Document classification and update process completed.")