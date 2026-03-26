import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime

# --- 1. KONFIGURACJA ---
st.set_page_config(page_title="Portfel", page_icon="💰", layout="centered")

# --- CSS (POPRAWIONY MOBILE UI) ---
st.markdown("""
<style>

/* Globalne zwężenie */
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
    padding-left: 0.5rem !important;
    padding-right: 0.5rem !important;
}

/* Kolumny */
[data-testid="column"] {
    padding: 0 2px !important;
}

/* Rzędy */
[data-testid="stHorizontalBlock"] {
    gap: 4px !important;
}

/* Przyciski kategorii */
div.stButton > button {
    width: 100% !important;
    height: 48px !important;
    font-size: 11px !important;
    border-radius: 10px !important;
    padding: 4px !important;
    line-height: 1.1 !important;
}

/* Markdown spacing */
.stMarkdown p {
    margin: 0 !important;
}

/* Metric */
[data-testid="stMetricValue"] {
    font-size: 26px !important;
    text-align: center;
}

/* Formularz */
[data-testid="stForm"] {
    padding: 8px !important;
}

/* Inputy */
input, .stNumberInput input {
    padding: 6px !important;
    font-size: 14px !important;
}

/* Separator */
hr {
    margin: 4px 0 !important;
}

</style>
""", unsafe_allow_html=True)

# --- 2. POŁĄCZENIE ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 3. FUNKCJE ---
def fetch_data():
    try:
        res = supabase.table("wydatki").select("*").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            df["cena"] = pd.to_numeric(df["cena"])
            df["created_at"] = pd.to_datetime(df.get("created_at", datetime.now().isoformat()))
            df["miesiac"] = df["created_at"].dt.strftime('%Y-%m')
        return df
    except:
        return pd.DataFrame(columns=["id", "kategoria", "produkt", "cena", "miesiac"])

def usun_wydatek(row_id):
    supabase.table("wydatki").delete().eq("id", row_id).execute()
    st.rerun()

def wybierz_kategorie(nazwa):
    st.session_state.selected_kat = nazwa

# --- 4. START ---
df = fetch_data()

if 'selected_kat' not in st.session_state:
    st.session_state.selected_kat = "Jedzenie"

# Tytuł (ładniejszy mobilnie)
st.markdown("<h2 style='text-align:center;'>💰 Mój Portfel</h2>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

tab_dodaj, tab_wykres = st.tabs(["➕ Dodaj", "📊 Wykres"])

with tab_dodaj:

    # --- MIESIĄC ---
    if not df.empty:
        lista_m = sorted(df["miesiac"].unique(), reverse=True)
        wybrany_m = st.selectbox("Miesiąc", lista_m, label_visibility="collapsed")
        df_v = df[df["miesiac"] == wybrany_m]
    else:
        wybrany_m = datetime.now().strftime('%Y-%m')
        df_v = df

    suma = df_v['cena'].sum() if not df_v.empty else 0.0
    st.metric("Suma", f"{suma:.2f} zł")

    # --- KATEGORIE ---
    kategorie = {
        "Jedzenie": "🍕",
        "Transport": "🚗",
        "Dom": "🏠",
        "Rozrywka": "🎬",
        "Inne": "📦"
    }

    cols = st.columns(len(kategorie))
    for i, (nazwa, ikona) in enumerate(kategorie.items()):
        cols[i].button(
            f"{ikona} {nazwa}",   # ❗ bez \n (fix UI)
            key=f"btn_{nazwa}",
            on_click=wybierz_kategorie,
            args=(nazwa,)
        )

    st.markdown(
        f"<p style='text-align:center; font-size:13px;'>Wybrano: <b>{st.session_state.selected_kat}</b></p>",
        unsafe_allow_html=True
    )

    # --- FORMULARZ ---
    with st.form("dodaj", clear_on_submit=True):
        c1, c2 = st.columns([3, 2])
        co = c1.text_input("Nazwa", placeholder="np. Kawa")
        ile = c2.number_input("zł", min_value=0.0, step=0.01)

        if st.form_submit_button("DODAJ 🚀", use_container_width=True):
            if co and ile > 0:
                supabase.table("wydatki").insert({
                    "kategoria": st.session_state.selected_kat,
                    "produkt": co,
                    "cena": ile
                }).execute()
                st.rerun()

    # --- LISTA ---
    st.subheader("📜 Ostatnie")

    if not df_v.empty:
        for _, row in df_v.sort_values("id", ascending=False).iterrows():
            c1, c2, c3 = st.columns([4, 2, 1])

            c1.markdown(f"<b>{row['produkt']}</b>", unsafe_allow_html=True)
            c2.markdown(f"{row['cena']:.2f} zł", unsafe_allow_html=True)

            if c3.button("❌", key=f"del_{row['id']}"):
                usun_wydatek(row['id'])

            st.markdown("<hr>", unsafe_allow_html=True)

with tab_wykres:
    if not df_v.empty:
        fig = px.pie(df_v, values='cena', names='kategoria', hole=0.5)
        fig.update_layout(
            margin=dict(t=0, b=0, l=0, r=0),
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
