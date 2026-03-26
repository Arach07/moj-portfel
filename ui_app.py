import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime

# --- 1. KONFIGURACJA ---
st.set_page_config(page_title="Portfel", page_icon="💰", layout="centered")

# --- KOMPLEKSOWY CSS DLA MOBILNEGO ŚCIŚNIĘCIA ---
st.markdown("""
    <style>
    /* Usuwamy gigantyczne odstępy między kolumnami Streamlita */
    [data-testid="column"] {
        width: auto !important;
        flex: 1 1 0% !important;
        min-width: 0px !important;
        padding: 0 2px !important;
    }
    
    /* Wymuszamy, żeby rzędy się nie rozjeżdżały */
    [data-testid="stHorizontalBlock"] {
        gap: 5px !important;
        justify-content: center !important;
    }

    /* Przyciski kategorii - mniejsze i zgrabne */
    div.stButton > button {
        width: 100% !important;
        border-radius: 8px !important;
        height: 50px !important;
        padding: 0 !important;
        font-size: 10px !important;
        background-color: #f8f9fa;
    }

    /* Lista historii - walka o jedną linię */
    .stMarkdown p {
        margin-bottom: 0px !important;
    }
    
    /* Wyśrodkowanie metryki */
    [data-testid="stMetricValue"] {
        font-size: 28px !important;
        text-align: center;
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

st.title("💰 Mój Portfel")

tab_dodaj, tab_wykres = st.tabs(["➕ Dodaj", "📊 Wykres"])

with tab_dodaj:
    # Wybór miesiąca (mały)
    if not df.empty:
        lista_m = sorted(df["miesiac"].unique(), reverse=True)
        wybrany_m = st.selectbox("Miesiąc", lista_m, label_visibility="collapsed")
        df_v = df[df["miesiac"] == wybrany_m]
    else:
        wybrany_m = datetime.now().strftime('%Y-%m')
        df_v = df

    suma = df_v['cena'].sum() if not df_v.empty else 0.0
    st.metric("Suma", f"{suma:.2f} zł")

    # IKONY - tu jest klucz do braku rozjeżdżania
    kategorie = {"Jedzenie": "🍕", "Transport": "🚗", "Dom": "🏠", "Rozrywka": "🎬", "Inne": "📦"}
    cols = st.columns(len(kategorie))
    for i, (nazwa, ikona) in enumerate(kategorie.items()):
        cols[i].button(f"{ikona}\n{nazwa}", key=f"btn_{nazwa}", on_click=wybierz_kategorie, args=(nazwa,))

    st.markdown(f"<p style='text-align: center; font-size: 13px;'>Wybrano: <b>{st.session_state.selected_kat}</b></p>", unsafe_allow_html=True)

    with st.form("dodaj", clear_on_submit=True):
        c1, c2 = st.columns([2, 1])
        co = c1.text_input("Nazwa", placeholder="np. Kawa")
        ile = c2.number_input("zł", min_value=0.0, step=0.01)
        if st.form_submit_button("DODAJ 🚀", use_container_width=True):
            if co and ile > 0:
                supabase.table("wydatki").insert({"kategoria": st.session_state.selected_kat, "produkt": co, "cena": ile}).execute()
                st.rerun()

    st.subheader("📜 Ostatnie")
    if not df_v.empty:
        for _, row in df_v.sort_values("id", ascending=False).iterrows():
            # Bardzo ciasny układ linii: Produkt | Cena | X
            c1, c2, c3 = st.columns([3, 2, 1])
            c1.markdown(f"**{row['produkt']}**")
            c2.write(f"{row['cena']:.2f}zł")
            if c3.button("❌", key=f"del_{row['id']}"):
                usun_wydatek(row['id'])
            st.markdown("<hr style='margin:2px 0; opacity:0.1'>", unsafe_allow_html=True)

with tab_wykres:
    if not df_v.empty:
        fig = px.pie(df_v, values='cena', names='kategoria', hole=0.5)
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
