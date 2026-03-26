import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Szybki Portfel", page_icon="⚡", layout="centered")

# --- CSS DLA MOBILNEGO WYGLĄDU ---
st.markdown("""
    <style>
    /* Sprawia, że kolumny nie przeskakują pod siebie na telefonie */
    [data-testid="column"] {
        display: flex;
        flex-direction: column;
        align-items: center;
        min-width: 0px !important;
    }
    /* Stylizacja przycisków kategorii */
    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 70px;
        padding: 5px;
        font-size: 14px;
        background-color: #f8f9fa;
        border: 1px solid #ddd;
    }
    /* Stylizacja listy wydatków */
    .expense-row {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 5px;
        border-left: 5px solid #007bff;
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

# --- 4. PRZYGOTOWANIE DANYCH ---
df = fetch_data()
if 'selected_kat' not in st.session_state:
    st.session_state.selected_kat = "Jedzenie"

# --- 5. INTERFEJS ---
st.title("⚡ Szybki Portfel")

# Zakładki u góry
tab_dodaj, tab_wykres = st.tabs(["➕ Dodaj / Lista", "📊 Wykresy"])

with tab_dodaj:
    # Budżet i wybór miesiąca
    if not df.empty:
        lista_miesiecy = sorted(df["miesiac"].unique(), reverse=True)
        wybrany_miesiac = st.selectbox("📅 Miesiąc", lista_miesiecy)
        df_view = df[df["miesiac"] == wybrany_miesiac]
    else:
        wybrany_miesiac = datetime.now().strftime('%Y-%m')
        df_view = df

    suma_m = df_view['cena'].sum() if not df_view.empty else 0.0
    st.metric(f"Wydano ({wybrany_miesiac})", f"{suma_m:.2f} zł")

    # 1. IKONY OBOK SIEBIE (Używamy kolumn z małym odstępem)
    st.write("Wybierz kategorię:")
    kategorie = {"Jedzenie": "🍕", "Transport": "🚗", "Dom": "🏠", "Rozrywka": "🎬", "Inne": "📦"}
    cols = st.columns(len(kategorie))
    
    for i, (nazwa, ikona) in enumerate(kategorie.items()):
        with cols[i]:
            st.button(f"{ikona}\n{nazwa}", key=f"btn_{nazwa}", on_click=wybierz_kategorie, args=(nazwa,))

    st.info(f"Wybrano: **{st.session_state.selected_kat}**")

    # Formularz dodawania
    with st.form("form_dodaj", clear_on_submit=True):
        co = st.text_input("Nazwa zakupu")
        ile = st.number_input("Kwota (zł)", min_value=0.0, step=0.01)
        if st.form_submit_button("ZAPISZ 🚀", use_container_width=True):
            if co and ile > 0:
                supabase.table("wydatki").insert({
                    "kategoria": st.session_state.selected_kat, 
                    "produkt": co, 
                    "cena": ile
                }).execute()
                st.rerun()

    st.divider()

    # 3. LISTA - POZYCJE OBOK SIEBIE
    st.subheader("📜 Historia")
    if not df_view.empty:
        for _, row in df_view.sort_values("id", ascending=False).iterrows():
            with st.container():
                # Definiujemy proporcje kolumn, żeby wszystko było w jednej linii
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.markdown(f"**{row['produkt']}**\n*{row['kategoria']}*")
                c2.markdown(f"**{row['cena']:.2f} zł**")
                with c3:
                    if st.button("❌", key=f"del_{row['id']}"):
                        usun_wydatek(row['id'])
                st.markdown("---")

with tab_wykres:
    st.subheader("📊 Analiza wydatków")
    if not df_view.empty:
        # 2. WYKRES NA ŚRODKU
        fig = px.pie(df_view, values='cena', names='kategoria', hole=0.5,
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(
            margin=dict(t=20, b=20, l=20, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        # Wyświetlamy wykres na całą szerokość - Plotly automatycznie centruje zawartość
        st.plotly_chart(fig, use_container_width=True)
        
        # Dodatkowe podsumowanie pod wykresem
        st.dataframe(df_view.groupby("kategoria")["cena"].sum().sort_values(ascending=False), use_container_width=True)
    else:
        st.info("Dodaj wydatki, aby zobaczyć wykres.")
