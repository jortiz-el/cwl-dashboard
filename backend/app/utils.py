from .leagues import CWL_LEAGUES

def get_league_info(league_id: int):
    return CWL_LEAGUES.get(
        league_id,
        {
            "name": f"Liga desconocida ({league_id})",
            "logo": None
        }
    )
