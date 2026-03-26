import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Szybki Portfel", page_icon="⚡", layout="centered")

# Stylizacja przycisków
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

# --- 4. PRZYGOTOWANIE ---
df = fetch_data()

if 'selected_kat' not in st.session_state:
    st.session_state.selected_kat = "Jedzenie"

# --- 5. INTERFEJS ---

st.title("⚡ Szybki Portfel")

# Wybór miesiąca
if not df.empty:
    lista_miesiecy = sorted(df["miesiac"].unique(), reverse=True)
    wybrany_miesiac = st.selectbox("📅 Wybierz miesiąc", lista_miesiecy)
    df_view = df[df["miesiac"] == wybrany_miesiac]
else:
    wybrany_miesiac = datetime.now().strftime('%Y-%m')
    df_view = df

# Budżet
with st.expander("💳 Ustawienia budżetu"):
    zarobki = st.number_input("Twoje zarobki (zł)", value=7000.0)
    limit = st.number_input("Miesięczny limit (zł)", value=3000.0)

suma_m = df_view['cena'].sum() if not df_view.empty else 0.0
st.metric(f"Wydano w {wybrany_miesiac}", f"{suma_m:.2f} zł", delta=f"{limit-suma_m:.2f} limitu")

# Przyciski kategorii
st.subheader("🚀 Wybierz kategorię")
kategorie = {"Jedzenie": "🍕", "Transport": "🚗", "Dom": "🏠", "Rozrywka": "🎬", "Inne": "📦"}
cols = st.columns(len(kategorie))

for i, (nazwa, ikona) in enumerate(kategorie.items()):
    cols[i].button(f"{ikona}\n{nazwa}", key=f"btn_{nazwa}", on_click=wybierz_kategorie, args=(nazwa,))

st.info(f"Wybrana kategoria: **{st.session_state.selected_kat}**")

# FORMULARZ (Tu był błąd - teraz jest poprawiony)
with st.form("form_dodaj", clear_on_submit=True):
    co = st.text_input("Nazwa zakupu")
    ile = st.number_input("Kwota (zł)", min_value=0.0, step=0.01) # Tu była ucięta linia!
    
    if st.form_submit_button("ZAPISZ WYDATEK 🚀"):
        if co and ile > 0:
            supabase.table("wydatki").insert({
                "kategoria": st.session_state.selected_kat, 
                "produkt": co, 
                "cena": ile
            }).execute()
            st.rerun()

# Wykres i Historia
if not df_view.empty:
    st.divider()
    fig = px.pie(df_view, values='cena', names='kategoria', hole=0.5)
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📜 Lista")
    for _, row in df_view.sort_values("id", ascending=False).iterrows():
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 2, 1])
            c1.write(f"**{row['produkt']}**")
            c1.caption(f"{row['kategoria']}")
            c2.write(f"{row['cena']:.2f} zł")
            if c3.button("❌", key=f"del_{row['id']}"):
                usun_wydatek(row['id'])
