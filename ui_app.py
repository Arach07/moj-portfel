import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime

# --- 1. KONFIGURACJA ---
st.set_page_config(page_title="Szybki Portfel", page_icon="⚡", layout="centered")

# --- 2. POŁĄCZENIE ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 3. FUNKCJE (MUSZĄ BYĆ TUTAJ, ŻEBY PYTHON JE ZNAŁ) ---
def wybierz_kategorie(nazwa):
    st.session_state.selected_kat = nazwa

def usun_wydatek(row_id):
    """Usuwa konkretny wiersz z bazy Supabase"""
    try:
        supabase.table("wydatki").delete().eq("id", row_id).execute()
        st.rerun()
    except Exception as e:
        st.error(f"Nie udało się usunąć: {e}")

def fetch_data():
    """Pobiera dane i naprawia daty, jeśli ich brakuje"""
    try:
        res = supabase.table("wydatki").select("*").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            df["cena"] = pd.to_numeric(df["cena"])
            # Naprawa dat dla starych wpisów
            if "created_at" not in df.columns or df["created_at"].isnull().any():
                df["created_at"] = df.get("created_at", datetime.now().isoformat())
                df["created_at"] = df["created_at"].fillna(datetime.now().isoformat())
            
            df["created_at"] = pd.to_datetime(df["created_at"])
            df["miesiac"] = df["created_at"].dt.strftime('%Y-%m')
        return df
    except Exception as e:
        return pd.DataFrame(columns=["id", "kategoria", "produkt", "cena", "created_at", "miesiac"])

# --- 4. LOGIKA I INTERFEJS ---

df = fetch_data()

st.title("⚡ Szybki Portfel")

# Filtrowanie
if not df.empty:
    lista_miesiecy = sorted(df["miesiac"].unique(), reverse=True)
    wybrany_miesiac = st.selectbox("📅 Miesiąc", lista_miesiecy)
    df_view = df[df["miesiac"] == wybrany_miesiac]
else:
    wybrany_miesiac = datetime.now().strftime('%Y-%m')
    df_view = df

# Statystyki
with st.expander("💳 Budżet"):
    zarobki = st.number_input("Zarobki", value=7000.0)
    limit = st.number_input("Limit wydatków", value=3000.0)

suma_m = df_view['cena'].sum() if not df_view.empty else 0.0
st.metric(f"Wydano ({wybrany_miesiac})", f"{suma_m:.2f} zł", delta=f"{limit-suma_m:.2f} limitu")

# Szybkie dodawanie
st.subheader("🚀 Dodaj")
kategorie = {"Jedzenie": "🍕", "Transport": "🚗", "Dom": "🏠", "Rozrywka": "🎬", "Inne": "📦"}

if 'selected_kat' not in st.session_state:
    st.session_state.selected_kat = "Jedzenie"

cols = st.columns(len(kategorie))

for i, (nazwa, ikona) in enumerate(kategorie.items()):
    # Używamy on_click, żeby zmiana była natychmiastowa
    cols[i].button(
        f"{ikona}\n{nazwa}", 
        key=f"btn_{nazwa}", 
        on_click=wybierz_kategorie, 
        args=(nazwa,)
    )

    # Wyświetlamy wybraną kategorię z lekkim wyróżnieniem
st.markdown(f"### Wybrano: {kategorie[st.session_state.selected_kat]} **{st.session_state.selected_kat}**")

# Historia z usuwaniem
st.divider()
if not df_view.empty:
    for _, row in df_view.sort_values("id", ascending=False).iterrows():
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 2, 1])
            c1.write(f"**{row['produkt']}**")
            c1.caption(f"{row['kategoria']}")
            c2.write(f"{row['cena']:.2f} zł")
            # TU BYŁ BŁĄD - teraz funkcja jest zdefiniowana wyżej, więc zadziała
            if c3.button("❌", key=f"del_{row['id']}"):
                usun_wydatek(row['id'])
