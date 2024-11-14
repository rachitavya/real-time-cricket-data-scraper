from datetime import datetime, timedelta
import time
import json
import traceback
from concurrent.futures import ThreadPoolExecutor

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

from scraper import Scraper  
from scraper.get_match_details import get_all_match_details
from scraper.utils import (
    save_to_db,
    db_client,
    db,
    match_details_collection,
    match_list_collection,
    scorecard_collection,
    live_page_collection,
    logger
)
    
executor = ThreadPoolExecutor()
scheduler = BackgroundScheduler()

def schedule_jobs():
    global scheduler
    # Daily job to scrape match list
    scheduler.add_job(scrape_match_list, 'interval', days=1, start_date='2024-11-15 06:00:00')
    # Daily job to scrape match details
    scheduler.add_job(get_all_match_details, 'interval', days=1, start_date='2024-11-15 07:00:00')
    # Daily job to schedule timed jobs for today's matches
    scheduler.add_job(schedule_timed_jobs_for_today_matches, 'interval', days=1, start_date='2024-11-15 08:00:00')
    # scheduler.add_job(schedule_timed_jobs_for_today_matches, 'date', run_date= datetime.now() + timedelta(seconds=5))

    try:
        print("Scheduler started. Daily jobs are scheduled.")
        scheduler.start()
        while True:
            pass  
    except (KeyboardInterrupt, SystemExit):
        print("Shutting down scheduler.")
        scheduler.shutdown()

def schedule_timed_jobs_for_today_matches():
    """Schedule match-specific jobs for today's matches."""
    today = datetime.now().date()    
    upcoming_matches = match_details_collection.find({"match_date": {"$regex": today.strftime("%b %d, %Y")}})    
    for match in upcoming_matches:
        logger.info(match["match_date"])
        match_id = match["match_id"]
        match_start_time = datetime.strptime(match["match_date"], "%b %d, %Y, %I:%M:%S %p")
        match_link = match["match_link"]
        
        # Schedule job to update match details 20 minutes before match
        match_20_minutes_before = match_start_time - timedelta(minutes=20)
        scheduler.add_job(
            lambda m_id=match_id, m_link=match_link: executor.submit(scrape_match_details, m_id, m_link),
            'date', 
            run_date=match_20_minutes_before
        )

        # Start live page scraping job at match start time
        scheduler.add_job(
            lambda m_id=match_id, m_link=match_link: executor.submit(start_live_scraping, m_id, m_link),
            'date', 
            run_date=match_start_time
        )

def scrape_match_list():
    try:
        logger.info("Starting to scrape match list...")
        scraper = Scraper()
        match_list_data = scraper.scrape_match_list()
        save_to_db(match_list_collection, match_list_data, unique_field="link")
        logger.info("Match list scraping completed successfully.")
    except Exception as e:
        logger.error(f"Error occurred while scraping match list: {e}")

def scrape_match_details(match_id, match_link):
    try:
        logger.info(f"Starting to scrape match details for match ID: {match_id}...")
        details_scraper = Scraper(isMonitoring=False)
        match_details = details_scraper.scrape_match_details(match_link)
        match_details_collection.update_one({"match_id": match_id}, {"$set": match_details})
        logger.info(f"Match details for match ID {match_id} scraped and saved successfully.")
    except Exception as e:
        logger.error(f"Error occurred while scraping match details for match ID {match_id}: {e}")

def start_live_scraping(match_id, match_link):
    try:
        logger.info(f"Starting live scraping for match ID: {match_id}...")
        match_link_live = "https://www.crex.live" + match_link.replace('info', 'live')
        match_link_scorecard = "https://www.crex.live" + match_link.replace('info', 'scorecard')

        live_scraper = Scraper(match_link=match_link_live, isMonitoring=True)
        scorecard_scraper = Scraper(match_link=match_link_scorecard, isMonitoring=True)

        while True:
            live_data = live_scraper.scrape_match_live_feed(match_link_live)
            scorecard_data = scorecard_scraper.scrape_match_scorecard(match_link_scorecard)

            live_data["match_id"] = str(match_id)
            scorecard_data["match_id"] = str(match_id)

            save_to_db(live_page_collection, live_data, unique_field=match_id)
            save_to_db(scorecard_collection, scorecard_data, unique_field=match_id)

            if "player_of_the_match" in live_data.keys():
                logger.info(f"Match ID {match_id} finished. Player of the match: {live_data.get('player_of_the_match')}")
                break

            logger.debug(f"Live data and scorecard data updated for match ID {match_id}")
            time.sleep(2)

    except Exception as e:
        logger.error(f"Error occurred during live scraping for match ID {match_id}: {e}\n{traceback.format_exc()}")


if __name__ == "__main__":
    schedule_jobs()
    # schedule_timed_jobs_for_today_matches()
    # scraper = Scraper(match_link="https://www.crex.live/scoreboard/RQR/1OX/92nd-Match/OU/Z4/mma-vs-mtd-92nd-match-european-cricket-series-malta-2024/live", isMonitoring=True)
    
    # # Scrape match list
    # # matches = scraper.scrape_match_list()
    # match_info = scraper.scrape_match_live_feed("https://www.crex.live/scoreboard/RQR/1OX/92nd-Match/OU/Z4/mma-vs-mtd-92nd-match-european-cricket-series-malta-2024/info")
    # print(">")
    # match_info = json.dumps(match_info,indent=4)
    # print(match_info)
    # # Close the driver
    # # scraper.close()

