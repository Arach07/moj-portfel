import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime

# --- KONFIGURACJA ---
st.set_page_config(page_title="Szybki Portfel", page_icon="⚡", layout="centered")

# CSS dla ładniejszych przycisków (opcjonalne, dla lepszego wyglądu)
st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #f0f2f6;
    }
    </style>
    """, unsafe_allow_html=True)

# Połączenie z Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- FUNKCJE ---
def fetch_data():
    try:
        res = supabase.table("wydatki").select("*").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            df["cena"] = pd.to_numeric(df["cena"])
            # Konwersja daty na format czytelny dla Pythona
            df["created_at"] = pd.to_datetime(df["created_at"])
            df["miesiac"] = df["created_at"].dt.strftime('%Y-%m')
        return df
    except:
        return pd.DataFrame(columns=["id", "kategoria", "produkt", "cena", "created_at", "miesiac"])

def usun_wydatek(row_id):
    supabase.table("wydatki").delete().eq("id", row_id).execute()
    st.rerun()

# --- LOGIKA APLIKACJI ---
df = fetch_data()

st.title("⚡ Szybki Portfel")

# --- FILTROWANIE PO MIESIĄCU ---
if not df.empty:
    lista_miesiecy = sorted(df["miesiac"].unique(), reverse=True)
    wybrany_miesiac = st.selectbox("📅 Wybierz miesiąc", lista_miesiecy)
    df_view = df[df["miesiac"] == wybrany_miesiac]
else:
    wybrany_miesiac = datetime.now().strftime('%Y-%m')
    df_view = df

# --- BUDŻET (Szybki podgląd) ---
with st.expander("💳 Ustawienia"):
    zarobki = st.number_input("Zarobki", value=7000.0)
    limit = st.number_input("Limit", value=3000.0)

suma_miesiaca = df_view['cena'].sum() if not df_view.empty else 0.0
st.metric(f"Wydano w {wybrany_miesiac}", f"{suma_miesiaca:.2f} zł", delta=f"{limit-suma_miesiaca:.2f} limitu")

# --- NOWY INTERFEJS DODAWANIA (IKONY) ---
st.subheader("🚀 Szybkie dodawanie")

# Słownik kategorii z ikonami
kategorie = {
    "Jedzenie": "🍕",
    "Transport": "🚗",
    "Dom": "🏠",
    "Rozrywka": "🎬",
    "Inne": "📦"
}

# Tworzymy kolumny dla przycisków kategorii
cols = st.columns(len(kategorie))
if 'selected_kat' not in st.session_state:
    st.session_state.selected_kat = "Jedzenie"

for i, (nazwa, ikona) in enumerate(kategorie.items()):
    if cols[i].button(f"{ikona}\n{nazwa}"):
        st.session_state.selected_kat = nazwa

# Informacja co wybrano
st.info(f"Wybrana kategoria: **{st.session_state.selected_kat}** {kategorie[st.session_state.selected_kat]}")

with st.form("form_dodaj", clear_on_submit=True):
    co = st.text_input("Co kupiłeś?")
    ile = st.number_input("Kwota (zł)", min_value=0.0, step=0.01)
    
    if st.form_submit_button("ZAPISZ 🚀"):
        if co and ile > 0:
            supabase.table("wydatki").insert({
                "kategoria": st.session_state.selected_kat, 
                "produkt": co, 
                "cena": ile
            }).execute()
            st.rerun()

# --- WYKRES ---
if not df_view.empty:
    fig = px.pie(df_view, values='cena', names='kategoria', hole=0.4)
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250)
    st.plotly_chart(fig, use_container_width=True)

# --- LISTA ---
st.subheader("📜 Historia")
for index, row in df_view.sort_values("id", ascending=False).iterrows():
    with st.container(border=True):
        c1, c2, c3 = st.columns([3, 2, 1])
        c1.write(f"**{row['produkt']}**")
        c1.caption(f"{row['kategoria']}")
        c2.write(f"{row['cena']:.2f} zł")
        if c3.button("❌", key=f"del_{row['id']}"):
            usun_wydatek(row['id'])
