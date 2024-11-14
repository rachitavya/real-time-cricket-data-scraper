import time
from selenium.webdriver.common.by import By
def get_right_wrapper_details(driver, right_wrapper_div):
    if right_wrapper_div is None:
        return {}

    # Toss data
    toss_data = {}
    toss_soup = right_wrapper_div.find("div", class_="toss-wrap")
    if toss_soup:
        toss_text = toss_soup.p.text.strip() if toss_soup.p else ""
        if toss_text:
            toss_data = {
                "toss_winner": toss_text.split(" won the toss")[0],
                "decision": toss_text.split("chose to ")[-1]
            }

    # Squads
    squads_soup = right_wrapper_div.find("div", class_="playingxi")
    squads_data = {}
    if squads_soup:
        heading_soup = squads_soup.find("div", class_="playingxi-header")
        heading = heading_soup.find("h2").text.strip() if heading_soup and heading_soup.find("h2") else None
        button = squads_soup.find("button", class_="playingxi-button selected")

        if button:
            team = button.text.strip() if button.text else ""
            squads_data[heading] = {}
            squads_data[heading][team] = get_playingxi_details(squads_soup)

            # Clicking the button to update squads data
            
            # button = driver.find_element(By.XPATH, "(//div[@class='playingxi-teams']//button[@class='playingxi-button'])[2]")
            # time.sleep(2)
            # button.click()
            team = button.text.strip() if button.text else ""
            squads_data[heading][team] = get_playingxi_details(squads_soup)                                                                                                                                   

    # Final data
    data = {
        "toss_details": toss_data,
    }
    if squads_data:
        data.update(squads_data)

    return data


def get_playingxi_details(soup):
    players = []

    for card in soup.find_all('div', class_='playingxi-card-row'):
        player = {}
        name = card.find('div', class_='p-name')
        player['name'] = name.get_text(strip=True) if name else None
        role = card.find('div', class_='bat-ball-type')
        player['role'] = role.get_text(strip=True) if role else None
        
        player_name_div = card.find('div', class_='player-name')
        if player_name_div:
            captain_keeper = player_name_div.find('div', class_='flex')
            if captain_keeper:
                divs = captain_keeper.find_all('div')
                if len(divs) > 1:
                    player['status'] = divs[1].get_text(strip=True) if divs[1] else None
                else:
                    player['status'] = None
            else:
                player['status'] = None
        else:
            player['status'] = None
        
        img = card.find('img', class_='lazyload')
        player['image_url'] = img['src'] if img else None
        players.append(player)

    return players
