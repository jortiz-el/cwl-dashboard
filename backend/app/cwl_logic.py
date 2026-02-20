from datetime import datetime, timezone
from .api_client import get_league_group_api, get_war_api, get_clan_info_api, get_normal_summary_api
from .utils import get_league_info
from .leagues import CWL_LEAGUES
import random


def get_league_group(clan_tag):
    return get_league_group_api(clan_tag)

def get_war(war_tag: str):
    return get_war_api(war_tag)

def get_clan_info(clan_tag: str):
    return get_clan_info_api(clan_tag)

def get_normal_summary(clan_tag: str):
    return get_normal_summary_api(clan_tag)

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

    # 🛑 Si no hay tiempo (preparation / no war)
    if not end_time_str:
        return None

    try:
        end_time = datetime.strptime(end_time_str, "%Y%m%dT%H%M%S.000Z")
        end_time = end_time.replace(tzinfo=timezone.utc)
    except Exception:
        return None

    now = datetime.now(timezone.utc)
    delta = end_time - now

    if delta.total_seconds() <= 0:
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

    clan_data = war.get("clan") or {}
    opp_data = war.get("opponent") or {}

    clan_tag_api = clan_data.get("tag")
    opp_tag_api = opp_data.get("tag")

    # 🛑 Si no hay tags, la guerra está en preparación o incompleta
    if not clan_tag_api or not opp_tag_api:
        return []

    if clan_tag_api == clan_tag:
        me = clan_data
    else:
        me = opp_data

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

def get_attack_ranking_data_normal(war, clan_tag):
    clan_data = war.get("clan") or {}
    opp_data = war.get("opponent") or {}

    clan_tag_api = clan_data.get("tag")
    opp_tag_api = opp_data.get("tag")

    # 🛑 Guerra en preparación o inválida
    if not clan_tag_api or not opp_tag_api:
        return []

    if clan_tag_api == clan_tag:
        me = clan_data
    else:
        me = opp_data

    rows = []

    for m in me.get("members", []):
        name = m["name"]
        pos = m["mapPosition"]
        attacks = m.get("attacks", [])

        total_stars = 0
        total_destr = 0
        attack_count = len(attacks)

        if attacks:
            for a in attacks:
                total_stars += a.get("stars", 0)
                total_destr += a.get("destructionPercentage", 0)

            attacked = True
        else:
            attacked = False


        attack_icon = "⚔️" if attacked else "❌"
        #star_icon = "⭐" * stars if stars > 0 else "⚫"

        rows.append({
            "Jugador": name,
            "Pos": pos,

            "Ataques": f"{attack_count}/2",

            "Atacó": attacked,
            "Estado": attack_icon,

            "Estrellas": total_stars,
            "_stars_sort": total_stars,

            "% Destrucción": f"{total_destr:.2f}%",
            "_destr_sort": total_destr,
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
    if war.get("clan", {}).get("tag") == clan_tag:
        me = war["clan"]
        opp = war["opponent"]
    else:
        me = war["opponent"]
        opp = war["clan"]

    team_size = len(me.get("members", []))
    attacks_per_member = war.get("attacksPerMember", 2)


    return {
        "me_tag": me.get("tag"),
        "opp_tag": opp.get("tag"),
        "me_name": me.get("name"),
        "opp_name": opp.get("name"),

        "team_size": team_size,
        "attacks_per_member": attacks_per_member,

        "me_attacks": me.get("attacks", 0),
        "me_max_attacks": team_size * attacks_per_member,
        "me_stars": me.get("stars", 0),
        "me_destr": me.get("destructionPercentage", 0),

        "opp_attacks": opp.get("attacks", 0),
        "opp_max_attacks": team_size * attacks_per_member,
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
                me_stars,
                me_attacks_done,
                me_max_attacks,
                opp_stars,
                opp_attacks_done,
                opp_max_attacks,
                summary["team_size"],
                summary["attacks_per_member"]
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

def get_normal_war_summary(clan_tag):
    war = get_normal_summary(clan_tag)

    if not war:
        return {
            "state": "no_war",
            "time_left": None,
            "summary": None,
            "ranking": [],
            "win_state": None,
            "me_bases": 0,
            "opp_bases": 0
        }

    summary = get_war_summary(war, clan_tag)
    ranking = get_attack_ranking_data_normal(war, clan_tag)

    if war.get("clan", {}).get("tag") == clan_tag:
        me = war["clan"]
        opp = war["opponent"]
    else:
        me = war["opponent"]
        opp = war["clan"]

    me_bases = len(me.get("members", []))
    opp_bases = len(opp.get("members", []))

    win_state = realtime_war_state(
        summary['me_stars'],
        summary['me_attacks'],
        summary['me_max_attacks'],
        summary['opp_stars'],
        summary['opp_attacks'],
        summary['opp_max_attacks'],
        summary['team_size'],
        summary['attacks_per_member']
    )


    return {
        "state": war.get("state"),
        "time_left": get_time_left(war.get("endTime")),
        "summary": summary,
        "ranking": ranking,
        "win_state": win_state,
        "me_bases": me_bases,
        "opp_bases": opp_bases,
        "me": {
            "name": me.get("name"),
            "badge": me.get("badgeUrls", {}).get("small"),
            "tag": me.get("tag")
        },
        "opp": {
            "name": opp.get("name"),
            "badge": opp.get("badgeUrls", {}).get("small"),
            "tag": opp.get("tag")
        }
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
    team_size,
    attacks_per_member,
    star_distribution_me=None,
    star_distribution_opp=None,
    simulations=10000
):

    # =============================
    # ⭐ Máximo real de estrellas
    # =============================
    max_possible_stars = team_size * 3

    # =============================
    # ⚔️ Ataques restantes reales
    # =============================
    me_left = max(0, me_max_attacks - me_attacks_done)
    opp_left = max(0, opp_max_attacks - opp_attacks_done)

    # =============================
    # 🎲 Distribuciones por defecto
    # =============================
    if star_distribution_me is None:
        star_distribution_me = {3: 0.35, 2: 0.30, 1: 0.20, 0: 0.15}

    if star_distribution_opp is None:
        star_distribution_opp = {3: 0.35, 2: 0.30, 1: 0.20, 0: 0.15}

    # =============================
    # 🟢 CIERRES MATEMÁTICOS REALES
    # =============================

    # Ya usamos todos los ataques
    if me_left == 0 and opp_left == 0:
        if me_stars > opp_stars:
            return {"status": "finished_win", "win_probability": 100.0, "lose_probability": 0.0, "draw_probability": 0.0}
        elif me_stars < opp_stars:
            return {"status": "finished_loss", "win_probability": 0.0, "lose_probability": 100.0, "draw_probability": 0.0}
        else:
            return {"status": "finished_draw", "win_probability": 0.0, "lose_probability": 0.0, "draw_probability": 100.0}

    # El rival NO puede alcanzarnos ni haciendo pleno
    if opp_stars + (opp_left * 3) < me_stars:
        return {
            "status": "secured_win",
            "win_probability": 100.0,
            "lose_probability": 0.0,
            "draw_probability": 0.0
        }

    # Nosotros NO podemos alcanzarlos ni haciendo pleno
    if me_stars + (me_left * 3) < opp_stars:
        return {
            "status": "secured_loss",
            "win_probability": 0.0,
            "lose_probability": 100.0,
            "draw_probability": 0.0
        }

    # =============================
    # 🎯 MONTE CARLO REAL
    # =============================
    wins = 0
    losses = 0
    draws = 0

    for _ in range(simulations):

        me_final = me_stars
        opp_final = opp_stars

        # Simular ataques míos
        for _ in range(me_left):
            r = random.random()
            cumulative = 0
            for stars, prob in star_distribution_me.items():
                cumulative += prob
                if r <= cumulative:
                    me_final += stars
                    break

        # Simular ataques rival
        for _ in range(opp_left):
            r = random.random()
            cumulative = 0
            for stars, prob in star_distribution_opp.items():
                cumulative += prob
                if r <= cumulative:
                    opp_final += stars
                    break

        # Limitar al máximo real
        me_final = min(me_final, max_possible_stars)
        opp_final = min(opp_final, max_possible_stars)

        if me_final > opp_final:
            wins += 1
        elif me_final < opp_final:
            losses += 1
        else:
            draws += 1

    return {
        "status": "open_war",
        "win_probability": round((wins / simulations) * 100, 1),
        "lose_probability": round((losses / simulations) * 100, 1),
        "draw_probability": round((draws / simulations) * 100, 1),
    }




