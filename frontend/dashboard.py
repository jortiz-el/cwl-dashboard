import streamlit as st
from datetime import datetime
import pandas as pd
import requests
import os
import re
from collections import defaultdict
import copy
import random

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000") # local

import streamlit as st

@st.cache_data(ttl=60, show_spinner=False)
def get_full_summary_api(clan_tag):
    try:
        r = requests.get(
            f"{BACKEND_URL}/cwl/full-summary",
            params={
                "clan_tag": clan_tag
            },
            timeout=60,
        )

        if r.status_code == 403:
            st.warning(f"🔒 El clan {clan_tag} es privado o no tienes acceso.")
            return None

        if r.status_code == 404:
            st.warning(f"❌ Clan {clan_tag} no encontrado.")
            return None

        if r.status_code >= 500:
            # Puede ser NO CWL, no necesariamente error real
            try:
                data = r.json()
                return data
            except Exception:
                st.error(f"🚨 Error del servidor para clan {clan_tag}. es posible que el clan no este publico")
            return None

        r.raise_for_status()
        return r.json()

    except requests.exceptions.Timeout:
        st.error(f"⏱️ Timeout al consultar clan {clan_tag}.")
        return None

    except requests.exceptions.RequestException as e:
        st.error(f"⚠️ Error de red para clan {clan_tag}.")
        st.caption(str(e))
        return None


def get_war_summary_api(clan_tag):
    r = requests.get(
        f"{BACKEND_URL}/cwl/war-summary",
        params={"clan_tag": clan_tag},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()

def get_league_group_api(clan_tag):
    r = requests.get(
        f"{BACKEND_URL}/cwl/league-group",
        params={"clan_tag": clan_tag},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()

@st.cache_data(ttl=60)
def get_clan_info_api(clan_tag):
    try:
        r = requests.get(
            f"{BACKEND_URL}/clan/info",
            params={"clan_tag": clan_tag},
            timeout=30
        )
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            st.warning(f"⚠️ {data['error']}")
            return None
        return data
    except requests.exceptions.RequestException as e:
        st.error(f"⚠️ No se pudo cargar info del clan {clan_tag}")
        st.caption(str(e))
        return None

@st.cache_data(ttl=30)
def get_normal_war_api(clan_tag):
    try:
        r = requests.get(
            f"{BACKEND_URL}/war/normal-summary",
            params={"clan_tag": clan_tag},
            timeout=30
        )
        r.raise_for_status()
        return r.json()
    except:
        return None


clans_list = [
    {"name": "GOD'S ACADEMY", "tag": "#2R9JPR82Y"},
    {"name": "LOS EXÓTICOS", "tag": "#2L8V8CPLV"},
    {"name": "TITO TEAM", "tag": "#2CP9C2VJ0"},
    {"name": "M1 Bellum", "tag": "#2RUQCC9RP"},
    {"name": "M1 Coco Bellum ", "tag": "#2JL989J2C"},
    {"name": "M2 Gods Empire", "tag": "#2GCVLQPVQ"},
    {"name": "M2 No Somos Mancos 3", "tag": "#2R9J9Q029"},
    {"name": "C3 Los Chunguitos", "tag": "#P0CJRRQ"},
    {"name": "C3 NoSomosMancos", "tag": "#28U2CV0PV"},
    {"name": "⚡ASGARD⚡", "tag": "#8L8PPVYU8"},
    {"name": "PULP FICTION", "tag": "#2CPU9J20Q"},
    {"name": "PULP FICTION II", "tag": "#2CGYYGP8C"},
    {"name": "PULP FICTION III", "tag": "#2JJRCGJC2"}
]

CLAN_TAGS = [
    "#2R9JPR82Y",
    # añade más
]

def parse_time_left_to_minutes(time_left_str):
    """
    Convierte '5h 12m' o '3h' o '45m' a minutos
    """
    hours = 0
    minutes = 0

    h_match = re.search(r"(\d+)h", time_left_str)
    m_match = re.search(r"(\d+)m", time_left_str)

    if h_match:
        hours = int(h_match.group(1))

    if m_match:
        minutes = int(m_match.group(1))

    return hours * 60 + minutes
# 🎛️ Selector modo Guerra Normal o CWL
st.sidebar.title("⚙️ Modo de Guerra")
war_mode = st.sidebar.radio(
    "Selecciona tipo de guerra",
    ["CWL", "Guerra Normal"]
)

st.set_page_config(page_title="War Dashboard", layout="wide")

if war_mode == "CWL":
    st.title("🏆 CWL Dashboard")
else:
    st.title("⚔️ Guerra Normal Dashboard")


if "modal_clan_tag" not in st.session_state:
    st.session_state.modal_clan_tag = None


# 🎛️ Selector LIVE / ALL
show_all_rounds = False

if war_mode == "CWL":
    mode = st.sidebar.radio(
        "Modo CWL",
        ["LIVE (solo activa / última)", "ALL (todas las rondas)"]
    )
    show_all_rounds = mode.startswith("ALL")


#st.caption(f"Modo actual: {'ALL' if show_all_rounds else 'LIVE'}")

# Mostrar un multiselect en la web
selected = st.multiselect(
    "Selecciona los clanes a monitorizar",
    options=[clan["name"] for clan in clans_list],
    default=[clans_list[0]["name"]]  # selecciona el primero por defecto
)

# Filtrar los clanes seleccionados
selected_clans = [clan for clan in clans_list if clan["name"] in selected]

# botones de seleccion para listar clanes

#st.write("Selecciona un clan para monitorizar:")
#cols = st.columns(len(clans_list))
#for i, clan in enumerate(clans_list):
#    if cols[i].button(clan["name"]):
#        st.session_state["selected_clan"] = clan["tag"]

if not selected_clans:
    st.warning("⚠️ Selecciona al menos un clan para mostrar el dashboard.")
    st.stop()



def render_cwl_tab(clan):

    #for clan in selected_clans:
    clan_tag = clan['tag'] #logica para seleccion de clanes desde el dropdownlist
    #clan_tag = st.session_state["selected_clan"] #logica para seleccion de clanes desde botones
    st.header(f"🏰 Clan {clan_tag}")

#with st.spinner("🔄 Actualizando datos del clan..."):
    data = get_full_summary_api(clan_tag)

    if not data:
        st.info(f"⏭️ Saltando clan {clan['name']}")
        return

    # 🏆 Caso: NO hay CWL activa (guerra normal o fuera de temporada)
    if data.get("no_cwl"):
        st.info(f"ℹ️ {clan['name']}: no tiene CWL activa actualmente.(posible guerra normal en curso).")
        return

    # calculo para Ranking de fuerza del grupo 
    strength = data.get("strength_ranking", [])
    position_adv = data.get("position_advantage", [])    

    # obtener datos de la liga
    league = data.get("league")

    # obtener datos de las guerras
    wars = data.get("wars", [])

    if not wars:
        st.warning("No hay datos de guerras CWL para este clan.")
        return

    player_history = defaultdict(lambda: {
        "attacks": 0,
        "Estrellas": 0,
        "% Destrucción": 0.0,
        "fails": 0,
        "no_attack": 0,
        "rounds": 0,
    })

    for war_hist in wars:
        for p in war_hist["ranking"]:
            name = p["Jugador"]

            player_history[name]["rounds"] += 1

            if p["Atacó"]:
                player_history[name]["attacks"] += 1
                stars = int(p["_stars_sort"])  # SIEMPRE int real
                destr_raw = p["% Destrucción"]
                if isinstance(destr_raw, str):
                    destr = float(destr_raw.replace("%", "").strip())
                else:
                    destr = float(destr_raw)

                player_history[name]["Estrellas"] += stars
                player_history[name]["% Destrucción"] += destr


                if stars == 0:
                    player_history[name]["fails"] += 1
            else:
                player_history[name]["no_attack"] += 1




    # 🧠 Lógica LIVE vs ALL
    if show_all_rounds:
        wars_to_show = sorted(wars, key=lambda w: w["round"])
        st.info("Mostrando TODAS las rondas")
    else:
        active = [w for w in wars if w["state"] == "inWar"]
        if active:
            wars_to_show = active
        else:
            ended = [w for w in wars if w["state"] == "warEnded"]
            ended.sort(key=lambda w: w.get("end_time") or "", reverse=True)
            wars_to_show = ended[:1]
            st.info("Mostrando última guerra finalizada")

    # Inicializamos dict de modales si no existe
    clan_key = clan_tag.replace("#", "")
    if "modals_open_by_clan" not in st.session_state:
        st.session_state["modals_open_by_clan"] = {}

    if clan_key not in st.session_state["modals_open_by_clan"]:
        st.session_state["modals_open_by_clan"][clan_key] = {}


    # 🖥️ Renderizar guerras
    for war in wars_to_show:
        summary = war["summary"]

        me_badge = war["me"]["badge"]
        opp_badge = war["opp"]["badge"]

        round_idx = war["round"]

        # Columnas para la presentación de la guerra
        col_round, col_me_name, col_me_logo,  col_vs, col_opp_logo, col_opp_name = st.columns([3, 2, 1, 1, 1, 2])

        # Texto Ronda 
        with col_round:
            st.markdown(f"<h2>🏆 Ronda {round_idx}</h2>", unsafe_allow_html=True)
        
        # Nombre clan propio centrado verticalmente
        with col_me_name:
            st.markdown(f"<h3 style='text-align:center; margin:0;'>{summary['me_name']}</h3>", unsafe_allow_html=True)
        # Logo clan propio
        with col_me_logo:
            if me_badge:
                st.markdown(
                    f"""
                    <div style="display:flex; justify-content:center;">
                        <img src="{me_badge}" width="60">
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        # VS
        with col_vs:
            st.markdown("<h3 style='text-align:center; margin:0;'>🆚</h3>", unsafe_allow_html=True)
        
        # Logo clan rival
        with col_opp_logo:
            if opp_badge:
                st.markdown(
                    f"""
                    <div style="display:flex; justify-content:center;">
                        <img src="{opp_badge}" width="60">
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # Nombre clan rival centrado verticalmente
        with col_opp_name:
            st.markdown(f"<h3 style='text-align:center; margin:0;'>{summary['opp_name']}</h3>", unsafe_allow_html=True)
            # Botón para abrir modal de scouting (key único por ronda y clan)
            button_key = f"modal_btn_{summary['opp_tag'].replace('#','')}_{round_idx}"
            if st.button("🔎 Info Clan Enemigo", key=button_key):
                st.session_state["modals_open_by_clan"][clan_key][round_idx] = summary["opp_tag"]


        # ==========================
        # 🏰 MODAL SCOUTING CLAN
        # ==========================
        if round_idx in st.session_state["modals_open_by_clan"][clan_key]:
            selected_tag = st.session_state["modals_open_by_clan"][clan_key][round_idx]
            safe_key = selected_tag.replace("#", "")

            st.markdown("---")
            st.markdown(f"## 🔎 Clan Scouting — Ronda {round_idx}", unsafe_allow_html=True)

            # Botón cerrar centrado
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                close_key = f"close_modal_{safe_key}_{round_idx}"
                if st.button("❌ Cerrar", key=close_key):
                    del st.session_state["modals_open_by_clan"][clan_key][round_idx]
                    st.rerun()

            # Info del clan
            clan_info = get_clan_info_api(selected_tag)
            if not clan_info or clan_info.get("error"):
                st.warning("⚠️ Este clan es privado o no se puede acceder a más información.")
                if clan_info and "tag" in clan_info:
                    st.write(f"🏷️ Tag: {clan_info['tag']}")
                st.markdown("---")
            else:
                col_logo, col_stats, col_misc = st.columns([1, 2, 2])
                with col_logo:
                    badge_url = clan_info.get("badgeUrls", {}).get("large") or clan_info.get("badge")
                    if badge_url:
                        st.image(badge_url, width=120)
                with col_stats:
                    st.markdown(f"### {clan_info.get('name')}")
                    st.write(f"🏷️ Tag: {clan_info.get('tag')}")
                    st.write(f"🏆 Nivel: {clan_info.get('clanLevel')}")
                    st.write(f"👥 Miembros: {clan_info.get('members')}/50")
                    st.write(f"🔰 Clan Points: {clan_info.get('clanPoints')}")
                    st.write(f"⚔️ War Wins: {clan_info.get('warWins')}")
                    st.write(f"🔓 Tipo: {clan_info.get('type')}")
                    st.write(f"🕒 Frecuencia de guerras: {clan_info.get('warFrequency')}")
                with col_misc:
                    location = clan_info.get("location")
                    if location:
                        country_name = location.get("name")
                        country_code = location.get("countryCode")
                        if country_code:
                            flag_url = f"https://flagcdn.com/24x18/{country_code.lower()}.png"
                            st.markdown(
                                f"🌍 País: {country_name} <img src='{flag_url}' width='24' style='vertical-align:middle; margin-left:5px;'>",
                                unsafe_allow_html=True
                            )
                        else:
                            st.write(f"🌍 País: {country_name}")
                    else:
                        st.write("🌍 País: Desconocido")

                    chat_lang = clan_info.get("chatLanguage")
                    if chat_lang:
                        st.write(f"🗣️ Idioma: {chat_lang.get('name')}")
                    league = clan_info.get("league")
                    if league:
                        st.write(f"🏅 Liga CWL: {league.get('name')}")
                        if league.get("iconUrls", {}).get("small"):
                            st.image(league["iconUrls"]["small"], width=40)
                    description = clan_info.get("description")
                    if description:
                        st.write(f"📝 Descripción: {description}")

            st.markdown("---")


        #if league:
        #    col_l1, col_l2 = st.columns([1, 5])

        #    with col_l1:
        #        if league.get("logo"):
        #            st.image(
        #                f"{BACKEND_URL}{league['logo']}",
        #                width=60
        #            )

        #    with col_l2:
        #        st.markdown(f"🏅 **Liga CWL:** {league['name']}**")

        # 🏅 informacion de Liga 
        #if league:
        #    st.write(f"🏅 **Liga ID:** {league}**")  
        #    st.write(f"🏅 **Liga CWL:** {league['name']}**")     
        #st.subheader(f"🏆 Ronda {round_idx} — {summary['me_name']} 🆚 {summary['opp_name']}")

        st.caption(f"⚔️ Tamaño oficial de guerra CWL: {data.get('team_size')} vs {data.get('team_size')}")
        st.write(f"🛡️ Estado: **{war['state']}**") 
        st.write(f"⏳ Tiempo restante: **{war['time_left']}**")

        # 🎯 Probabilidad de victoria
        win_data = war.get("win_state", {})
        status = win_data.get("status")

        if status == "final_win":
            st.success("🏆 RESULTADO FINAL: VICTORIA")

        elif status == "final_loss":
            st.error("💀 RESULTADO FINAL: DERROTA")

        elif status == "final_draw":
            st.info("🤝 RESULTADO FINAL: EMPATE")

        elif status == "secured_win":
            st.success("🟢 Victoria matemáticamente asegurada")

        elif status == "secured_loss":
            st.error("🔴 Derrota matemáticamente asegurada")

        elif status == "open":
            st.warning(
                f"🟡 Guerra abierta\n"
                f"🎯 Victoria: {win_data['win_probability']}% | "
                f"❌ Derrota: {win_data['lose_probability']}% | "
                f"🤝 Empate: {win_data['draw_probability']}%"
            )



        # ⏳ Barra de progreso de guerra (CWL = 24h por ronda)
        if war.get("time_left") and war["state"] == "inWar":
            try:
                minutes_left = parse_time_left_to_minutes(war["time_left"])

                TOTAL_WAR_MINUTES = 24 * 60  # CWL = 24h
                minutes_elapsed = TOTAL_WAR_MINUTES - minutes_left

                progress = min(max(minutes_elapsed / TOTAL_WAR_MINUTES, 0), 1)

                st.progress(progress)
                st.caption(f"⏳ Progreso de guerra: {int(progress * 100)}%")

            except Exception as e:
                st.caption("⏳ No se pudo calcular el progreso de la guerra.")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "⚔️ Ataques",
                f"{summary['me_attacks']}/{summary['me_max_attacks']}",
                f"{summary['opp_attacks']}/{summary['opp_max_attacks']}"
            )

        with col2:
            st.metric(
                "⭐ Estrellas",
                f"{summary['me_stars']} - {summary['opp_stars']}",
                f"{summary['me_stars'] - summary['opp_stars']:+}"
            )

        with col3:
            st.metric(
                "🏚️ Destrucción total",
                f"{summary['me_destr']:.2f}% - {summary['opp_destr']:.2f}%",
                f"{summary['me_destr'] - summary['opp_destr']:+.2f}%"
            )

        # 📊 Ranking
        ranking = war["ranking"]
        df = pd.DataFrame(ranking)

        def highlight_no_attack(row):
            styles = [""] * len(row)

            if row["Atacó"] is False:
                # Rojo suave, NO tapa el texto
                styles = ["background-color: rgba(255, 0, 0, 0.15)"] * len(row)

            return styles
        
        df = df.sort_values(
            by=["_stars_sort", "_destr_sort"],
            ascending=[False, False]
        )

        df = df.drop(columns=["_stars_sort", "_destr_sort"])

        styled_df = (
            df.style
            .apply(highlight_no_attack, axis=1)
        )


        st.dataframe(styled_df, use_container_width=True)
    
    # =========================
    # 📈 HISTORIAL POR JUGADOR (CWL COMPLETA)
    # =========================

    st.subheader("📈 Historial por jugador (CWL completa)")

    rows = []

    for name, stats in player_history.items():
        attacks = stats["attacks"]
        rounds = stats["rounds"]

        avg_stars = stats["Estrellas"] / attacks if attacks else 0
        avg_destr = stats["% Destrucción"] / attacks if attacks else 0

        rows.append({
            "Jugador": name,
            "Ataques": attacks,
            "Rondas": rounds,
            "No atacó": stats["no_attack"],
            "⭐ Total": stats["Estrellas"],
            "⭐ Media": round(avg_stars, 2),
            "% Media": round(avg_destr, 2),
            "0⭐ Fails": stats["fails"],
        })

    hist_df = pd.DataFrame(rows)

    # 🔹 Ordenar por Ataques descendente
    #hist_df = hist_df.sort_values(by=["Ataques"], ascending=False)

    hist_df = hist_df.sort_values(
        by=["⭐ Media", "% Media"],
        ascending=[False, False]
    )
    
    st.dataframe(hist_df, use_container_width=True)

    # =========================
    # 🏅 BONUS DE GUERRA (CWL)
    # =========================
    if st.button("👁️ Mostrar recomendación de bonus", key=f"bonus_btn_{clan_tag}"):
        st.subheader("🏅 Recomendación Bonus de Guerra (CWL)")

        eligible_players = []

        for name, stats in player_history.items():
            # ❌ Excluir si no atacó alguna ronda
            if stats["no_attack"] > 0:
                continue

            eligible_players.append({
                "Jugador": name,
                "Ataques": stats["attacks"],
                "⭐ Total": stats["Estrellas"],
                "% Total": round(stats["% Destrucción"], 2),
                "0⭐ Fails": stats["fails"],
            })

        bonus_df = pd.DataFrame(eligible_players)

        if bonus_df.empty:
            st.warning("No hay jugadores elegibles para bonus (todos deben haber atacado).")
        else:
            bonus_df = bonus_df.sort_values(
                by=["Ataques", "⭐ Total", "% Total", "0⭐ Fails"],
                ascending=[False, False, False, True]
            )

            st.caption("Ordenado por: Ataques → Estrellas → % Destrucción → Menos 0⭐")

            #st.dataframe(bonus_df.reset_index(drop=True), use_container_width=True)

            st.success("🎯 TOP candidatos a bonus:")
            for i, row in bonus_df.head(10).iterrows():
                st.write(
                    f"#{i+1} — {row['Jugador']} | "
                    f"Ataques: {row['Ataques']} | "
                    f"⭐ {row['⭐ Total']} | "
                    f"{row['% Total']}%"
                )
    else:
        st.caption("🔒 Recomendación de bonus oculta. Pulsa el botón para mostrar.")

    # =========================
    # 📈 RANKING DE CLANES (CWL COMPLETA)
    # =========================
    if strength:
        st.subheader("📊 Ranking de Fuerza Teórica (CWL Group)")

        df_strength = pd.DataFrame(strength)

        df_display = df_strength[["rank", "name", "top_avg_th", "weighted_score"]]
        df_display["top_avg_th"] = df_display["top_avg_th"].map(lambda x: f"{x:.2f}")

        def highlight_my_clan(row):
            if df_strength.loc[row.name, "is_me"]:
                return ["background-color: rgba(128,128,128,0.2)"] * len(row)
            return [""] * len(row)

        styled_df = df_display.style.apply(highlight_my_clan, axis=1)

        st.dataframe(styled_df, use_container_width=True)            


    # mostrar ventaja estructural vs clanes
    if position_adv:
        st.subheader("⚔️ Ventaja estructural por posición")

        df_pos = pd.DataFrame(position_adv)

        st.dataframe(df_pos, use_container_width=True)

        for row in position_adv:
            diff = row["avg_position_diff"]

            if diff > 0.3:
                st.success(f"🟢 Ventaja vs {row['opponent']}")
            elif diff < -0.3:
                st.error(f"🔴 Desventaja vs {row['opponent']}")
            else:
                st.warning(f"🟡 Guerra equilibrada vs {row['opponent']}")   


# ==========================
#GUERRA NORMAL
# ==========================

# REEMPLAZAR COMPLETAMENTE la función simulate_normal_war_pro POR ESTAS NUEVAS FUNCIONES
# (colócalas justo antes de def render_normal_war_tab(clan): )

def get_star_probs(delta):
    """Probabilidades realistas [P0, P1, P2, P3] basadas en stats comunitarias (tunables)"""
    if delta >= 2:
        return [0.00, 0.00, 0.00, 1.00]
    elif delta == 1:
        return [0.00, 0.05, 0.10, 0.85]   # menos 3★ que antes
    elif delta == 0:
        return [0.10, 0.20, 0.30, 0.40]   # solo 40% 3★ en mirror (realista en guerras cerradas)
    elif delta == -1:
        return [0.15, 0.30, 0.40, 0.15]
    elif delta == -2:
        return [0.30, 0.40, 0.25, 0.05]
    else:
        return [0.60, 0.30, 0.09, 0.01]

def expected_additional(att_th, base_th, rem_stars):
    """Expected stars adicionales (capped por rem)"""
    delta = att_th - base_th
    probs = get_star_probs(delta)
    e = sum(min(s, rem_stars) * p for s, p in enumerate(probs))
    return e

def sample_stars(att_th, base_th):
    """Sample real 0-3 estrellas"""
    delta = att_th - base_th
    probs = get_star_probs(delta)
    r = random.random()
    cum = 0.0
    for s in range(4):
        cum += probs[s]
        if r < cum:
            return s
    return 0

def simulate_additional_stars(att_ths_list, bases_list):
    """Simula estrellas adicionales: attackers fuertes atacan bases óptimas primero"""
    bases = copy.deepcopy(bases_list)
    att_ths = sorted(att_ths_list, reverse=True)  # TH altos primero
    total_add = 0
    for att_th in att_ths:
        avail_bases = [i for i, b in enumerate(bases) if b['rem_stars'] > 0]
        if not avail_bases:
            break
        # Elige MEJOR base (max expected)
        best_idx = max(
            avail_bases,
            key=lambda i: expected_additional(att_th, bases[i]['th'], bases[i]['rem_stars'])
        )
        exp_val = expected_additional(att_th, bases[best_idx]['th'], bases[best_idx]['rem_stars'])
        if exp_val <= 0:
            continue
        # Sample y aplica
        got_stars = sample_stars(att_th, bases[best_idx]['th'])
        add = min(got_stars, bases[best_idx]['rem_stars'])
        bases[best_idx]['rem_stars'] -= add
        total_add += add
    return total_add

def estimate_normal_war_probs(opp_bases, me_bases, my_att_ths, opp_att_ths,my_stars_current,opp_stars_current, num_sims=8000):
    """Monte Carlo principal: % win/draw/lose"""
    my_current_total = sum(b['stars'] for b in opp_bases)
    opp_current_total = sum(b['stars'] for b in me_bases)
    
    # Prepara rem_stars para cada sim
    opp_bases_rem = [{'th': b['th'], 'rem_stars': 3 - b['stars']} for b in opp_bases]
    me_bases_rem = [{'th': b['th'], 'rem_stars': 3 - b['stars']} for b in me_bases]
    
    wins = ties = losses = 0
    for _ in range(num_sims):
        my_add = simulate_additional_stars(my_att_ths[:], opp_bases_rem[:])
        opp_add = simulate_additional_stars(opp_att_ths[:], me_bases_rem[:])
        
        # Pequeño ruido para evitar empates forzados (simula fallos impredecibles)
        my_add += random.uniform(-0.5, 0.5)
        opp_add += random.uniform(-0.5, 0.5)
        
        final_my = my_stars_current + my_add
        final_opp = opp_stars_current + opp_add

        
        if final_my > final_opp:
            wins += 1
        elif final_my < final_opp:
            losses += 1
        else:
            ties += 1

    
    total = num_sims
    return {
        "win": round(wins / total * 100, 1),
        "draw": round(ties / total * 100, 1),
        "lose": round(losses / total * 100, 1)
    }


# ==========================
# Guerra Normal render
# ==========================
def render_normal_war_tab(clan):
    clan_tag = clan['tag']
    st.header(f"🏰 Clan — {clan_tag}")

    war = get_normal_war_api(clan_tag)

    if not war:
        st.info("No hay guerra activa.")
        return
    elif war.get("state") == "notInWar":
        st.info("🏖️ El clan no está actualmente en guerra.")
        return


    summary = war.get("summary")

    if not summary:
        st.warning("No se pudo cargar el resumen de guerra.")
        return

    full_war = war.get("full_war_data")
    if not full_war or "clan" not in full_war or "opponent" not in full_war:
        st.error("Error grave: El backend no devolvió la guerra completa con 'full_war_data'. Contacta al dev del backend.")
        st.json(war)  # muestra todo para debug
        return

    me_badge = war["me"]["badge"]
    opp_badge = war["opp"]["badge"]
    # Columnas para la presentación de la guerra
    col_me_name, col_me_logo,  col_vs, col_opp_logo, col_opp_name = st.columns([ 2, 1, 1, 1, 2])

    
    # Nombre clan propio centrado verticalmente
    with col_me_name:
        st.markdown(f"<h3 style='text-align:center; margin:0;'>{summary['me_name']}</h3>", unsafe_allow_html=True)
    # Logo clan propio
    with col_me_logo:
        if me_badge:
            st.markdown(
                f"""
                <div style="display:flex; justify-content:center;">
                    <img src="{me_badge}" width="60">
                </div>
                """,
                unsafe_allow_html=True
            )
    # VS
    with col_vs:
        st.markdown("<h3 style='text-align:center; margin:0;'>🆚</h3>", unsafe_allow_html=True)
    
    # Logo clan rival
    with col_opp_logo:
        if opp_badge:
            st.markdown(
                f"""
                <div style="display:flex; justify-content:center;">
                    <img src="{opp_badge}" width="60">
                </div>
                """,
                unsafe_allow_html=True
            )
    


    # Nombre clan rival centrado verticalmente
    with col_opp_name:
        st.markdown(f"<h3 style='text-align:center; margin:0;'>{summary['opp_name']}</h3>", unsafe_allow_html=True)
        # 🔥 BOTÓN SCOUTING GUERRA NORMAL
        button_key = f"normal_scout_{clan_tag.replace('#','')}"
        session_key = f"normal_scout_open_{clan_tag.replace('#','')}"      
        if st.button("🔎 Info Clan Enemigo", key=button_key):
            st.session_state[session_key] = war["opp"]["tag"]

    if session_key in st.session_state:
        opp_tag = st.session_state[session_key]

        st.markdown("---")
        st.markdown(f"## 🔎 Clan Scouting ", unsafe_allow_html=True)

        close_btn_key = f"close_normal_scout_{clan_tag.replace('#','')}"
        if st.button("❌ Cerrar", key=close_btn_key):
            del st.session_state[session_key]
            st.rerun()
            
        # Info del clan
        clan_info = get_clan_info_api(opp_tag)
        if not clan_info or clan_info.get("error"):
            st.warning("⚠️ Este clan es privado o no se puede acceder a más información.")
            if clan_info and "tag" in clan_info:
                st.write(f"🏷️ Tag: {clan_info['tag']}")
            st.markdown("---")
        else:
            col_logo, col_stats, col_misc = st.columns([1, 2, 2])
            with col_logo:
                badge_url = clan_info.get("badgeUrls", {}).get("large") or clan_info.get("badge")
                if badge_url:
                    st.image(badge_url, width=120)
            with col_stats:
                st.markdown(f"### {clan_info.get('name')}")
                st.write(f"🏷️ Tag: {clan_info.get('tag')}")
                st.write(f"🏆 Nivel: {clan_info.get('clanLevel')}")
                st.write(f"👥 Miembros: {clan_info.get('members')}/50")
                st.write(f"🔰 Clan Points: {clan_info.get('clanPoints')}")
                st.write(f"⚔️ War Wins: {clan_info.get('warWins')}")
                st.write(f"🔓 Tipo: {clan_info.get('type')}")
                st.write(f"🕒 Frecuencia de guerras: {clan_info.get('warFrequency')}")
            with col_misc:
                location = clan_info.get("location")
                if location:
                    country_name = location.get("name")
                    country_code = location.get("countryCode")
                    if country_code:
                        flag_url = f"https://flagcdn.com/24x18/{country_code.lower()}.png"
                        st.markdown(
                            f"🌍 País: {country_name} <img src='{flag_url}' width='24' style='vertical-align:middle; margin-left:5px;'>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.write(f"🌍 País: {country_name}")
                else:
                    st.write("🌍 País: Desconocido")

                chat_lang = clan_info.get("chatLanguage")
                if chat_lang:
                    st.write(f"🗣️ Idioma: {chat_lang.get('name')}")
                league = clan_info.get("league")
                if league:
                    st.write(f"🏅 Liga CWL: {league.get('name')}")
                    if league.get("iconUrls", {}).get("small"):
                        st.image(league["iconUrls"]["small"], width=40)
                description = clan_info.get("description")
                if description:
                    st.write(f"📝 Descripción: {description}")

        st.markdown("---")
    
    st.write(f"🛡️ Estado: **{war.get('state')}**")
    st.write(f"⏳ Tiempo restante: **{war.get('time_left')}**")


    # ==========================
    # 🎯 Probabilidad de victoria realista
    # ==========================

    me_attacks_done = summary.get("me_attacks", 0)
    me_max_attacks = summary.get("me_max_attacks", 0)

    opp_attacks_done = summary.get("opp_attacks", 0)
    opp_max_attacks = summary.get("opp_max_attacks", 0)

    me_attacks_left = me_max_attacks - me_attacks_done
    opp_attacks_left = opp_max_attacks - opp_attacks_done

    # Ataques ya realizados
    me_attacks_done = summary.get("me_attacks", 0)
    opp_attacks_done = summary.get("opp_attacks", 0)

    # Calcula atacantes restantes
    me_attackers = []
    for member in full_war["clan"]["members"]:
        attacks_made = len(member.get("attacks", []))
        attacks_left = max(0, 2 - attacks_made)
        if attacks_left > 0:
            me_attackers.extend([member.get("townHallLevel", 12)] * attacks_left)

    opp_attackers = []
    for member in full_war["opponent"]["members"]:
        attacks_made = len(member.get("attacks", []))
        attacks_left = max(0, 2 - attacks_made)
        if attacks_left > 0:
            opp_attackers.extend([member.get("townHallLevel", 12)] * attacks_left)


    # =====================================
    # NUESTRAS BASES (atacadas por el rival)
    # =====================================
    me_bases = []
    me_base_stars = {}  # tag → estrellas (capeadas en cada suma)

    # Recolectamos y capeamos EN CADA ATAQUE
    for opp_member in full_war["opponent"]["members"]:
        for atk in opp_member.get("attacks", []):
            def_tag = atk.get("defenderTag")
            if def_tag:
                if def_tag not in me_base_stars:
                    me_base_stars[def_tag] = 0
                # Capeo inmediato: nunca suma más de 3 en total
                added = atk.get("stars", 0)
                me_base_stars[def_tag] = min(3, me_base_stars[def_tag] + added)

    # Construimos la lista oficial (solo miembros reales del clan)
    for member in full_war["clan"]["members"]:
        tag = member["tag"]
        stars_received = me_base_stars.get(tag, 0)
        me_bases.append({
            "stars": stars_received,
            "th": member.get("townHallLevel", 12)
        })

    # Forzamos ajuste global si hay desfase (seguridad extra)
    calculated_me = sum(b['stars'] for b in me_bases)
    expected_me = summary['opp_stars']
    if calculated_me != expected_me:
        #st.warning(f"Desfase detectado en nuestras bases: calculado {calculated_me} vs esperado {expected_me}. Ajustando enteros...")
        diff = expected_me - calculated_me  # puede ser positivo o negativo
        if diff != 0:
            # Ordenamos bases con estrellas >0 para ajustar primero las que tienen más margen
            adjustable_bases = [b for b in me_bases if b['stars'] < 3 and b['stars'] > 0]
            adjustable_bases.sort(key=lambda b: b['stars'], reverse=(diff > 0))  # si diff >0, subimos las bajas primero
            
            abs_diff = abs(diff)
            adjusted = 0
            i = 0
            while adjusted < abs_diff and i < len(adjustable_bases):
                b = adjustable_bases[i]
                if diff > 0:  # necesitamos subir
                    if b['stars'] < 3:
                        b['stars'] += 1
                        adjusted += 1
                elif diff < 0:  # necesitamos bajar
                    if b['stars'] > 0:
                        b['stars'] -= 1
                        adjusted += 1
                i += 1
            
            # Si aún queda diff (raro), ajustamos en cualquier base
            remaining = abs_diff - adjusted
            if remaining > 0:
                for b in me_bases:
                    if diff > 0 and b['stars'] < 3:
                        b['stars'] += 1
                        remaining -= 1
                        if remaining == 0: break
                    elif diff < 0 and b['stars'] > 0:
                        b['stars'] -= 1
                        remaining -= 1
                        if remaining == 0: break

    # =====================================
    # BASES ENEMIGAS (atacadas por nosotros)
    # =====================================
    opp_bases = []
    opp_base_stars = {}

    for my_member in full_war["clan"]["members"]:
        for atk in my_member.get("attacks", []):
            def_tag = atk.get("defenderTag")
            if def_tag:
                if def_tag not in opp_base_stars:
                    opp_base_stars[def_tag] = 0
                added = atk.get("stars", 0)
                opp_base_stars[def_tag] = min(3, opp_base_stars[def_tag] + added)

    for member in full_war["opponent"]["members"]:
        tag = member["tag"]
        stars_received = opp_base_stars.get(tag, 0)
        opp_bases.append({
            "stars": stars_received,
            "th": member.get("townHallLevel", 12)
        })

    calculated_opp = sum(b['stars'] for b in opp_bases)
    expected_opp = summary['me_stars']
    if calculated_opp != expected_opp:
        #st.warning(f"Desfase detectado en bases enemigas: calculado {calculated_opp} vs esperado {expected_opp}. Ajustando enteros...")
        diff = expected_opp - calculated_opp
        if diff != 0:
            adjustable_bases = [b for b in opp_bases if b['stars'] < 3 and b['stars'] > 0]
            adjustable_bases.sort(key=lambda b: b['stars'], reverse=(diff > 0))
            
            abs_diff = abs(diff)
            adjusted = 0
            i = 0
            while adjusted < abs_diff and i < len(adjustable_bases):
                b = adjustable_bases[i]
                if diff > 0 and b['stars'] < 3:
                    b['stars'] += 1
                    adjusted += 1
                elif diff < 0 and b['stars'] > 0:
                    b['stars'] -= 1
                    adjusted += 1
                i += 1
            
            remaining = abs_diff - adjusted
            if remaining > 0:
                for b in opp_bases:
                    if diff > 0 and b['stars'] < 3:
                        b['stars'] += 1
                        remaining -= 1
                        if remaining == 0: break
                    elif diff < 0 and b['stars'] > 0:
                        b['stars'] -= 1
                        remaining -= 1
                        if remaining == 0: break

    calculated_me_stars = sum(b['stars'] for b in me_bases)
    calculated_opp_stars = sum(b['stars'] for b in opp_bases)

    #st.caption(f"Debug: objeto war = {war}")

    # =============================
    # 🎯 LÓGICA DE PROBABILIDADES REALISTA (Monte Carlo con targeting inteligente)
    # =============================
    team_size = len(me_bases)  # tamaño real de la guerra
    TOTAL_STARS = team_size * 3
    
    my_stars_current = summary['me_stars']      # estrellas que NOSOTROS hemos sacado (en bases enemigas)
    opp_stars_current = summary['opp_stars']    # estrellas que el RIVAL nos ha sacado (en nuestras bases)
    
    me_attacks_left = len(me_attackers)
    opp_attacks_left = len(opp_attackers)
    
    # Máximo estrellas restantes posibles en cada lado
    my_rem_max = sum(3 - b['stars'] for b in opp_bases)   # lo que aún podemos sacar nosotros
    opp_rem_max = sum(3 - b['stars'] for b in me_bases)   # lo que aún puede sacar el rival
    
    my_max_total = my_stars_current + min(me_attacks_left * 2.2, my_rem_max)
    opp_max_total = opp_stars_current + min(opp_attacks_left * 2.2, opp_rem_max)
    
    # =============================
    # RESULTADO FINAL O MATEMÁTICO
    # =============================
    display_result = False
    war_state = war.get("state")
    
    if war_state == "warEnded":
        if my_stars_current > opp_stars_current:
            st.success("🏆 RESULTADO FINAL: VICTORIA")
        elif my_stars_current < opp_stars_current:
            st.error("💀 RESULTADO FINAL: DERROTA")
        else:
            st.info("🤝 RESULTADO FINAL: EMPATE")
        display_result = True
    
    elif opp_max_total < my_stars_current:
        if my_rem_max == 0 and opp_rem_max >= my_stars_current > opp_stars_current:
            st.success("🟢 Alta probabilidad de Victoria y baja posibilidad de empate")
            display_result = True
        else:
            st.success("🟢 Victoria matemáticamente asegurada")
            display_result = True
    
    elif my_max_total < opp_stars_current:
        if opp_rem_max == 0  and my_rem_max >= opp_stars_current > my_stars_current:
            st.error("🔴 Alta probabilidad de derrota y baja posibilidad de empate")
            display_result = True
        else:
            st.error("🔴 Derrota matemáticamente asegurada")
            display_result = True

    # =============================
    # SIMULACIÓN SI LA GUERRA SIGUE ABIERTA
    # =============================
    if not display_result:
        if war_state == "preparation":
            st.info("🛠️ Guerra en preparación — simulación no disponible aún")
        elif war_state == "inWar":           
            with st.spinner("🔄 Simulando miles de escenarios posibles..."):
                result = estimate_normal_war_probs(
                    opp_bases=opp_bases,       # bases del rival (donde atacamos nosotros)
                    me_bases=me_bases,         # nuestras bases (donde ataca el rival)
                    my_att_ths=me_attackers,   # THs de nuestros ataques restantes
                    opp_att_ths=opp_attackers, # THs de los ataques restantes del rival
                    my_stars_current=my_stars_current,     
                    opp_stars_current=opp_stars_current,   
                    num_sims=8000             # puedes subir a 12000 si quieres más precisión                    
                )
            
            st.warning(
                f"🟡 Guerra en curso (Simulación - no determina el resultado final de la guerra)\n"
                f"🎯 Victoria: **{result['win']}%** | "
                f"🤝 Empate: **{result['draw']}%** | "
                f"❌ Derrota: **{result['lose']}%**"
            )
            
            # Opcional: colorear según probabilidad dominante
            if result['win'] > 65:
                st.success(f"Alta probabilidad de victoria ({result['win']}%) — ¡a por todas!")
            elif result['lose'] > 65:
                st.error(f"Alta probabilidad de derrota ({result['lose']}%) — cuidado...")
            elif result['draw'] > 50:
                st.info("Guerra muy igualada, probable empate")



    # ==========================
    # 📊 MÉTRICAS PRINCIPALES
    # ==========================
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "⚔️ Ataques",
            f"{summary['me_attacks']}/{summary['me_max_attacks']}",
            f"{summary['opp_attacks']}/{summary['opp_max_attacks']}"
        )

    with col2:
        st.metric(
            "⭐ Estrellas",
            f"{summary['me_stars']} - {summary['opp_stars']}",
            f"{summary['me_stars'] - summary['opp_stars']:+}"
        )

    with col3:
        st.metric(
            "🏚️ Destrucción total",
            f"{summary['me_destr']:.2f}% - {summary['opp_destr']:.2f}%",
            f"{summary['me_destr'] - summary['opp_destr']:+.2f}%"
        )


    # ==========================
    # 📊 RANKING JUGADORES
    # ==========================
    ranking = war.get("ranking", [])

    if not ranking:
        st.warning("No hay datos de ranking disponibles.")
        return
    

    df = pd.DataFrame(ranking)

    # Ordenar por estrellas totales y destrucción
    if "_stars_sort" in df.columns and "_destr_sort" in df.columns:
        df = df.sort_values(
            by=["_stars_sort", "_destr_sort"],
            ascending=[False, False]
        )
        df = df.drop(columns=["_stars_sort", "_destr_sort"])

    # Resaltar jugadores que no usaron los 2 ataques    
    war_state = war.get("state")

    def highlight_incomplete(row):
        # 🚫 No resaltar si la guerra no está activa
        if war_state == "preparation":
            return [""] * len(row)
        
        if "Ataques" in row:
            if row["Ataques"].startswith("0/") or row["Ataques"].startswith("1/"):
                return ["background-color: rgba(255, 0, 0, 0.15)"] * len(row)
        return [""] * len(row)

    styled_df = df.style.apply(highlight_incomplete, axis=1)

    st.dataframe(styled_df, use_container_width=True)
    

    # =====================================
    # ⚔️ VENTAJA ESTRUCTURAL VS CLAN ENEMIGO (igual que CWL)
    # =====================================
    st.subheader("⚔️ Ventaja estructural vs clan enemigo")

    def calculate_position_adv(full_war, summary):
        # Ordena miembros por TH descendente (top del mapa)
        our_members = sorted(full_war["clan"]["members"], key=lambda m: m.get("townhallLevel", 0), reverse=True)
        opp_members = sorted(full_war["opponent"]["members"], key=lambda m: m.get("townhallLevel", 0), reverse=True)
        
        team_size = len(our_members)
        
        # Compara posición por posición (1vs1, 2vs2, etc.)
        diff_sum = 0
        for i in range(team_size):
            our_th = our_members[i].get("townhallLevel", 0)
            opp_th = opp_members[i].get("townhallLevel", 0)
            diff_sum += our_th - opp_th
        
        avg_diff = round(diff_sum / team_size, 2)
        
        return [{
            "Clan": summary['me_name'],
            "avg_position_diff": avg_diff,
            "top_avg_th": round(sum(m.get("townhallLevel", 0) for m in our_members[:team_size]) / team_size, 2)
        },
        {
            "Clan": summary['opp_name'],
            "avg_position_diff": avg_diff,
            "top_avg_th": round(sum(m.get("townhallLevel", 0) for m in opp_members[:team_size]) / team_size, 2)
        }]

    position_adv = calculate_position_adv(full_war, summary)

    # Tabla
    df_pos = pd.DataFrame(position_adv)
    st.dataframe(df_pos, use_container_width=True)

    # Mensajes coloreados
    for row in position_adv:
        if row["Clan"] == summary['opp_name']:
            diff = row["avg_position_diff"]
            opp_name = summary['opp_name']
            if diff > 0.3:
                st.success(f"🟢 **Ventaja clara** vs {opp_name} (+{diff:+.2f} TH promedio en top {len(full_war['clan']['members'])})")
            elif diff > 0:
                st.success(f"🟢 **Ligera ventaja** vs {opp_name} (+{diff:+.2f} TH promedio)")
            elif diff < -0.3:
                st.error(f"🔴 **Desventaja clara** vs {opp_name} ({diff:+.2f} TH promedio)")
            elif diff < 0:
                st.error(f"🔴 **Ligera desventaja** vs {opp_name} ({diff:+.2f} TH promedio)")
            else:
                st.warning(f"🟡 **Guerra equilibrada** vs {opp_name} ({diff:+.2f} TH promedio)")



# Crear pestañas para cada clan
tab_labels = [clan["name"] for clan in selected_clans]
tabs = st.tabs(tab_labels)
#for clan_tag in CLAN_TAGS:
for i, clan in enumerate(selected_clans):
    with tabs[i]:
        if war_mode == "CWL":
            render_cwl_tab(clan)
        else:
            render_normal_war_tab(clan)
            

st.caption(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")

# 🔄 Botón refrescar
if st.button("🔄 Refrescar ahora"):
    st.rerun()

