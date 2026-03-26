import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Szybki Portfel", page_icon="⚡", layout="centered")

# --- 2. CSS DLA STYLU "DARK PREMIUM" ---
st.markdown("""
    <style>
    /* Tło całej aplikacji */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    
    /* Stylizacja kart (kontenerów) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        border-radius: 15px !important;
        padding: 15px !important;
    }

    /* Przyciski kategorii */
    div.stButton > button {
        background-color: #21262D !important;
        color: white !important;
        border: 1px solid #30363D !important;
        border-radius: 12px !important;
        height: 60px !important;
        font-weight: 600 !important;
        transition: 0.3s;
    }
    
    div.stButton > button:hover {
        border-color: #58A6FF !important;
        background-color: #30363D !important;
    }

    /* Układ ikon obok siebie */
    [data-testid="column"] {
        width: calc(20% - 5px) !important;
        flex: 1 1 calc(20% - 5px) !important;
        min-width: 0px !important;
    }
    
    [data-testid="stHorizontalBlock"] {
        gap: 5px !important;
    }

    /* Stylizacja pól tekstowych */
    .stTextInput input, .stNumberInput input {
        background-color: #0D1117 !important;
        color: white !important;
        border: 1px solid #30363D !important;
        border-radius: 10px !important;
    }

    /* Ukrycie dekoracji Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. POŁĄCZENIE Z SUPABASE ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 4. FUNKCJE ---
def fetch_data():
    try:
        res = supabase.table("wydatki").select("*").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            df["cena"] = pd.to_numeric(df["cena"])
            df["created_at"] = pd.to_datetime(df.get("created_at", datetime.now().isoformat()))
            df["miesiac"] = df["created_at"].dt.strftime('%Y-%m')
        return df
    except:
        return pd.DataFrame(columns=["id", "kategoria", "produkt", "cena", "miesiac"])

def usun_wydatek(row_id):
    supabase.table("wydatki").delete().eq("id", row_id).execute()
    st.rerun()

# --- 5. LOGIKA ---
df = fetch_data()
if 'selected_kat' not in st.session_state:
    st.session_state.selected_kat = "Jedzenie"

# --- 6. INTERFEJS ---
st.title("💰 Mój Portfel")

tab_dodaj, tab_wykresy = st.tabs(["➕ Dodaj", "📊 Wykresy"])

with tab_dodaj:
    # Filtrowanie i Metryki
    if not df.empty:
        lista_m = sorted(df["miesiac"].unique(), reverse=True)
        wybrany_m = st.selectbox("Wybierz miesiąc", lista_m, label_visibility="collapsed")
        df_v = df[df["miesiac"] == wybrany_m]
    else:
        wybrany_m = datetime.now().strftime('%Y-%m')
        df_v = df

    suma = df_v['cena'].sum() if not df_v.empty else 0.0
    st.metric("Całkowite wydatki", f"{suma:.2f} zł")

    # Ikony Kategorii
    st.write("Kategoria:")
    kategorie = {"Jedzenie": "🍕", "Transport": "🚗", "Dom": "🏠", "Rozrywka": "🎬", "Inne": "📦"}
    cols = st.columns(len(kategorie))
    for i, (nazwa, ikona) in enumerate(kategorie.items()):
        if cols[i].button(f"{ikona}\n{nazwa}"):
            st.session_state.selected_kat = nazwa

    st.markdown(f"<p style='color: #8B949E; font-size: 0.9em;'>Wybrano: <b style='color: #58A6FF;'>{st.session_state.selected_kat}</b></p>", unsafe_allow_html=True)

    # Formularz
    with st.form("dodaj_form", clear_on_submit=True):
        co = st.text_input("Nazwa wydatku", placeholder="Np. Zakupy Biedronka")
        ile = st.number_input("Kwota (zł)", min_value=0.0, step=0.01)
        if st.form_submit_button("DODAJ DO PORTFELA", use_container_width=True):
            if co and ile > 0:
                supabase.table("wydatki").insert({
                    "kategoria": st.session_state.selected_kat, 
                    "produkt": co, 
                    "cena": ile
                }).execute()
                st.rerun()

    # Historia
    st.subheader("Ostatnie transakcje")
    if not df_v.empty:
        for _, row in df_v.sort_values("id", ascending=False).iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.markdown(f"**{row['produkt']}**\n<small style='color: #8B949E;'>{row['kategoria']}</small>", unsafe_allow_html=True)
                c2.markdown(f"<h4 style='margin:0;'>{row['cena']:.2f} zł</h4>", unsafe_allow_html=True)
                if c3.button("❌", key=f"del_{row['id']}"):
                    usun_wydatek(row['id'])
    else:
        st.info("Brak wpisów.")

with tab_wykresy:
    if not df_v.empty:
        fig = px.pie(df_v, values='cena', names='kategoria', hole=0.6,
                     color_discrete_sequence=px.colors.qualitative.G10)
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color="white",
            margin=dict(t=0, b=0, l=0, r=0)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Brak danych do wykresu.")
