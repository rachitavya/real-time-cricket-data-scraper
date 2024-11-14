from scraper.utils import safe_text

def get_left_wrapper_details(driver, left_wrapper_div):
    if not left_wrapper_div:
        return {}
    
    # Series data
    series_url = left_wrapper_div.find("a", class_="content-wrap s-wrap")["href"] if left_wrapper_div.find("a", class_="content-wrap s-wrap") else None
    image_url = left_wrapper_div.find("img").get("src") if left_wrapper_div.find("img") else None
    alt_text = left_wrapper_div.find("img").get("alt") if left_wrapper_div.find("img") else None
    match_format = left_wrapper_div.find("div", class_="s-format").text.strip() if left_wrapper_div.find("div", class_="s-format") and left_wrapper_div.find("div", class_="s-format").text else None
    series_name = left_wrapper_div.find("div", class_="s-name").text.strip() if left_wrapper_div.find("div", class_="s-name") and left_wrapper_div.find("div", class_="s-name").text else None

    # Date and venue
    date_div = left_wrapper_div.find("div", class_="match-date")
    match_date = date_div.find("div").text.strip() if date_div and date_div.find("div") and date_div.find("div").text else None
    venue_div = left_wrapper_div.find("div", class_="match-date match-venue")
    match_venue = venue_div.find("div").text.strip() if venue_div and venue_div.find("div") and venue_div.find("div").text else None
    team_names = left_wrapper_div.find_all("div", class_="form-team-name")

    # Recent matches
    recent_match_cards_wrappers = left_wrapper_div.find_all('div', class_="format-match-exp")
    
    recent_matches = {}
    for i, card_wrapper in enumerate(recent_match_cards_wrappers):
        team_name = team_names[i].text.strip() if i < len(team_names) else None
        if team_name:
            recent_matches[team_name] = []

            recent_match_cards = card_wrapper.find_all('div', class_="format-card-wrap")
            for card in recent_match_cards:
                match = {}
                teams = card.find_all('div', class_="team-name")
                match['team1'] = teams[0].text.strip() if len(teams) > 0 and teams[0].text else None
                match['team2'] = teams[1].text.strip() if len(teams) > 1 and teams[1].text else None

                scores = card.find_all('div', class_="team-score")
                overs = card.find_all('div', class_="team-over")
                url = card.find('a', class_='team-form-card')
                match['team1_score'] = scores[0].text.strip() if len(scores) > 0 and scores[0].text else None
                match['team1_overs'] = overs[0].text.strip() if len(overs) > 0 and overs[0].text else None
                match['team2_score'] = scores[1].text.strip() if len(scores) > 1 and scores[1].text else None
                match['team2_overs'] = overs[1].text.strip() if len(overs) > 1 and overs[1].text else None
                match["url"] = url["href"] if url and url.get("href") else None

                result = card.find('div', class_="win match") or card.find('div', class_="loss match")
                match['result'] = result.text.strip() if result and result.text else "N/A"
                
                recent_matches[team_name].append(match)

    # Head-to-head matches
    head_to_head = []
    match_cards = left_wrapper_div.find_all('a', class_= "global-match-card gmc-without-logo")
    for card in match_cards:
        match_link = card['href'] if card and card.get('href') else None
        teams = [team.get_text(strip=True) for team in card.find_all('div', class_='team-name')] if card else []
        scores = {}
        overs = card.find_all('div', class_='team-over') if card else []
        score_elements = card.find_all('div', class_='team-score') if card else []
        for team, score, over in zip(teams, score_elements, overs):
            team_data = {
                "overs": over.get_text(strip=True) if over else None,
                "score": score.get_text(strip=True) if score else None
            }
            scores[team] = team_data
        winner = card.find('div', class_='match-dec-text').get_text(strip=True) if card.find('div', class_='match-dec-text') else None
        series = card.find('div', class_='series-name').get_text(strip=True) if card.find('div', class_='series-name') else None

        match_data = {
            'match_link': match_link,
            'teams': teams,
            'scores': scores,
            'winner': winner,
            'series': series
        }
        head_to_head.append(match_data)

    # Comparison data
    comparison_data = {}
    header_card_soup = left_wrapper_div.find("div", class_="team-header-card") if left_wrapper_div else None
    team_1 = header_card_soup.find('div', class_='team1').find('div', class_='team-name').get_text(strip=True) if header_card_soup and header_card_soup.find('div', class_='team1') and header_card_soup.find('div', class_='team1').find('div', class_='team-name') else None
    team_2 = header_card_soup.find('div', class_='team2').find('div', class_='team-name').get_text(strip=True) if header_card_soup and header_card_soup.find('div', class_='team2') and header_card_soup.find('div', class_='team2').find('div', class_='team-name') else None

    def extract_comparison(table_soup, team_1=team_1, team_2=team_2):
        comparison_data = {}
        comparison_rows = table_soup.find_all('tr') if table_soup else []
        for row in comparison_rows:
            cells = row.find_all('td') if row else []
            if len(cells) == 3:
                stat_value = cells[0].get_text(strip=True) if cells[0] else None
                stat_name = cells[1].get_text(strip=True) if cells[1] else None
                comparison_data[stat_name] = {
                    team_1: stat_value,
                    team_2: cells[2].get_text(strip=True) if cells[2] else None
                }
        return comparison_data

    table_soup = left_wrapper_div.find("table", class_= "table table-borderless colHeader") if left_wrapper_div else None
    overall_comparison = extract_comparison(table_soup)

    table_soup = left_wrapper_div.find("table", class_= "table table-borderless colHeader") if left_wrapper_div else None
    on_venue_comparison = extract_comparison(table_soup)

    comparison_data = {
        "overall": overall_comparison,
        "on_venue": on_venue_comparison
    }

    # Venue details
    venue_soup = left_wrapper_div.find("div", id="venue-details")
    venue_data = {
        "venue_name": safe_text(venue_soup.find('div', class_='title-text')),
        "weather_temp": safe_text(venue_soup.find('div', class_='weather-temp')),
        "weather_condition": safe_text(venue_soup.find('div', class_='weather-cloudy-text-mweb')),
        "humidity": safe_text(venue_soup.find('div', class_='weather-place-hum-text')),
        "rain_chance": safe_text(venue_soup.find_all('div', class_='weather-place-hum-text')[1]) if len(venue_soup.find_all('div', class_='weather-place-hum-text')) > 1 else None,
        "matches_played": safe_text(venue_soup.find('div', class_='match-count'))
    } if venue_soup else {}

    # Pace and spin data
    pace_spin_soup = venue_soup.find("div", class_="venue-pace-wrap") if venue_soup else None
    percentages = pace_spin_soup.find('div', class_='progress-bar-wrap').find_all('div', class_='s-format') if pace_spin_soup else []
    venue_data["pace_spin_data"] = {
        'Pace': {
            'wickets': int(pace_spin_soup.find('div', class_='pace-text', text='Pace').find_next('div', class_='wicket-count').text.strip().split()[0]) if pace_spin_soup and pace_spin_soup.find('div', class_='pace-text', text='Pace') else None,
            'percentage': int(percentages[0].text.strip().replace('%', '')) if len(percentages) > 0 else None
        },
        'Spin': {
            'wickets': int(pace_spin_soup.find('div', class_='pace-text', text='Spin').find_next('div', class_='wicket-count').text.strip().split()[0]) if pace_spin_soup and pace_spin_soup.find('div', class_='pace-text', text='Spin') else None,
            'percentage': int(percentages[1].text.strip().replace('%', '')) if len(percentages) > 1 else None
        }
    }

    # Venue recent matches
    venue_recent_match_cards = venue_soup.find_all('app-form-match-card') if venue_soup else []
    venue_recent_matches_data = []
    for match in venue_recent_match_cards:
        match_link = match.find('a')['href'] if match.find('a') else None
        teams = match.find_all('div', class_='team-name')
        team_1 = teams[0].text.strip() if len(teams) > 0 else None
        team_2 = teams[1].text.strip() if len(teams) > 1 else None
        scores = match.find_all('div', class_='team-score')
        score_1 = scores[0].text.strip() if len(scores) > 0 else None
        score_2 = scores[1].text.strip() if len(scores) > 1 else None
        result = match.find('div', class_='match-result').text.strip() if match.find('div', class_='match-result') else None
        venue_recent_matches_data.append({
            'match_link': match_link,
            'team_1': team_1,
            'team_2': team_2,
            'score_1': score_1,
            'score_2': score_2,
            'result': result
        })
    venue_data["recent_matches"] = venue_recent_matches_data

    # Umpire data
    umpire_data = []
    umpires = left_wrapper_div.find_all('div', class_='umpire-text')
    for umpire in umpires:
        umpire_name = umpire.get_text(strip=True)
        umpire_data.append(umpire_name)

    return {
        "series_url": series_url,
        "image_url": image_url,
        "alt_text": alt_text,
        "match_format": match_format,
        "series_name": series_name,
        "match_date": match_date,
        "match_venue": match_venue,
        "recent_matches": recent_matches,
        "head_to_head": head_to_head,
        "comparison_data": comparison_data,
        "venue_data": venue_data
    }



if __name__=="__main__":
    get_left_wrapper_details()