import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Szybki Portfel", page_icon="⚡", layout="centered")

# Stylizacja przycisków (opcjonalnie dla lepszego wyglądu na telefonie)
st.markdown("""
    <style>
    div.stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 60px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. POŁĄCZENIE Z SUPABASE ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 3. FUNKCJE (LOGIKA BAZY) ---

def fetch_data():
    """Pobiera dane i przygotowuje kolumny daty"""
    try:
        res = supabase.table("wydatki").select("*").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            df["cena"] = pd.to_numeric(df["cena"])
            
            # Naprawa daty: jeśli pusta, wstaw dzisiejszą
            if "created_at" not in df.columns or df["created_at"].isnull().any():
                df["created_at"] = df.get("created_at", datetime.now().isoformat())
                df["created_at"] = df["created_at"].fillna(datetime.now().isoformat())
            
            df["created_at"] = pd.to_datetime(df["created_at"])
            df["miesiac"] = df["created_at"].dt.strftime('%Y-%m')
        return df
    except Exception as e:
        return pd.DataFrame(columns=["id", "kategoria", "produkt", "cena", "created_at", "miesiac"])

def usun_wydatek(row_id):
    """Usuwa wpis i odświeża stronę"""
    supabase.table("wydatki").delete().eq("id", row_id).execute()
    st.rerun()

def wybierz_kategorie(nazwa):
    """Callback dla szybszej zmiany kategorii"""
    st.session_state.selected_kat = nazwa

# --- 4. PRZYGOTOWANIE DANYCH ---
df = fetch_data()

# Inicjalizacja wybranej kategorii w pamięci sesji
if 'selected_kat' not in st.session_state:
    st.session_state.selected_kat = "Jedzenie"

# --- 5. INTERFEJS UŻYTKOWNIKA ---

st.title("⚡ Szybki Portfel")

# SEKCJA: WYBÓR MIESIĄCA
if not df.empty:
    lista_miesiecy = sorted(df["miesiac"].unique(), reverse=True)
    wybrany_miesiac = st.selectbox("📅 Wybierz miesiąc", lista_miesiecy)
    df_view = df[df["miesiac"] == wybrany_miesiac]
else:
    wybrany_miesiac = datetime.now().strftime('%Y-%m')
    df_view = df

# SEKCJA: STATYSTYKI (ZAROBKI I LIMIT)
with st.expander("💳 Ustawienia budżetu"):
    zarobki = st.number_input("Twoje zarobki (zł)", value=7000.0)
    limit = st.number_input("Miesięczny limit (zł)", value=3000.0)

suma_m = df_view['cena'].sum() if not df_view.empty else 0.0
st.metric(f"Wydano w {wybrany_miesiac}", f"{suma_m:.2f} zł", delta=f"{limit-suma_m:.2f} limitu")

# SEKCJA: SZYBKIE DODAWANIE (IKONY)
st.subheader("🚀 Wybierz kategorię")
kategorie = {
    "Jedzenie": "🍕", 
    "Transport": "🚗", 
    "Dom": "🏠", 
    "Rozrywka": "🎬", 
    "Inne": "📦"
}

cols = st.columns(len(kategorie))
for i, (nazwa, ikona) in enumerate(kategorie.items()):
    # Przycisk z on_click działa znacznie szybciej
    cols[i].button(
        f"{ikona}\n{nazwa}", 
        key=f"btn_{nazwa}", 
        on_click=wybierz_kategorie, 
        args=(nazwa,)
    )

# Wyświetlamy aktualnie wybrany typ dużym napisem
st.info(f"Wybrana kategoria: **{st.session_state.selected_kat}** {kategorie[st.session_state.selected_kat]}")

with st.form("form_dodaj", clear_on_submit=True):
    co = st.text_input("Nazwa zakupu (np. Biedronka)")
    ile = st.number_
