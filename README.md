# real-time-cricket-data-scraper
## Overview
This is a web scraping project which scrape details from `crex.live` website for the upcoming fixture of matches. Additionally, system automatically triggers individual match scraping jobs for real-time "Scorecard" and "Live" data whenever a match starts according to its schedule.
The focus is on the ability to do it more efficiently on the both resource and latency front.
### Tech Used
- **Selenium** for browser automation
- **BeautifulSoup4** for HTML parsing
- **MongoDB** for database
- **APScheduler** for scheduling jobs

## Scheduler Execution Flow:
- Scheduler runs every day:
    - At 06:00 AM, it starts the job to scrape the match list.
    - At 07:00 AM, it starts the job to update match details.
    - At 08:00 AM, it schedules the timed scraping jobs for all matches happening that day.
- For each match happening today:
  - The schedule_timed_jobs_for_today_matches function schedules:
    - A job to scrape match details 20 minutes before the match.
    - A job to start live page scraping exactly at match start time.
    - A job to start scorecard scraping exactly at match start time.

## MongoDB collections
- match_list
- match_details
- scorecard
- live_page

## Setup
1. Setup .env by taking reference from `sample.env`
2. Create a virtual environment and activate it
    ```
    python -m venv venv
    source venv/bin/activate
    ```
3. Install required dependencies
    ```
    pip install -r requirements.txt
    ```

## Start app
Start the scheduler from the following command. This will automatically put jobs to scrape the details and will save to the database.
  ```
  python main.py
  ```