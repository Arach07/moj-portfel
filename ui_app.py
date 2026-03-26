import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from supabase import create_client, Client

# --- KONFIGURACJA ---
st.set_page_config(page_title="Mój Portfel Mobilny", page_icon="📱", layout="centered")

# Połączenie z Supabase (z Twoich Secrets)
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- FUNKCJE BAZY DANYCH ---
def fetch_data():
    try:
        res = supabase.table("wydatki").select("*").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            df["cena"] = pd.to_numeric(df["cena"])
        return df
    except:
        return pd.DataFrame(columns=["kategoria", "produkt", "cena"])

# --- UI ---
st.title("📱 Portfel w Chmurze")

# Pobieramy świeże dane przy każdym odświeżeniu
df = fetch_data()

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "➕ Dodaj", "📜 Historia"])

with tab1:
    if not df.empty:
        suma = df['cena'].sum()
        st.metric("Suma wydatków", f"{suma:.2f} zł")
        
        # Wykres kołowy (Plotly)
        fig = px.pie(df, values='cena', names='kategoria', hole=0.4, 
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Brak danych w bazie. Dodaj swój pierwszy wydatek!")

with tab2:
    st.subheader("Nowy wydatek")
    with st.form("dodaj_form", clear_on_submit=True):
        kat = st.selectbox("Kategoria", ["Jedzenie", "Dom", "Transport", "Rozrywka", "Inne"])
        co = st.text_input("Co kupiłeś?")
        ile = st.number_input("Kwota (zł)", min_value=0.0, step=0.01)
        
        if st.form_submit_button("Zapisz do bazy 🚀"):
            if co and ile > 0:
                supabase.table("wydatki").insert({
                    "kategoria": kat, 
                    "produkt": co, 
                    "cena": ile
                }).execute()
                st.success("Zapisano!")
                st.rerun()
            else:
                st.warning("Uzupełnij nazwę i kwotę!")

with tab3:
    st.subheader("Ostatnie wpisy")
    if not df.empty:
        # Wyświetlanie od najnowszego
        for index, row in df.iloc[::-1].iterrows():
            with st.container(border=True):
                col_a, col_b = st.columns([3, 1])
                col_a.write(f"**{row['produkt']}**")
                col_a.caption(f"{row['kategoria']}")
                col_b.write(f"{row['cena']:.2f} zł")
                
                # Przycisk usuwania (opcjonalnie, wymaga kolumny id)
                # if st.button("Usuń", key=f"del_{index}"):
                #     # Tu można dodać usuwanie po ID
                #     pass
    else:
        st.write("Lista jest pusta.")

# Sekcja resetu na samym dole
if st.sidebar.button("🔥 WYCZYŚĆ BAZĘ"):
    supabase.table("wydatki").delete().neq("kategoria", "brak").execute()
    st.rerun()
