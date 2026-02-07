from datetime import datetime, timezone
from .api_client import get_league_group_api, get_war_api

def get_league_group(clan_tag):
    return get_league_group_api(clan_tag)

def get_war(war_tag: str):
    return get_war_api(war_tag)


def find_all_my_wars(group_json, clan_tag):
    wars_list = []

    for round_idx, round_wars in enumerate(group_json.get("rounds", []), start=1):
        war_tags_list = round_wars.get("warTags", [])

        for war_tag in war_tags_list:
            if not isinstance(war_tag, str) or not war_tag.startswith("#") or war_tag == "#0":
                continue

            try:
                war = get_war(war_tag)
            except Exception as e:
                print(f"⚠️ No se pudo cargar warTag {war_tag}: {e}")
                continue

            if war["clan"]["tag"] == clan_tag or war["opponent"]["tag"] == clan_tag:
                wars_list.append((war, round_idx))

    return wars_list

def parse_end_time(war):
    end_time_str = war.get("endTime")
    if not end_time_str:
        return None

    dt = datetime.strptime(end_time_str, "%Y%m%dT%H%M%S.000Z")
    return dt.replace(tzinfo=timezone.utc)

def get_time_left(end_time_str):
    # Formato: 20240205T123456.000Z
    end_time = datetime.strptime(end_time_str, "%Y%m%dT%H%M%S.000Z")
    end_time = end_time.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)

    delta = end_time - now
    if delta.total_seconds() < 0:
        return "Finalizada"

    hours, rem = divmod(int(delta.total_seconds()), 3600)
    minutes, _ = divmod(rem, 60)
    return f"{hours}h {minutes}m"

def print_attack_ranking(war, clan_tag):
    if war["clan"]["tag"] == clan_tag:
        me = war["clan"]
    else:
        me = war["opponent"]

    rows = []

    for m in me.get("members", []):
        name = m["name"]
        pos = m["mapPosition"]
        attacks = m.get("attacks", [])

        if attacks:
            a = attacks[0]
            stars = a.get("stars", 0)
            destr = a.get("destructionPercentage", 0)
            attacked = True
        else:
            stars = 0
            destr = 0
            attacked = False

        rows.append({
            "name": name,
            "pos": pos,
            "stars": stars,
            "destr": destr,
            "attacked": attacked
        })

    rows.sort(key=lambda x: (x["stars"], x["destr"]), reverse=True)

    print(f"\n📊 RANKING DE ATAQUES — {me['name']}")
    print("-" * 60)
    print(f"{'#':<3} {'Jugador':<18} {'⭐':<3} {'%':<6} {'Estado'}")
    print("-" * 60)

    for i, r in enumerate(rows, start=1):
        estado = "✅" if r["attacked"] else "❌ NO ATACÓ"
        print(f"{i:<3} {r['name']:<18} {r['stars']:<3} {r['destr']:<6} {estado}")

    print("-" * 60)

def get_attack_ranking_data(war, clan_tag):
    if war["clan"]["tag"] == clan_tag:
        me = war["clan"]
    else:
        me = war["opponent"]

    rows = []

    for m in me.get("members", []):
        name = m["name"]
        pos = m["mapPosition"]
        attacks = m.get("attacks", [])

        if attacks:
            a = attacks[0]
            stars = a.get("stars", 0)
            destr = a.get("destructionPercentage", 0)
            attacked = True
        else:
            stars = 0
            destr = 0
            attacked = False

        attack_icon = "⚔️" if attacked else "❌"
        #star_icon = "⭐" * stars if stars > 0 else "⚫"

        rows.append({
            "Jugador": name,
            "Pos": pos,

            "Atacó": attacked,
            "Estado": attack_icon,

            "Estrellas": render_stars(stars),
            "_stars_sort": stars,

            "% Destrucción": f"{destr:.2f}%",
            "_destr_sort": destr,
        })

    rows.sort(key=lambda x: (x["Estrellas"], x["% Destrucción"]), reverse=True)
    return rows

def render_stars(n):
    """
    Devuelve un string con 3 estrellas: amarillas por las obtenidas, grises por las no obtenidas
    n: número de estrellas obtenidas (0 a 3)
    """
    total_stars = 3
    yellow = "⭐"
    gray = "✩" 
    return yellow * n + gray * (total_stars - n)

def get_war_summary(war, clan_tag):
    if war["clan"]["tag"] == clan_tag:
        me = war["clan"]
        opp = war["opponent"]
    else:
        me = war["opponent"]
        opp = war["clan"]

    return {
        "me_name": me["name"],
        "opp_name": opp["name"],
        "me_attacks": me.get("attacks", 0),
        "me_max_attacks": len(me.get("members", [])),
        "me_stars": me.get("stars", 0),
        "me_destr": me.get("destructionPercentage", 0),

        "opp_attacks": opp.get("attacks", 0),
        "opp_max_attacks": len(opp.get("members", [])),
        "opp_stars": opp.get("stars", 0),
        "opp_destr": opp.get("destructionPercentage", 0),

        "state": war.get("state"),
        "round": war.get("round")
    }

def get_full_cwl_summary(clan_tag: str):
    group = get_league_group_api(clan_tag)
    if not group:
        return {"wars": []}

    wars_found = find_all_my_wars(group, clan_tag)
    wars_payload = []

    for war, round_idx in wars_found:
        # summary básico
        summary = get_war_summary(war, clan_tag)

        # ranking
        ranking = get_attack_ranking_data(war, clan_tag)

        # badges
        if war["clan"]["tag"] == clan_tag:
            me = war["clan"]
            opp = war["opponent"]
        else:
            me = war["opponent"]
            opp = war["clan"]

        wars_payload.append({
            "round": round_idx,
            "state": war.get("state"),
            "end_time": war.get("endTime"),
            "time_left": get_time_left(war.get("endTime")),

            "me": {
                "name": me.get("name"),
                "badge": me.get("badgeUrls", {}).get("small"),
            },
            "opp": {
                "name": opp.get("name"),
                "badge": opp.get("badgeUrls", {}).get("small"),
            },

            "summary": summary,
            "ranking": ranking,
        })

    return {
        "clan_tag": clan_tag,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "wars": wars_payload,
    }