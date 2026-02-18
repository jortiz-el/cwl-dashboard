from fastapi import FastAPI
from .cwl_logic import get_league_group, get_war_summary, get_full_cwl_summary, get_clan_info

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/cwl/league-group")
def cwl_league_group(clan_tag: str):
    return get_league_group(clan_tag)

@app.get("/cwl/war-summary")
def cwl_war_summary(clan_tag: str):
    return get_war_summary(clan_tag)

@app.get("/cwl/full-summary")
def cwl_full_summary(clan_tag: str):
    return get_full_cwl_summary(clan_tag)

@app.get("/clan/info")
def clan_info(clan_tag: str):
    return get_clan_info(clan_tag)

