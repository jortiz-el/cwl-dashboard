import streamlit as st
import pandas as pd
import requests
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")


@st.cache_data(ttl=60)
def get_clan_donations_api(clan_tag):
    try:
        r = requests.get(
            f"{BACKEND_URL}/clan/donations",
            params={"clan_tag": clan_tag},
            timeout=30
        )
        r.raise_for_status()
        return r.json()
    except:
        return None


def render_donations_tab(clan):

    clan_tag = clan["tag"]
    st.header(f"💰 Donaciones — {clan['name']}")

    data = get_clan_donations_api(clan_tag)

    if not data:
        st.warning("No se pudieron cargar las donaciones.")
        st.caption(data)
        return

    clan_info = data["clan_info"]
    members = data["members"]

    # =============================
    # 🏰 RESUMEN CLAN
    # =============================
    col1, col2 = st.columns([1, 3])

    with col1:
        if clan_info.get("badge"):
            st.image(clan_info["badge"], width=120)

    with col2:
        #st.markdown(f"### {clan_info['name']}")
        st.write(f"🏆 Nivel: {clan_info['level']}")
        st.write(f"🏅 Liga CWL: {clan_info['league']}")
        st.write(f"⚔️ War Wins: {clan_info['war_wins']}")

    st.markdown("---")

    # =============================
    # 📊 TABLA AVANZADA
    # =============================

    df = pd.DataFrame(members)

    df["Ratio"] = df.apply(
        lambda x: round(x["donations"] / x["received"], 2)
        if x["received"] > 0 else x["donations"],
        axis=1
    )

    df = df.sort_values(by="donations", ascending=False)

    st.subheader("👥 Miembros")

    st.dataframe(
        df[["name","th_icon", "role", "donations", "Ratio", "trophies"]],
        column_config={
        "th_icon": st.column_config.ImageColumn(
            "TH",
            help="Town Hall",
            width="small"
        )
        },
        use_container_width=True
    )

    # =============================
    # 🩺 SALUD DEL CLAN
    # =============================

    st.subheader("🩺 Salud del Clan")

    avg_don = df["donations"].mean()
    low_don = len(df[df["donations"] == 0])
    low_th = len(df[df["th"] <= 10])

    if avg_don > 1000:
        st.success("🟢 Clan muy activo en donaciones")
    elif avg_don > 300:
        st.warning("🟡 Actividad media en donaciones")
    else:
        st.error("🔴 Pocas donaciones en el clan")

    if low_don > 5:
        st.error("🔴 Muchos jugadores con 0 donaciones")

    if low_th > len(df) * 0.4:
        st.warning("🟡 Muchos jugadores TH bajos")
