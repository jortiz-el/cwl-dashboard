import os
import requests
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

BASE_URL = "https://api.clashofclans.com/v1"

if "COC_API_TOKEN" in st.secrets:
    API_KEY = st.secrets["COC_API_TOKEN"]
else:
    API_KEY = os.getenv("COC_API_TOKEN")

if not API_KEY:
    raise RuntimeError("COC_API_TOKEN not found in secrets or env vars")

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
    
    if r.status_code != 200:
        raise Exception(
            f"COC API ERROR\n"
            f"Status: {r.status_code}\n"
            f"URL: {r.url}\n"
            f"Response: {r.text}"
        )
    
    r.raise_for_status()
    return r.json()

def get_war_api(war_tag):
    url = f"{BASE_URL}/clanwarleagues/wars/{encode(war_tag)}"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json()
