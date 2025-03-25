import pymongo
from pymongo import MongoClient
import os

# For reproducibility.
import random
import numpy as np
import torch

random.seed(42)
np.random.seed(42)
torch.manual_seed(42)

# Connect to MongoDB.
client = MongoClient("mongodb://localhost:27017")
db = client["email_processing"]
collection = db["emails"]

# Retrieve all emails
emails = list(collection.find({}))

# Map our classification labels to integers.
label_mapping = {"duplicate": 0, "update": 1, "request": 2}

texts = []
labels = []

# Process each email.
for email in emails:
    if email.get("is_duplicate", False):
        label_name = "duplicate"
    elif email.get("is_update_case", False):
        label_name = "update"
    else:
        label_name = "request"
    
    # Combine subject and body for the text feature.
    text = f"{email.get('subject', '')} {email.get('body', '')}"
    texts.append(text)
    labels.append(label_mapping[label_name])

# Prepare a data dictionary.
data_dict = {
    "text": texts,
    "label": labels
}

# Use the Hugging Face Datasets library.
from datasets import Dataset

dataset = Dataset.from_dict(data_dict)
dataset = dataset.train_test_split(test_size=0.2, seed=42)
train_dataset = dataset["train"]
eval_dataset = dataset["test"]

# Load a pre-trained tokenizer and model.
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer

model_name = "distilbert-base-uncased"  # Small yet robust; you can choose another model.
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Tokenize the text.
def tokenize_function(examples):
    return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=128)

train_dataset = train_dataset.map(tokenize_function, batched=True)
eval_dataset = eval_dataset.map(tokenize_function, batched=True)

# Set the format for PyTorch.
train_dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])
eval_dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])

# Load the model with a classification head.
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=len(label_mapping))

# Set up the training arguments.
training_args = TrainingArguments(
    output_dir="output_llm",
    evaluation_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=3,
    weight_decay=0.01,
    logging_dir="logs",
    logging_steps=10,
)

# Setup the Trainer.
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    tokenizer=tokenizer,
)

# Fine-tune the model.
trainer.train()

# Evaluate the model.
eval_results = trainer.evaluate()
print("Evaluation results:", eval_results)

# Optionally, save your fine-tuned model.
model.save_pretrained("email_classifier_llm")
tokenizer.save_pretrained("email_classifier_llm")