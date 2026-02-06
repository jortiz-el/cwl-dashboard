import os
import time
import requests
import argparse
from dotenv import load_dotenv
from datetime import datetime, timezone
from cwl_logic import get_league_group, find_all_my_wars, parse_end_time, print_attack_ranking 
load_dotenv()

BASE_URL = "https://api.clashofclans.com/v1"
API_KEY = os.getenv("COC_API_KEY")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}

CLAN_TAGS = [
    #"#2R9JPR82Y" # GOD'S ACADEMY
    "#2CPU9J20Q",
    "#2CGYYGP8C",
    "#2JJRCGJC2"
]
REFRESH_SECONDS = 180  # 3 minutos (recomendado)
#SHOW_ALL_ROUNDS = False  # True = mostrar todas las rondas de la CWL


def encode(tag: str) -> str:
    return requests.utils.quote(tag)

def parse_args():
    parser = argparse.ArgumentParser(description="Monitor CWL Clash of Clans")

    parser.add_argument(
        "--all",
        action="store_true",
        help="Mostrar TODAS las rondas de la CWL"
    )

    parser.add_argument(
        "--live",
        action="store_true",
        help="Mostrar solo guerra activa o última finalizada (modo live)"
    )

    return parser.parse_args()

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


def print_war_status(war, round_idx, CLAN_TAG ):
    if war["clan"]["tag"] == CLAN_TAG:
        me = war["clan"]
        opp = war["opponent"]
    else:
        me = war["opponent"]
        opp = war["clan"]

    max_attacks = war.get("teamSize", 0)
    used_attacks = me.get("attacks", 0)
    remaining = max_attacks - used_attacks


    print("\n" + "="*50)
    print(f"🏆 CWL - RONDA {round_idx}")
    print(f"{me['name']}  VS  {opp['name']}")
    print(f"Estado: {war['state']}")
    if "endTime" in war:
        print(f"⏳ Tiempo restante: {get_time_left(war['endTime'])}")
    print("-"*50)
    print(f"⭐ Estrellas: {me['stars']}  -  {opp['stars']}")
    print(f"🏚️ Destrucción: {me['destructionPercentage']:.2f}%  -  {opp['destructionPercentage']:.2f}%")
    print(f"⚔️ Ataques: {me.get('attacks', 0)}  -  {opp.get('attacks', 0)}")
    print(f"🧮 Ataques restantes: {remaining}")
    print("="*50)

def main():
    print("🔴 Monitor CWL MULTI-CLAN (Ctrl+C para salir)")
    print(f"Clanes monitorizados: {', '.join(CLAN_TAGS)}")
    print(f"Refresco cada {REFRESH_SECONDS} segundos\n")

    args = parse_args()

    show_all_rounds = args.all

    if args.live:
        show_all_rounds = False

    while True:
        try:
            for clan_tag in CLAN_TAGS:
                print("\n" + "=" * 70)
                print(f"🏰 CLAN: {clan_tag}")
                print("=" * 70)

                group = get_league_group(clan_tag)
                if not group:
                    print("No hay CWL activa para este clan.")
                    continue

                wars = find_all_my_wars(group, clan_tag)
                if not wars:
                    print("No se encontraron guerras para este clan.")
                    continue

                if show_all_rounds:
                    # 🔵 MODO COMPLETO — TODAS las rondas
                    wars_to_show = sorted(
                        wars,
                        key=lambda x: x[1]  # ordenar por round_idx
                    )
                    print("🔵 MODO COMPLETO: Mostrando TODAS las rondas de la CWL")

                else:
                    # 🟢 MODO LIVE — solo activa o última finalizada
                    active_wars = [(w, r) for w, r in wars if w["state"] == "inWar"]

                    if active_wars:
                        wars_to_show = active_wars
                    else:
                        ended_wars = [(w, r) for w, r in wars if w["state"] == "warEnded"]

                        if not ended_wars:
                            print("ℹ️ No hay guerras activas ni finalizadas aún.")
                            continue

                        ended_wars.sort(
                            key=lambda x: parse_end_time(x[0]) or datetime.min.replace(tzinfo=timezone.utc),
                            reverse=True
                        )

                        wars_to_show = [ended_wars[0]]
                        print("🟢 MODO LIVE: No hay guerra activa. Mostrando última finalizada.")


                for war, round_idx in wars_to_show:
                    print_war_status(war, round_idx, clan_tag)
                    print_attack_ranking(war, clan_tag)


            print(f"\n🕒 Última actualización: {time.strftime('%H:%M:%S')}")
            time.sleep(REFRESH_SECONDS)

        except KeyboardInterrupt:
            print("\n🛑 Monitor detenido por el usuario.")
            break
        except Exception as e:
            print("❌ Error:", e)
            time.sleep(60)


if __name__ == "__main__":
    main()
