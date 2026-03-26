import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Szybki Portfel", page_icon="💰", layout="centered")

# --- BARDZO AGRESYWNY CSS DLA MOBILNEGO UKŁADU ---
st.markdown("""
    <style>
    /* Wymuszanie rzędu dla przycisków kategorii na telefonie */
    [data-testid="column"] {
        width: 18% !important;
        flex: 1 1 18% !important;
        min-width: 0px !important;
        padding: 0px 2px !important;
    }
    
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: space-between !important;
    }

    /* Styl przycisków kategorii - mniejszy font i padding */
    div.stButton > button {
        width: 100% !important;
        border-radius: 8px !important;
        height: 50px !important;
        padding: 0px !important;
        font-size: 10px !important;
        line-height: 1 !important;
        white-space: pre-wrap !important;
    }

    /* Naprawa listy wydatków - Nazwa, Cena i X w jednej linii */
    .expense-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid rgba(49, 51, 63, 0.1);
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
    st.metric("Wydano", f"{suma_m:.2f} zł")

    # IKONY KATEGORII - wymuszone poziomo
    kategorie = {"Jedzenie": "🍕", "Transport": "🚗", "Dom": "🏠", "Rozrywka": "🎬", "Inne": "📦"}
    cols = st.columns(len(kategorie))
    for i, (nazwa, ikona) in enumerate(kategorie.items()):
        cols[i].button(f"{ikona}\n{nazwa}", key=f"btn_{nazwa}", on_click=wybierz_kategorie, args=(nazwa,))

    st.info(f"Kategoria: **{st.session_state.selected_kat}**")

    with st.form("dodaj_form", clear_on_submit=True):
        co = st.text_input("Co kupiłeś?", placeholder="Nazwa")
        ile = st.number_input("Kwota (zł)", min_value=0.0, step=0.01)
        if st.form_submit_button("DODAJ 🚀", use_container_width=True):
            if co and ile > 0:
                supabase.table("wydatki").insert({
                    "kategoria": st.session_state.selected_kat, 
                    "produkt": co, 
                    "cena": ile
                }).execute()
                st.rerun()

    st.subheader("📜 Ostatnie")
    if not df_view.empty:
        for _, row in df_view.sort_values("id", ascending=False).iterrows():
            # Ręczne tworzenie rzędu za pomocą kolumn z wyłączonym zawijaniem
            c1, c2, c3 = st.columns([3, 2, 1])
            with c1:
                st.write(f"**{row['produkt']}**")
            with c2:
                st.write(f"{row['cena']:.2f} zł")
            with c3:
                if st.button("❌", key=f"del_{row['id']}"):
                    usun_wydatek(row['id'])

with tab_wykres:
    if not df_view.empty:
        fig = px.pie(df_view, values='cena', names='kategoria', hole=0.5,
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig, use_container_width=True)
