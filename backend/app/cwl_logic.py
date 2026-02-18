from datetime import datetime, timezone
from .api_client import get_league_group_api, get_war_api, get_clan_info_api
from .utils import get_league_info
from .leagues import CWL_LEAGUES
import random


def get_league_group(clan_tag):
    return get_league_group_api(clan_tag)

def get_war(war_tag: str):
    return get_war_api(war_tag)

def get_clan_info(clan_tag: str):
    return get_clan_info_api(clan_tag)

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
        "me_tag": me["tag"],
        "opp_tag": opp["tag"],
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
    team_size = group.get("teamSize", 15)
    strength_ranking = calculate_group_strength(group, clan_tag, team_size)
    position_advantage = calculate_position_advantage(strength_ranking)


    league_id = group.get("leagueId")
    league_info = CWL_LEAGUES.get(league_id,{})

    # Si no hay CWL activa o la API no devuelve rounds
    if not group or not group.get("rounds"):
        return {
            "clan_tag": clan_tag,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "wars": [],
            "no_cwl": True,
            "message": "Este clan no tiene CWL activa actualmente."
        }


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


        # Estrellas y ataques actuales
        me_stars = summary['me_stars']
        me_attacks_done = summary['me_attacks']
        me_max_attacks = summary['me_max_attacks']

        opp_stars = summary['opp_stars']
        opp_attacks_done = summary['opp_attacks']
        opp_max_attacks = summary['opp_max_attacks']

        # Estimación de estrellas promedio por ataque restante
        # Aquí puedes hacer algo más sofisticado usando weighted_score/top_th
        war_state = war.get("state")

        if war_state == "warEnded":

            # Resultado real definitivo
            if me_stars > opp_stars:
                prob_data = {
                    "status": "final_win",
                    "result_text": "Victoria"
                }
            elif me_stars < opp_stars:
                prob_data = {
                    "status": "final_loss",
                    "result_text": "Derrota"
                }
            else:
                prob_data = {
                    "status": "final_draw",
                    "result_text": "Empate"
                }

        elif war_state == "inWar":

            prob_data = realtime_war_state(
                me_stars, me_attacks_done, me_max_attacks,
                opp_stars, opp_attacks_done, opp_max_attacks
            )

        else:
            prob_data = {
                "status": "not_started"
            }


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
            "win_state": prob_data,
        })

    return {
        "clan_tag": clan_tag,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "wars": wars_payload,
        "league": {
        "id": league_id,
        "name": league_info.get("name", "Unknown League"),
        "logo": league_info.get("logo", None)
        },
        "strength_ranking": strength_ranking,
        "position_advantage": position_advantage,
        "group_raw": group,
        "team_size": team_size,
    }

def calculate_group_strength(group_json, my_clan_tag, war_size):
    clans = group_json.get("clans", [])
    results = []

    for clan in clans:
        members = clan.get("members", [])

        # ordenar por TH descendente
        members_sorted = sorted(
            members,
            key=lambda x: x["townHallLevel"],
            reverse=True
        )

        top_members = members_sorted[:war_size]

        top_ths = [m["townHallLevel"] for m in top_members]

        # Promedio clásico
        avg_th = sum(top_ths) / war_size if war_size else 0

        # 🔥 NUEVO: Score ponderado real
        weighted_score = sum(
            th * (war_size - i)
            for i, th in enumerate(top_ths)
        )

        results.append({
            "rank": 0,
            "name": clan["name"],
            "top_avg_th": round(avg_th, 2),
            "weighted_score": weighted_score,
            "top_members": top_members, 
            "is_me": clan["tag"] == my_clan_tag
        })

    results.sort(
        key=lambda x: x["weighted_score"],
        reverse=True
    )

    for i, r in enumerate(results, start=1):
        r["rank"] = i

    return results

def calculate_position_advantage(strength_data):
    my_clan = next(c for c in strength_data if c["is_me"])

    comparisons = []

    for clan in strength_data:
        if clan["is_me"]:
            continue

        diff_sum = 0
        positions = len(my_clan["top_members"])

        for i in range(positions):
            my_th = my_clan["top_members"][i].get("townHallLevel", 0)
            opp_th = clan["top_members"][i].get("townHallLevel", 0)
            diff_sum += my_th - opp_th

        avg_diff = diff_sum / positions

        comparisons.append({
            "opponent": clan["name"],
            "avg_position_diff": round(avg_diff, 2)
        })

    return comparisons



def realtime_war_state(
    me_stars, me_attacks_done, me_max_attacks,
    opp_stars, opp_attacks_done, opp_max_attacks,
    star_distribution_me=None,
    star_distribution_opp=None,
    simulations=10000
):
    """
    Calcula estado real de guerra:
    - Victoria asegurada
    - Derrota asegurada
    - Guerra abierta con probabilidad real (Monte Carlo)
    """

    # Distribución por defecto si no tenemos histórico real
    # (puedes luego hacerlo dinámico por clan)
    if star_distribution_me is None:
        star_distribution_me = {0: 0.05, 1: 0.15, 2: 0.50, 3: 0.30}

    if star_distribution_opp is None:
        star_distribution_opp = {0: 0.10, 1: 0.20, 2: 0.45, 3: 0.25}

    me_left = me_max_attacks - me_attacks_done
    opp_left = opp_max_attacks - opp_attacks_done

    # =============================
    # 🟢 VICTORIA MATEMÁTICA
    # =============================
    if me_stars > opp_stars + (opp_left * 3):
        return {
            "status": "secured_win",
            "win_probability": 100.0,
            "lose_probability": 0.0,
            "draw_probability": 0.0
        }

    # =============================
    # 🔴 DERROTA MATEMÁTICA
    # =============================
    if opp_stars > me_stars + (me_left * 3):
        return {
            "status": "secured_loss",
            "win_probability": 0.0,
            "lose_probability": 100.0,
            "draw_probability": 0.0
        }

    # =============================
    # 🟡 GUERRA ABIERTA → MONTE CARLO
    # =============================

    wins = 0
    losses = 0
    draws = 0


