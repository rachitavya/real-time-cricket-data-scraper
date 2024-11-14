def get_score_card_details(score_card_div):
    if not score_card_div:
        return {}
    # Extract Team 1 details
    team_1_name = score_card_div.find("div", class_="team-name team-1").text.strip() if score_card_div.find("div", class_="team-name team-1") else None
    team_1_score = score_card_div.find("div", class_="team-score").find("span").text.strip() if score_card_div.find("div", class_="team-score") and score_card_div.find("div", class_="team-score").find("span") else None
    team_1_overs = score_card_div.find("div", class_="team-score").find_all("span")[1].text.strip() if score_card_div.find("div", class_="team-score") and len(score_card_div.find("div", class_="team-score").find_all("span")) > 1 else None

    # Extract Team 2 details (with additional checks)
    team_2_name = None
    team_2_score = None
    team_2_overs = None

    team_2_div = score_card_div.find("div", class_="team-name team-2 text-right")
    if team_2_div:
        team_2_name = team_2_div.find("div").text.strip() if team_2_div.find("div") else None
    team_2_score_div = score_card_div.find("div", class_="team-score text-right")
    if team_2_score_div:
        team_2_score = team_2_score_div.find("span").text.strip() if team_2_score_div.find("span") else None
        team_2_overs = team_2_score_div.find_all("span")[1].text.strip() if len(team_2_score_div.find_all("span")) > 1 else None

    # Extract match result or status
    match_result = score_card_div.find("div", class_="result-box").find("span", class_="font3").text.strip() if score_card_div.find("div", class_="result-box") and score_card_div.find("div", class_="result-box").find("span", class_="font3") else None

    data = {
        "team_1_name": team_1_name,
        "team_1_score": team_1_score,
        "team_1_overs": team_1_overs,
        "team_2_name": team_2_name,
        "team_2_score": team_2_score,
        "team_2_overs": team_2_overs,
        "match_result": match_result
    }

    return data
