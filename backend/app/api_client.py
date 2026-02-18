import requests
from .config import COC_API_TOKEN, BASE_URL

HEADERS = {
    "Authorization": f"Bearer {COC_API_TOKEN}"
}

def encode(tag: str) -> str:
    return requests.utils.quote(tag)

def get_league_group_api(clan_tag: str):
    url = f"{BASE_URL}/clans/{encode(clan_tag)}/currentwar/leaguegroup"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json()

def get_war_api(war_tag: str):
    url = f"{BASE_URL}/clanwarleagues/wars/{encode(war_tag)}"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json()

def get_clan_info_api(clan_tag: str):
    clan_tag = clan_tag.replace("#", "%23")
    url = f"{BASE_URL}/clans/{clan_tag}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        return {"error": "Clan no encontrado o privado"}
    data = r.json()
    return data