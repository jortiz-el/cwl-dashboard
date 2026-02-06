import streamlit as st
from datetime import datetime
from cwl_logic import get_war_summary
import pandas as pd

from cwl_logic import (
    get_league_group,
    find_all_my_wars,
    parse_end_time,
    get_attack_ranking_data
)

clans_list = [
    {"name": "GOD'S ACADEMY", "tag": "#2R9JPR82Y"},
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

    group = get_league_group(clan_tag)
    if not group:
        st.warning("No hay CWL activa para este clan.")
        continue

    wars = find_all_my_wars(group, clan_tag)

    if not wars:
        st.warning("No se encontraron guerras.")
        continue

    # 🧠 Lógica LIVE vs ALL
    if show_all_rounds:
        wars_to_show = sorted(wars, key=lambda x: x[1])
        st.info("Mostrando TODAS las rondas")
    else:
        active_wars = [(w, r) for w, r in wars if w["state"] == "inWar"]

        if active_wars:
            wars_to_show = active_wars
        else:
            ended_wars = [(w, r) for w, r in wars if w["state"] == "warEnded"]

            ended_wars.sort(
                key=lambda x: parse_end_time(x[0]) or datetime.min,
                reverse=True
            )

            wars_to_show = [ended_wars[0]]
            st.info("Mostrando última guerra finalizada")

    # 🖥️ Renderizar guerras
    for war, round_idx in wars_to_show:
        summary = get_war_summary(war, clan_tag)
        me = war["clan"] if war["clan"]["tag"] == clan_tag else war["opponent"]
        opp = war["opponent"] if me == war["clan"] else war["clan"]
        me_badge = me.get("badgeUrls", {}).get("small")
        opp_badge = opp.get("badgeUrls", {}).get("small")

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
        st.write(f"Estado: **{war['state']}**")

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
        ranking = get_attack_ranking_data(war, clan_tag)
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

