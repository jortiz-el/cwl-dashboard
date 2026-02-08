import streamlit as st
from datetime import datetime
import pandas as pd
import requests
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000") # local

import streamlit as st

def get_full_summary_api(clan_tag):
    try:
        r = requests.get(
            f"{BACKEND_URL}/cwl/full-summary",
            params={"clan_tag": clan_tag},
            timeout=30,
        )

        if r.status_code == 403:
            st.warning(f"🔒 El clan {clan_tag} es privado o no tienes acceso.")
            return None

        if r.status_code == 404:
            st.warning(f"❌ Clan {clan_tag} no encontrado.")
            return None

        if r.status_code >= 500:
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
        timeout=30,
    )
    r.raise_for_status()
    return r.json()

def get_league_group_api(clan_tag):
    r = requests.get(
        f"{BACKEND_URL}/cwl/league-group",
        params={"clan_tag": clan_tag},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()

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
    {"name": "PULP FICTION", "tag": "#2CPU9J20Q"}
]

CLAN_TAGS = [
    "#2R9JPR82Y",
    # añade más
]

st.set_page_config(page_title="CWL Dashboard", layout="wide")
st.title("🏆 CWL Dashboard")

# 🎛️ Selector LIVE / ALL
mode = st.radio(
    "Modo de visualización",
    ["LIVE (solo activa / última)", "ALL (todas las rondas)"]
)

show_all_rounds = mode.startswith("ALL")

st.caption(f"Modo actual: {'ALL' if show_all_rounds else 'LIVE'}")

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


#for clan_tag in CLAN_TAGS:
for clan in selected_clans:
    clan_tag = clan['tag'] #logica para seleccion de clanes desde el dropdownlist
    #clan_tag = st.session_state["selected_clan"] #logica para seleccion de clanes desde botones
    st.header(f"🏰 Clan {clan_tag}")

    data = get_full_summary_api(clan_tag)

    if not data:
        st.info(f"⏭️ Saltando clan {clan['name']}")
        continue

    wars = data.get("wars", [])

    if not wars:
        st.warning("No hay CWL activa para este clan.")
        continue

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

    # 🖥️ Renderizar guerras
    for war in wars_to_show:
        summary = war["summary"]

        me_badge = war["me"]["badge"]
        opp_badge = war["opp"]["badge"]

        round_idx = war["round"]



        # Columnas más compactas
        col_round, col_me_name,  col_vs, col_opp_name = st.columns([1, 1, 1, 1])

        # Texto Ronda 
        with col_round:
            st.markdown(f"<h2>🏆 Ronda {round_idx}</h2>", unsafe_allow_html=True)

        # Nombre clan 
        with col_me_name:
            st.markdown(f"<h2>{summary['me_name']}</h2>", unsafe_allow_html=True)
            if me_badge:
                st.image(me_badge, width=70)

        # VS centrado vertical
        with col_vs:
            st.markdown("<h2 style='text-align:center; margin:0;'>🆚</h2>", unsafe_allow_html=True)

        # Nombre rival
        with col_opp_name:
            st.markdown(f"<h2>{summary['opp_name']}</h2>", unsafe_allow_html=True)
            if opp_badge:
                st.image(opp_badge, width=70)

        #st.subheader(f"🏆 Ronda {round_idx} — {summary['me_name']} 🆚 {summary['opp_name']}")
        st.write(f"🛡️ Estado: **{war['state']}**") 
        st.write(f"⏳ Tiempo restante: **{war['time_left']}**") 

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

st.caption(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")

# 🔄 Botón refrescar
if st.button("🔄 Refrescar ahora"):
    st.rerun()

