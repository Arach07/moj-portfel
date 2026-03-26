import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from supabase import create_client, Client

# --- KONFIGURACJA ---
st.set_page_config(page_title="Mój Portfel Mobilny", page_icon="💰", layout="centered")

# Połączenie z Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- FUNKCJE BAZY DANYCH ---
def fetch_data():
    try:
        # Pobieramy wszystko, w tym ukryte 'id' do usuwania
        res = supabase.table("wydatki").select("*").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            df["cena"] = pd.to_numeric(df["cena"])
        return df
    except:
        return pd.DataFrame(columns=["id", "kategoria", "produkt", "cena"])

def usun_wydatek(row_id):
    try:
        supabase.table("wydatki").delete().eq("id", row_id).execute()
        st.success("Usunięto!")
        st.rerun()
    except Exception as e:
        st.error(f"Błąd usuwania: {e}")

# --- UI ---
st.title("💰 Mój Portfel")

df = fetch_data()

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "➕ Dodaj", "📜 Historia"])

with tab1:
    if not df.empty:
        suma = df['cena'].sum()
        st.metric("Suma całkowita", f"{suma:.2f} zł")
        fig = px.pie(df, values='cena', names='kategoria', hole=0.4, 
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Brak danych. Dodaj coś!")

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
                st.rerun()

with tab3:
    st.subheader("Lista wydatków")
    if not df.empty:
        # Wyświetlamy od najnowszego (najwyższe ID na górze)
        df_sorted = df.sort_values(by="id", ascending=False)
        
        for index, row in df_sorted.iterrows():
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**{row['produkt']}**")
                    st.caption(f"{row['kategoria']}")
                
                with col2:
                    st.write(f"{row['cena']:.2f} zł")
                
                with col3:
                    # Przycisk usuwania - używa ID z bazy danych
                    if st.button("❌", key=f"del_{row['id']}"):
                        usun_wydatek(row['id'])
    else:
        st.write("Historia jest pusta.")

# Przycisk "Wyczyść wszystko" przeniosłem do bocznego paska, żeby nie przeszkadzał
if st.sidebar.button("⚠️ WYCZYŚĆ CAŁĄ BAZĘ"):
    if st.sidebar.checkbox("Potwierdzam usunięcie wszystkiego"):
        supabase.table("wydatki").delete().neq("id", 0).execute()
        st.rerun()
