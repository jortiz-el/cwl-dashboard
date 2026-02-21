from .api_client import get_clan_info_api
import os


BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

def get_clan_donations(clan_tag):

    clan = get_clan_info_api(clan_tag)  # tu función actual

    print(BACKEND_URL)

    members_data = []

    for m in clan["memberList"]:
        members_data.append({
            "name": m["name"],
            "role": m["role"],
            "donations": m.get("donations", 0),
            "received": m.get("donationsReceived", 0),
            "trophies": m.get("trophies", 0),
            "th": m.get("townHallLevel", 0),
            "th_icon": f"{BACKEND_URL}/static/th/th{m.get('townHallLevel', 0)}.png"
        })

    return {
        "clan_info": {
            "name": clan["name"],
            "badge": clan["badgeUrls"]["large"],
            "level": clan["clanLevel"],
            "league": clan.get("warLeague", {}).get("name", "No league"),
            "war_wins": clan.get("warWins", 0)
        },
        "members": members_data
    }
