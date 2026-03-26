import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime

# --- 1. KONFIGURACJA ---
st.set_page_config(page_title="Portfel", page_icon="💰", layout="centered")

# --- ZAAWANSOWANY CSS DLA MOBILE ---
st.markdown("""
    <style>
    /* 1. Usunięcie marginesów głównych */
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    
    /* 2. WYMUSZENIE POZIOMEGO UKŁADU KOLUMN NA MOBILE */
    [data-testid="column"] {
        flex: 1 1 auto !important;
        min-width: 0px !important;
    }
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 4px !important;
    }

    /* 3. Przyciski kategorii - ładniejsze i równe */
    div.stButton > button {
        width: 100% !important;
        aspect-ratio: 1/1 !important; /* Kwadratowe przyciski */
        padding: 0px !important;
        font-size: 11px !important;
        border-radius: 12px !important;
        border: 1px solid #f0f2f6 !important;
        transition: 0.3s;
    }
    div.stButton > button:active {
        background-color: #ff4b4b !important;
        color: white !important;
    }

    /* 4. Kompaktowa lista wydatków */
    .expense-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 5px;
        border-bottom: 1px solid #eee;
    }
    .expense-info { flex-grow: 1; }
    .expense-price { font-weight: bold; margin-right: 15px; }
    
    /* Stylizacja przycisku X wewnątrz listy */
    .stButton > button[kind="secondary"] {
        height: 30px !important;
        width: 30px !important;
        line-height: 1 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. POŁĄCZENIE (bez zmian) ---
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
            df["created_at"] = pd.to_datetime(df.get("created_at", datetime.now().isoformat()))
            df["miesiac"] = df["created_at"].dt.strftime('%Y-%m')
        return df
    except:
        return pd.DataFrame(columns=["id", "kategoria", "produkt", "cena", "miesiac"])

def usun_wydatek(row_id):
    supabase.table("wydatki").delete().eq("id", row_id).execute()
    st.rerun()

def wybierz_kategorie(nazwa):
    st.session_state.selected_kat = nazwa

# --- 4. LOGIKA APLIKACJI ---
df = fetch_data()
if 'selected_kat' not in st.session_state:
    st.session_state.selected_kat = "Jedzenie"

st.title("💰 Mój Portfel")

tab_dodaj, tab_wykres = st.tabs(["➕ Dodaj", "📊 Wykres"])

with tab_dodaj:
    # Wybór miesiąca i Suma w jednej linii dla oszczędności miejsca
    c_m1, c_m2 = st.columns([1, 1])
    if not df.empty:
        lista_m = sorted(df["miesiac"].unique(), reverse=True)
        wybrany_m = c_m1.selectbox("Miesiąc", lista_m, label_visibility="collapsed")
        df_v = df[df["miesiac"] == wybrany_m]
    else:
        wybrany_m = datetime.now().strftime('%Y-%m')
        df_v = df
    
    suma = df_v['cena'].sum() if not df_v.empty else 0.0
    c_m2.markdown(f"<h3 style='text-align:right; margin:0;'>{suma:.2f} zł</h3>", unsafe_allow_html=True)

    st.write("---")

    # KATEGORIE - ikony w jednym rzędzie
    kategorie = {"Jedzenie": "🍕", "Transport": "🚗", "Dom": "🏠", "Rozrywka": "🎬", "Inne": "📦"}
    cols = st.columns(len(kategorie))
    for i, (nazwa, ikona) in enumerate(kategorie.items()):
        # Podświetlenie wybranej kategorii
        style = "primary" if st.session_state.selected_kat == nazwa else "secondary"
        cols[i].button(f"{ikona}\n{nazwa}", key=f"btn_{nazwa}", on_click=wybierz_kategorie, args=(nazwa,), type=style)

    # Formularz dodawania
    with st.container():
        st.markdown(f"<div style='text-align:center; padding:10px;'>Wybrano: <b>{st.session_state.selected_kat}</b></div>", unsafe_allow_html=True)
        with st.form("dodaj", clear_on_submit=True):
            c1, c2 = st.columns([2, 1])
            co = c1.text_input("Nazwa", placeholder="np. Kawa", label_visibility="collapsed")
            ile = c2.number_input("zł", min_value=0.0, step=1.0, label_visibility="collapsed")
            if st.form_submit_button("DODAJ WYDATEK 🚀", use_container_width=True):
                if co and ile > 0:
                    supabase.table("wydatki").insert({"kategoria": st.session_state.selected_kat, "produkt": co, "cena": ile}).execute()
                    st.rerun()

    st.subheader("📜 Ostatnie")
    if not df_v.empty:
        # Sortowanie od najnowszych
        for _, row in df_v.sort_values("id", ascending=False).iterrows():
            # Czysty HTML dla maksymalnej kontroli nad linią
            c1, c2, c3 = st.columns([4, 2, 1])
            c1.markdown(f"<div style='padding-top:5px;'>{row['produkt']}</div>", unsafe_allow_html=True)
            c2.markdown(f"<div style='padding-top:5px; font-weight:bold;'>{row['cena']:.2f}zł</div>", unsafe_allow_html=True)
            if c3.button("✕", key=f"del_{row['id']}"):
                usun_wydatek(row['id'])
            st.markdown("<hr style='margin:0px; opacity:0.1'>", unsafe_allow_html=True)

with tab_wykres:
    if not df_v.empty:
        fig = px.pie(df_v, values='cena', names='kategoria', hole=0.5)
        fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
