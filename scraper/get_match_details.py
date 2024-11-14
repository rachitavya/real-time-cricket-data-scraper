import pymongo
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from scraper import Scraper

from scraper.utils import (
    match_details_collection,
    match_list_collection,
)

MANDATORY_FIELDS = ["team_1_name", "team_2_name", "match_date"]

def has_missing_mandatory_fields(match_details):
    return any(not match_details.get(field) for field in MANDATORY_FIELDS)

def is_details_changed(existing_details, new_details):
    for field in MANDATORY_FIELDS:
        existing_value = existing_details.get(field, "")
        new_value = new_details.get(field, "")
        
        # Ensure we only strip valid strings, not None
        if existing_value and new_value:
            if existing_value.strip() != new_value.strip():
                return True
        elif existing_value != new_value:
            return True
    
    return False


def save_match_details_to_db(match_id, match_details):
    match_details["match_id"] = match_id 
    match_details["scraped_at"] = datetime.now()

    result = match_details_collection.insert_one(match_details)
    if result.acknowledged:
        print(f"Match details saved to match_details collection with ID {result.inserted_id}")
    else:
        print(f"Failed to save match details for match ID {match_id}")

def get_all_match_details():
    scraper = Scraper()
    match_list = match_list_collection.find()  

    for match in match_list:
        match_id = match["_id"]
        match_link = match["link"]
        team_1_name = match["team1"]["name"]
        team_2_name = match["team2"]["name"]
        print(f"Processing match {match_id} with link {match_link}")
        existing_match_details = match_details_collection.find_one({"match_id": match_id})

        if existing_match_details:
            print(f"Match {match_id} details already exist.")
            if has_missing_mandatory_fields(existing_match_details):
                print(f"Missing mandatory fields for match {match_id}. Scraping new details...")
                new_details = scraper.scrape_match_details(match_link)
                if new_details:
                    if is_details_changed(existing_match_details, new_details):
                        result = match_details_collection.update_one(
                            {"match_id": match_id},
                            {"$set": new_details}
                        )
                        if result.modified_count > 0:
                            print(f"Updated match details for match {match_id}")
                        else:
                            print(f"No changes detected for match {match_id}, skipping update.")
                    else:
                        print(f"No changes in details for match {match_id}. Skipping update.")
                else:
                    print(f"Failed to scrape new details for match {match_id}")
        else:
            print(f"Match {match_id} details do not exist. Scraping new details...")
            
            new_details = scraper.scrape_match_details(match_link)
            
            if new_details:
                new_details["team_1_name"]=team_1_name      # This is being done to prevent loss
                new_details["team_2_name"]=team_2_name      # of team name when match goes live.
                new_details["match_link"]= match_link
                save_match_details_to_db(match_id, new_details)
            else:
                print(f"Failed to scrape details for match {match_id}")

    scraper.close()

# Run the function
if __name__ == "__main__":
    get_all_match_details()
