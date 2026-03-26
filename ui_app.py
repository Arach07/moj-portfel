import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

# --- KONFIGURACJA ---
st.set_page_config(page_title="Mój Portfel", page_icon="💰", layout="centered")

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
        return df
    except:
        return pd.DataFrame(columns=["id", "kategoria", "produkt", "cena"])

def usun_wydatek(row_id):
    supabase.table("wydatki").delete().eq("id", row_id).execute()
    st.rerun()

# --- UI GŁÓWNE ---
st.title("💰 Mój Portfel")

# --- SEKCJA BUDŻETU ---
with st.expander("💳 Ustawienia Budżetu", expanded=False):
    col_b1, col_b2 = st.columns(2)
    zarobki = col_b1.number_input("Twoje zarobki (zł)", value=7000.0, step=100.0)
    limit_wydatkow = col_b2.number_input("Limit na wydatki (zł)", value=3000.0, step=100.0)

df = fetch_data()
suma_wydatkow = df['cena'].sum() if not df.empty else 0.0
zostalo_z_limitu = limit_wydatkow - suma_wydatkow
oszczednosci = zarobki - suma_wydatkow

# --- DASHBOARD NA GÓRZE ---
c1, c2, c3 = st.columns(3)
c1.metric("Wydano", f"{suma_wydatkow:.2f} zł")
c2.metric("Z limitu", f"{zostalo_z_limitu:.2f} zł", delta=float(zostalo_z_limitu), delta_color="normal")
c3.metric("Oszczędności", f"{oszczednosci:.2f} zł")

# Wykres (tylko jeśli są dane)
if not df.empty:
    fig = px.pie(df, values='cena', names='kategoria', hole=0.5,
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- FORMULARZ DODAWANIA ---
st.subheader("➕ Dodaj nowy wydatek")
with st.form("dodaj_form", clear_on_submit=True):
    kat = st.selectbox("Kategoria", ["Jedzenie", "Dom", "Transport", "Rozrywka", "Inne"])
    co = st.text_input("Co kupiłeś?")
    ile = st.number_input("Kwota (zł)", min_value=0.0, step=0.01)
    
    if st.form_submit_button("Zapisz wydatek 🚀"):
        if co and ile > 0:
            supabase.table("wydatki").insert({
                "kategoria": kat, 
                "produkt": co, 
                "cena": ile
            }).execute()
            st.rerun()

st.divider()

# --- LISTA WYDATKÓW (PONIŻEJ) ---
st.subheader("📜 Ostatnie wydatki")
if not df.empty:
    # Sortowanie od najnowszego
    df_sorted = df.sort_values(by="id", ascending=False)
    
    for index, row in df_sorted.iterrows():
        with st.container(border=True):
            col_text, col_price, col_del = st.columns([3, 2, 1])
            with col_text:
                st.write(f"**{row['produkt']}**")
                st.caption(f"{row['kategoria']}")
            with col_price:
                st.write(f"{row['cena']:.2f} zł")
            with col_del:
                # Przycisk usuwania dopasowany do ID z Supabase
                if st.button("❌", key=f"del_{row['id']}"):
                    usun_wydatek(row['id'])
else:
    st.info("Brak wpisów. Zacznij oszczędzać!")
