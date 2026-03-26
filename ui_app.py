import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Szybki Portfel", page_icon="💰", layout="centered")

# --- POPRAWIONY CSS (WYŚRODKOWANIE I ZBliżenie IKON) ---
st.markdown("""
    <style>
    /* Wymuszanie rzędu i zbliżenie kolumn do siebie */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        justify-content: center !important; /* Środkuje grupę ikon */
        gap: 5px !important; /* Mały odstęp między ikonami */
    }

    /* Szerokość każdej kolumny z ikoną */
    [data-testid="column"] {
        width: 65px !important; /* Stała szerokość, żeby nie "pływały" */
        flex: 0 0 65px !important;
        min-width: 65px !important;
    }

    /* Styl przycisków kategorii */
    div.stButton > button {
        width: 100% !important;
        border-radius: 10px !important;
        height: 55px !important;
        padding: 0px !important;
        font-size: 10px !important;
        background-color: #f8f9fa;
        border: 1px solid #eee;
    }

    /* Wyśrodkowanie tekstu w metrykach i nagłówkach */
    .stMetric {
        text-align: center;
    }
    
    /* Styl dla listy historii - wszystko w jednej linii */
    .expense-row [data-testid="column"] {
        width: auto !important;
        flex: 1 1 auto !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. POŁĄCZENIE Z SUPABASE ---
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
            if "created_at" not in df.columns or df["created_at"].isnull().any():
                df["created_at"] = datetime.now().isoformat()
            df["created_at"] = pd.to_datetime(df["created_at"])
            df["miesiac"] = df["created_at"].dt.strftime('%Y-%m')
        return df
    except:
        return pd.DataFrame(columns=["id", "kategoria", "produkt", "cena", "created_at", "miesiac"])

def usun_wydatek(row_id):
    supabase.table("wydatki").delete().eq("id", row_id).execute()
    st.rerun()

def wybierz_kategorie(nazwa):
    st.session_state.selected_kat = nazwa

# --- 4. DANE ---
df = fetch_data()
if 'selected_kat' not in st.session_state:
    st.session_state.selected_kat = "Jedzenie"

# --- 5. INTERFEJS ---
st.title("💰 Mój Portfel")

tab_dodaj, tab_wykres = st.tabs(["➕ Dodaj", "📊 Wykres"])

with tab_dodaj:
    if not df.empty:
        lista_miesiecy = sorted(df["miesiac"].unique(), reverse=True)
        wybrany_miesiac = st.selectbox("📅 Miesiąc", lista_miesiecy, label_visibility="collapsed")
        df_view = df[df["miesiac"] == wybrany_miesiac]
    else:
        wybrany_miesiac = datetime.now().strftime('%Y-%m')
        df_view = df

    suma_m = df_view['cena'].sum() if not df_view.empty else 0.0
    st.metric("Wydano łącznie", f"{suma_m:.2f} zł")

    # IKONY KATEGORII - teraz wyśrodkowane i blisko siebie
    kategorie = {"Jedzenie": "🍕", "Transport": "🚗", "Dom": "🏠", "Rozrywka": "🎬", "Inne": "📦"}
    cols = st.columns(len(kategorie))
    for i, (nazwa, ikona) in enumerate(kategorie.items()):
        cols[i].button(f"{ikona}\n{nazwa}", key=f"btn_{nazwa}", on_click=wybierz_kategorie, args=(nazwa,))

    st.markdown(f"<p style='text-align: center; color: gray;'>Wybrano: <b>{st.session_state.selected_kat}</b></p>", unsafe_allow_html=True)

    with st.form("dodaj_form", clear_on_submit=True):
        co = st.text_input("Co kupiłeś?", placeholder="Nazwa")
        ile = st.number_input("Kwota (zł)", min_value=0.0, step=0.01)
        if st.form_submit_button("DODAJ WYDATEK 🚀", use_container_width=True):
            if co and ile > 0:
                supabase.table("wydatki").insert({
                    "kategoria": st.session_state.selected_kat, 
                    "produkt": co, 
                    "cena": ile
                }).execute()
                st.rerun()

    st.subheader("📜 Historia")
    if not df_view.empty:
        for _, row in df_view.sort_values("id", ascending=False).iterrows():
            # Rząd historii: Nazwa (szeroko), Cena, Usuń
            c1, c2, c3 = st.columns([2.5, 1.5, 0.5])
            with c1:
                st.markdown(f"**{row['produkt']}**")
                st.caption(row['kategoria'])
            with c2:
                st.write(f"{row['cena']:.2f} zł")
            with c3:
                if st.button("❌", key=f"del_{row['id']}"):
                    usun_wydatek(row['id'])
            st.markdown("<hr style='margin:0; opacity:0.1'>", unsafe_allow_html=True)

with tab_wykres:
    if not df_view.empty:
        fig = px.pie(df_view, values='cena', names='kategoria', hole=0.5,
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Brak danych.")
