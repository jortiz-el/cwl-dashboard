import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.clashofclans.com/v1"
API_KEY = os.getenv("COC_API_KEY")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}

def encode(tag: str) -> str:
    return requests.utils.quote(tag)

def get_league_group_api(clan_tag):
    url = f"{BASE_URL}/clans/{encode(clan_tag)}/currentwar/leaguegroup"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()

def get_war_api(war_tag):
    url = f"{BASE_URL}/clanwarleagues/wars/{encode(war_tag)}"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json()
