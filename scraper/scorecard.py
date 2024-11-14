from bs4 import BeautifulSoup
import json

def get_scorecard(soup, match_data):

    # 1. Team Score Parsing
    team_elements = soup.select(".c-2 .team-tab")
    n=len(team_elements)

    for i,team in enumerate(team_elements):
        team_name = team.select_one(".team-name").get_text(strip=True)
        team_score = team.select_one(".score-over span").get_text(strip=True)
        team_overs = team.select_one(".over").get_text(strip=True).strip("()")
        match_data["teams"][team_name] = {
            "score": team_score,
            "overs": team_overs
        }
        if "team-tab m-right bgColor" in str(team):
            current_team = team_name
            current_team_position=i

    # 2. Batting Table Parsing (including batting status)
    match_data["batting"][current_team]=[]
    batting_table_soup = soup.select(".bowler-table tbody")[0] if soup.select(".bowler-table tbody") else None
    if batting_table_soup:
        for row in batting_table_soup.find_all("tr"):
            player_name = row.select_one(".batsman-name .player-name").get_text(strip=True)
            batting_status = row.find('div', class_="decision").text.strip()
            runs = row.select("td")[1].get_text(strip=True)
            balls = row.select("td")[2].get_text(strip=True)
            fours = row.select("td")[3].get_text(strip=True)
            sixes = row.select("td")[4].get_text(strip=True)
            strike_rate = row.select("td")[5].get_text(strip=True)
            match_data["batting"][current_team].append({
                "player": player_name,
                "status": batting_status,
                "runs": runs,
                "balls": balls,
                "fours": fours,
                "sixes": sixes,
                "strike_rate": strike_rate
            })

    # 3. Bowling Table Parsing
    match_data["bowling"][current_team]=[]
    bowling_table_soup = soup.select(".bowler-table tbody")
    if bowling_table_soup:
        bowling_table_soup=bowling_table_soup[1]
        for row in bowling_table_soup.find_all("tr"):
            bowler_name = row.select_one(".bowler-name .player-name").get_text(strip=True)
            overs = row.select("td")[1].get_text(strip=True)
            maidens = row.select("td")[2].get_text(strip=True)
            runs = row.select("td")[3].get_text(strip=True)
            wickets = row.select("td")[4].get_text(strip=True)
            economy = row.select("td")[5].get_text(strip=True)
            match_data["bowling"][current_team].append({
                "bowler": bowler_name,
                "overs": overs,
                "maidens": maidens,
                "runs": runs,
                "wickets": wickets,
                "economy": economy
            })

    # 4. Fall of Wickets Parsing
    match_data["fall_of_wickets"][current_team]=[]
    fall_of_wickets_table_soup = soup.select(".bowler-table tbody")
    if fall_of_wickets_table_soup:
        fall_of_wickets_table_soup = fall_of_wickets_table_soup[2]
        for row in fall_of_wickets_table_soup.find_all("tr"):
            batsman = row.select_one(".bowler-name .player-name").get_text(strip=True)
            score = row.select("td")[1].get_text(strip=True)
            overs = row.select("td")[2].get_text(strip=True)
            match_data["fall_of_wickets"][current_team].append({
                "batsman": batsman,
                "score": score,
                "overs": overs
            })

    # 5. Partnership Parsing (complete partnership details)
    match_data["partnerships"][current_team]=[]
    partnership_sections = soup.select(".p-section-wrapper")
    if partnership_sections:
        for section in partnership_sections:
            wicket_info = section.select_one(".p-wckt-info").get_text(strip=True)
            partnership_runs = section.select_one(".run-total").get_text(strip=True) if section.select_one(".run-total") else "0"
            partnership = {
                "wicket": wicket_info,
                "partnership_runs": partnership_runs,
                "batters": []
            }
            for i,data in enumerate(section.select(".p-info-wrapper .p-data")):
                if i==1:
                    partnership["partnership_runs"]=data.select_one("p").get_text(strip=True)
                    continue
                batter_name = data.select_one("p").text.strip()
                runs = data.find("p", recursive=False).contents[0].strip()
                balls = data.select_one(".run-highlight").get_text(strip=True)
                partnership["batters"].append({
                    "batter": batter_name,
                    "runs": f"{runs}{balls}"
                })
            match_data["partnerships"][current_team].append(partnership)

    # 6. Yet to Bat Parsing
    match_data["yet_to_bat"][current_team]=[]
    yet_to_bat_section = soup.select(".yet-to-bat .content")
    if yet_to_bat_section:
        for player in yet_to_bat_section:
            player_name = player.select_one(".name").get_text(strip=True)
            avg = player.select_one("span").get_text(strip=True)
            match_data["yet_to_bat"][current_team].append({
                "player": player_name,
                "average": avg
            })

    
    return match_data, {"n_cards":n, "current":str(current_team_position)}
