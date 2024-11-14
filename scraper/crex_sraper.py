from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

from scraper.score_card import get_score_card_details
from scraper.left_wrapper import get_left_wrapper_details
from scraper.right_wrapper import get_right_wrapper_details
from scraper.scorecard import get_scorecard
from scraper.live import get_live_details

import time
import json

class Scraper:
    def __init__(self, match_link, isMonitoring = False):
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.isMonitoring = isMonitoring

        if isMonitoring:
            self.driver.get(match_link)
            time.sleep(3)

    def scrape_match_list(self):
        url = "https://crex.live/fixtures/match-list"
        self.driver.get(url)
        matches = []

        while True:
            try:
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                start=time.time()
                date_wise_wrap = soup.find("div", attrs={"id": "date-wise-wrap", "class": "date-wise-matches-card"})
                try:
                    empty_state = self.driver.find_element(By.CSS_SELECTOR, "div.emptyStateText")
                    if "Match isn't available at the moment" in empty_state.text:
                        print("No more matches available.")
                        break  # Exit the loop
                except Exception as e:
                    pass                

                if not date_wise_wrap:
                    print("No match list found on this page.")
                    break

                match_divs = date_wise_wrap.find_all("div", attrs={"_ngcontent-app-root-c20": True}, recursive=False)
                print(len(match_divs))    

                for match_div in match_divs:
                    date_div = match_div.find("div", class_="date")
                    if date_div:
                        match_date = date_div.text.strip()  # Extract the text content as date
                        print(f"Date: {match_date}")

                    # Extract the matches section
                    matches_section = match_div.find("div", class_="matches-card-space")
                    if matches_section:
                        # Find the list of matches
                        match_list = matches_section.find("ul", class_="match-list-wrapper")
                        
                        if match_list:
                            # Loop over each match card in the list
                            for match_card in match_list.find_all("li", class_="match-card-container"):
                                match_data = {}

                                # Extract match link and href attribute
                                match_link = match_card.find("a", class_="match-card-wrapper")
                                if match_link:
                                    match_data['link'] = match_link['href']  # relative URL for match details

                                # Team 1 details
                                team1_info = match_card.find_all("div", class_="team")[0]  # Team 1 (left side)
                                if team1_info:
                                    team1_name = team1_info.find("span", class_="team-name").text.strip()
                                    team1_score = team1_info.find("span", class_="team-score")
                                    team1_overs = team1_info.find("span", class_="total-overs")
                                    
                                    match_data['team1'] = {
                                        'name': team1_name,
                                        'score': team1_score.text.strip() if team1_score else "N/A",
                                        'overs': team1_overs.text.strip() if team1_overs else "N/A"
                                    }

                                # Team 2 details (right side)
                                team2_info = match_card.find_all("div", class_="team")[1]  # Team 2 (right side)
                                if team2_info:
                                    team2_name = team2_info.find("span", class_="team-name").text.strip()
                                    team2_score = team2_info.find("span", class_="team-score")
                                    
                                    match_data['team2'] = {
                                        'name': team2_name,
                                        'score': team2_score.text.strip() if team2_score else "N/A"
                                    }

                                # Live status or result info
                                live_status = match_card.find("div", class_="live-info")
                                if live_status:
                                    match_data['status'] = live_status.find("span", class_="liveTag").text.strip()

                                matches.append(match_data)

                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, "button.arrow.arrow-right")
                    next_button.click()
                    print("Next page button clicked.")
                    time.sleep(0.5)
                except Exception as e:
                    print("Failed to find or click the 'Next Page' button:", e)

                end=time.time()
                print(">", end-start)  # Wait for the new page to load

            except Exception as e:
                print("Error while scraping match list:", e)
                break

        return matches

    def scrape_match_details(self, match_url):
        """Scrapes the details of an individual match from its URL."""
        # Match info

        base_url = "https://www.crex.live"
        match_info_url= base_url+match_url
        self.driver.get(match_info_url)
        time.sleep(3)

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        score_card_div = soup.find("div", attrs={"class": "live-score-card"})
        score_card_details = get_score_card_details(score_card_div)

        left_wrapper_div = soup.find("div", attrs={"class": "info-left-wrapper"})
        left_wrapper_details = get_left_wrapper_details(self.driver, left_wrapper_div)

        right_wrapper_div = soup.find("div", attrs={"class": "info-right-wrapper"})
        right_wrapper_details = get_right_wrapper_details(self.driver,right_wrapper_div)

        return score_card_details | left_wrapper_details | right_wrapper_details
    
    def scrape_match_scorecard(self, match_url):
        print("Getting scorecard")
        if not self.isMonitoring:
            base_url = "https://www.crex.live"
            match_url = match_url.replace('info', 'scorecard')
            match_info_url= base_url+match_url
            self.driver.get(match_info_url)

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        scorecard_soup = soup.find("div", class_="container live-screen-wrap")
        scorecard_data={}
        if scorecard_soup:
            match_data = {
                "teams": {},
                "batting": {},
                "bowling": {},
                "fall_of_wickets": {},
                "partnerships": {},
                "yet_to_bat": {}
            }
            scorecard_data, card  = get_scorecard(scorecard_soup, match_data)
            print(card)
            if card["n_cards"]==2:
                print("here")
                clickables = {
                    "1":self.driver.find_element(By.XPATH, "/html/body/app-root/div/app-match-details/div[3]/div/app-match-scorecard/div/div[1]/div[1]/div[1]/div/div"),
                    "0":self.driver.find_element(By.XPATH, "/html/body/app-root/div/app-match-details/div[3]/div/app-match-scorecard/div/div[1]/div[1]/div[2]/div")
                }        
                clickables[card["current"]].click()
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                scorecard_soup = soup.find("div", class_="container live-screen-wrap")
                scorecard_data, card  = get_scorecard(scorecard_soup, scorecard_data)

        return scorecard_data
    
    def scrape_match_live_feed(self, match_url):
        print("Getting live feed", match_url)
        if not self.isMonitoring:
            print("Not here")
            base_url = "https://www.crex.live"
            match_url = match_url.replace('info', 'live')
            match_info_url= base_url+match_url
            self.driver.get(match_info_url)

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        live_data = get_live_details(soup)
        return live_data
           
    def close(self):
        """Closes the WebDriver instance."""
        self.driver.quit()

# Example usage
if __name__ == "__main__":
    scraper = Scraper(match_link="/scoreboard/RQR/1OX/92nd-Match/OU/Z4/mma-vs-mtd-92nd-match-european-cricket-series-malta-2024/info", isMonitoring=True)
    
    # Scrape match list
    # matches = scraper.scrape_match_list()
    match_info = scraper.scrape_match_live_feed("/scoreboard/RQR/1OX/92nd-Match/OU/Z4/mma-vs-mtd-92nd-match-european-cricket-series-malta-2024/info")
    print(">")
    match_info = json.dumps(match_info,indent=4)
    print(match_info)
    # Close the driver
    # scraper.close()
