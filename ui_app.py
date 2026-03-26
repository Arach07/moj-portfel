import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Szybki Portfel", page_icon="💰", layout="centered")

# --- MOCNY CSS DLA UKŁADU MOBILNEGO ---
st.markdown("""
    <style>
    /* Wymuszanie kolumn obok siebie na telefonie */
    [data-testid="column"] {
        width: calc(20% - 1px) !important;
        flex: 1 1 calc(20% - 1px) !important;
        min-width: 0px !important;
    }
    
    /* Specjalny układ dla listy wydatków (trzy kolumny) */
    [data-testid="stVerticalBlock"] > div > div > [data-testid="column"] {
        width: auto !important;
        flex: 1 1 auto !important;
    }

    /* Styl przycisków kategorii */
    div.stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 55px;
        padding: 0px;
        font-size: 11px !important;
        line-height: 1.2;
    }

    /* Usunięcie zbędnych odstępów */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    
    /* Wyśrodkowanie wykresu */
    .js-plotly-plot {
        margin: 0 auto;
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
    # Miesiąc i Metryka
    if not df.empty:
        lista_miesiecy = sorted(df["miesiac"].unique(), reverse=True)
        wybrany_miesiac = st.selectbox("📅 Miesiąc", lista_miesiecy, label_visibility="collapsed")
        df_view = df[df["miesiac"] == wybrany_miesiac]
    else:
        wybrany_miesiac = datetime.now().strftime('%Y-%m')
        df_view = df

    suma_m = df_view['cena'].sum() if not df_view.empty else 0.0
    st.metric("Suma wydatków", f"{suma_m:.2f} zł")

    # IKONY KATEGORII (Wymuszone obok siebie)
    kategorie = {"Jedzenie": "🍕", "Transport": "🚗", "Dom": "🏠", "Rozrywka": "🎬", "Inne": "📦"}
    cols = st.columns(len(kategorie))
    for i, (nazwa, ikona) in enumerate(kategorie.items()):
        cols[i].button(f"{ikona}\n{nazwa}", key=f"btn_{nazwa}", on_click=wybierz_kategorie, args=(nazwa,))

    st.info(f"Kategoria: **{st.session_state.selected_kat}**")

    # Formularz
    with st.form("dodaj_form", clear_on_submit=True):
        co = st.text_input("Co kupiłeś?", placeholder="np. Zakupy")
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
            # Kontener z kolumnami dla każdego wiersza
            c1, c2, c3 = st.columns([2, 1, 0.5])
            c1.markdown(f"**{row['produkt']}** \n*{row['kategoria']}*")
            c2.markdown(f"**{row['cena']:.2f}**")
            with c3:
                if st.button("❌", key=f"del_{row['id']}"):
                    usun_wydatek(row['id'])
            st.markdown("<hr style='margin:0; opacity:0.2'>", unsafe_allow_html=True)

with tab_wykres:
    if not df_view.empty:
        st.subheader(f"Podsumowanie: {wybrany_miesiac}")
        fig = px.pie(df_view, values='cena', names='kategoria', hole=0.5,
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(
            margin=dict(t=0, b=0, l=0, r=0),
            legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela pod wykresem
        st.table(df_view.groupby("kategoria")["cena"].sum().sort_values(ascending=False))
    else:
        st.info("Brak danych do wykresu.")
