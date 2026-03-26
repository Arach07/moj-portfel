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

# --- 3. FUNKCJE ---

def usun_wydatek(row_id):
    try:
        supabase.table("wydatki").delete().eq("id", row_id).execute()
        st.rerun()
    except Exception as e:
        st.error(f"Nie udało się usunąć: {e}")

def fetch_data():
    try:
        res = supabase.table("wydatki").select("*").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            df["cena"] = pd.to_numeric(df["cena"])
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

# --- TUTAJ PRZENIOSŁEM WYBÓR MIESIĄCA NA SAMĄ GÓRĘ ---
if not df.empty:
    lista_miesiecy = sorted(df["miesiac"].unique(), reverse=True)
    wybrany_miesiac = st.selectbox("📅 Miesiąc", lista_miesiecy)
    df_view = df[df["miesiac"] == wybrany_miesiac]
else:
    wybrany_miesiac = datetime.now().strftime('%Y-%m')
    df_view = df

# Zakładki poniżej wyboru miesiąca
tab_dodaj, tab_wykresy = st.tabs(["➕ Dodaj & Historia", "📊 Wykresy"])

# --- ZAKŁADKA 1: DODAWANIE I LISTA ---
with tab_dodaj:
    # Statystyki
    with st.expander("💳 Budżet"):
        zarobki = st.number_input("Zarobki", value=7000.0)
        limit = st.number_input("Limit wydatków", value=3000.0)

    suma_m = df_view['cena'].sum() if not df_view.empty else 0.0
    st.metric(f"Wydano ({wybrany_miesiac})", f"{suma_m:.2f} zł", delta=f"{limit-suma_m:.2f} limitu")

    # Szybkie dodawanie
    st.subheader("🚀 Dodaj")
    kategorie = {"Jedzenie": "🍕", "Transport": "🚗", "Dom": "🏠", "Rozrywka": "🎬", "Inne": "📦"}

    cols = st.columns(len(kategorie))
    if 'selected_kat' not in st.session_state:
        st.session_state.selected_kat = "Jedzenie"

    for i, (nazwa, ikona) in enumerate(kategorie.items()):
        if cols[i].button(f"{ikona}\n{nazwa}"):
            st.session_state.selected_kat = nazwa

    st.caption(f"Wybrano: {st.session_state.selected_kat}")

    with st.form("form_dodaj", clear_on_submit=True):
        co = st.text_input("Nazwa")
        ile = st.number_input("Kwota (zł)", min_value=0.0, step=0.01)
        if st.form_submit_button("ZAPISZ 🚀"):
            if co and ile > 0:
                supabase.table("wydatki").insert({
                    "kategoria": st.session_state.selected_kat, 
                    "produkt": co, 
                    "cena": ile
                }).execute()
                st.rerun()

    # Historia
    st.divider()
    if not df_view.empty:
        for _, row in df_view.sort_values("id", ascending=False).iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.write(f"**{row['produkt']}**")
                c1.caption(f"{row['kategoria']}")
                c2.write(f"{row['cena']:.2f} zł")
                if c3.button("❌", key=f"del_{row['id']}"):
                    usun_wydatek(row['id'])
    else:
        st.info("Brak wydatków w tym miesiącu.")

# --- ZAKŁADKA 2: WYKRESY ---
with tab_wykresy:
    st.subheader(f"Analiza wydatków za {wybrany_miesiac}")
    
    if not df_view.empty:
        # Wykres kołowy (Donut chart)
        fig = px.pie(
            df_view, 
            values='cena', 
            names='kategoria', 
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        # Centrowanie legendy i dopasowanie marginesów
        fig.update_layout(
            margin=dict(t=0, b=0, l=0, r=0),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Prosta tabelka z podsumowaniem pod wykresem
        st.divider()
        summary = df_view.groupby("kategoria")["cena"].sum().reset_index().sort_values(by="cena", ascending=False)
        st.dataframe(summary, hide_index=True, use_container_width=True)
    else:
        st.info("Dodaj pierwsze wydatki, aby zobaczyć wykres!")
