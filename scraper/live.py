import re
import json
from bs4 import BeautifulSoup
from scraper.score_card import get_score_card_details

def split_crr_rrr(text):
    pattern = r"(CRR\s*:\s*\d+\.\d+)|(RRR\s*:\s*\d+\.\d+)"
    matches = re.findall(pattern, text)
    crr=rrr=remaining=""
    for match in matches:
        if match[0]:
            crr = match[0].strip().split(":")[1]
        if match[1]:
            rrr = match[1].strip().split(":")[1]
    remaining = re.sub(pattern, "", text).strip()
    remaining = remaining
    return crr, rrr, remaining

def get_live_details(soup):
    # 1. Ball status
    score_card_div = soup.find("div", attrs={"class": "live-score-card"})
    score_card_details = get_score_card_details(score_card_div)
    print(score_card_details)
    if score_card_details["team_2_name"] and "CRR" in score_card_details["team_2_name"]:
        crr, rrr, text = split_crr_rrr(score_card_details["team_2_name"])
        score_card_details["crr"] = crr
        score_card_details["rrr"] = rrr
        score_card_details["other_relevant_info"]=text
        score_card_details["recent_happening"] = score_card_details["match_result"]
        del score_card_details["team_2_score"]
        del score_card_details["team_2_overs"]
        del score_card_details["team_2_name"]
        del score_card_details["match_result"]


    # 2. Live players
    live_players_soup = soup.find("div", class_="playing-batsmen-wrapper")
    if live_players_soup:
        live_players = {"batters":[],"bowlers":[]}
        for player_card in live_players_soup.find_all("div", class_="batsmen-partnership"):
            name_tag = player_card.select_one('.batsmen-name a p')
            profile_link = player_card.select_one('.batsmen-name a')['href'] if player_card.select_one('.batsmen-name a') else None
            player_name = name_tag.text.strip() if name_tag else None
            score_tag = player_card.select_one('.batsmen-score p')
            balls_tag = player_card.select('.batsmen-score p')[1] if len(player_card.select('.batsmen-score p')) > 1 else None
            score = score_tag.text.strip() if score_tag else None
            balls = balls_tag.text.strip() if balls_tag else None
            fours = player_card.select_one('.strike-rate.right-space span:nth-of-type(2)').text.strip() if player_card.select_one('.strike-rate.right-space span:nth-of-type(2)') else None
            sixes = player_card.select_one('.strike-rate span:nth-of-type(2)').text.strip() if player_card.select_one('.strike-rate span:nth-of-type(2)') else None
            strike_rate = player_card.select_one('.strike-rate:last-of-type span:nth-of-type(2)').text.strip() if player_card.select_one('.strike-rate:last-of-type span:nth-of-type(2)') else None    
            on_strike=True if 'circle-strike-icon' in str(player_card) else False

            if '''class="bowler"''' in str(player_card):
                wickets, runs = tuple(score.split("-"))
                live_players["bowlers"].append({
                    "status":"bowling",
                    "name": player_name,
                    "profile_link": profile_link,
                    "wickets": wickets,
                    "runs_given": runs,
                    "overs": balls,                
                    "economy": strike_rate
                })
            else:

                live_players["batters"].append({
                    "status":"batting",
                    "name": player_name,
                    "profile_link": profile_link,
                    "score": score,
                    "balls": balls,
                    "4s": fours,
                    "6s": sixes,
                    "SR": strike_rate,
                    "on_strike": on_strike
                })
    else:
        live_players={}

    # 3. Win probabilities
    win_probabilities={}
    teams = [team.get_text() for team in soup.find_all('div', class_='teamNameScreenText')]
    probabilities = [prob.get_text() for prob in soup.find_all('div', class_='percentageScreenText')]
    if teams and win_probabilities:
        win_probabilities={
            "win_probabilities":{
                teams[0]:win_probabilities[0],
                teams[1]:probabilities[1],
            },
        }


    #4. POTM
    potm_data={}
    potm_soup = soup.find("div", class_="player-of-match-card")
    if potm_soup:
        player_name = potm_soup.find("span", class_="mom-player").text.strip() if potm_soup.find("span", class_="mom-player") else None
        team_name = potm_soup.find("div", class_="player-align").find_all("span")[-1].text.strip() if potm_soup.find("div", class_="player-align") else None
        bowling_score = potm_soup.find("div", class_="data-card-pom font2 font2copy").text.strip() if potm_soup.find("div", class_="data-card-pom font2 font2copy") else None
        batting_score = potm_soup.find("div", class_="data-card-pom font2").text.strip() if potm_soup.find("div", class_="data-card-pom font2") else None
        potm_data = {"player_of_the_match":{"player_name": player_name, "team_name":team_name, "bowling_score":bowling_score, "batting_score":batting_score}}
        
    return {} | score_card_details| live_players | win_probabilities | potm_data

if __name__=="__main__":
    import requests
    res = requests.get("https://crex.live/scoreboard/RQT/1OX/94th-Match/OT/OU/edk-vs-mtd-94th-match-european-cricket-series-malta-2024/live")
    soup = BeautifulSoup(res.text, "html.parser")
    print(json.dumps(get_live_details(soup), indent=2))
