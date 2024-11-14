import logging
import datetime
import pymongo
import os

from dotenv import load_dotenv
load_dotenv()

# MongoDB Setup
db_client = pymongo.MongoClient(os.environ.get("MONGODB_URL"))
db = db_client["cricket"]
match_list_collection = db["match_list"]
match_details_collection = db["match_details"]
scorecard_collection = db["scorecard"]
live_page_collection = db["live_page"]

from datetime import datetime

def save_to_db(collection, data, unique_field):
    print("Starting to save data...")
    is_empty_collection = collection.count_documents({}) == 0

    if isinstance(data, list):
        if not data:
            print("Provided data is an empty list.")
            return
        documents_to_insert = []
        for document in data:
            if is_empty_collection or not collection.find_one({unique_field: document.get(unique_field)}):
                documents_to_insert.append(document)
            else:
                print(f"Duplicate document found for {document.get(unique_field)}. Skipping insertion.")
        if documents_to_insert:
            try:
                collection.insert_many(documents_to_insert)
                print(f"Inserted {len(documents_to_insert)} documents into {collection.name} at {datetime.now()}.")
            except Exception as e:
                print(f"Error inserting documents: {e}")

    elif isinstance(data, dict):
        if is_empty_collection or not collection.find_one({unique_field: data.get(unique_field)}):
            try:
                collection.insert_one(data)
                print(f"Data saved to {collection.name} at {datetime.now()}.")
            except Exception as e:
                print(f"Error inserting single document: {e}")
        else:
            print(f"Duplicate document found for {data.get(unique_field)}. Skipping insertion.")
    else:
        print(f"Unsupported data type: {type(data)}. Only dict and list are supported.")
    print("Data saving operation finished.")

def safe_text(element):
    return element.text.strip() if element else None

# Configure logger
def setup_logger():
    logger = logging.getLogger("ScraperLogger")
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler('scraper.log')
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO) 

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()
