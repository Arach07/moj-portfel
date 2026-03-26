import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime

# --- 1. KONFIGURACJA ---
st.set_page_config(page_title="Portfel", page_icon="💰", layout="centered")

# --- STABILNY CSS DLA MOBILE ---
st.markdown("""
    <style>
    /* Usuwamy zbędne odstępy */
    .block-container { padding: 1rem 0.5rem !important; }
    
    /* SIATKA KATEGORII - 3 w rzędzie, stabilne */
    .category-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        margin-bottom: 20px;
    }
    
    /* Stylizacja przycisków Streamlit, aby wyglądały jak kafelki */
    div.stButton > button {
        width: 100% !important;
        height: 60px !important;
        padding: 5px !important;
        border-radius: 10px !important;
        font-size: 12px !important;
        line-height: 1.2 !important;
    }

    /* Naprawa formularza - żeby inputy nie nachodziły na siebie */
    [data-testid="stHorizontalBlock"] {
        gap: 10px !important;
    }

    /* Lista wydatków - schludne rzędy */
    .expense-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid #f0f2f6;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. POŁĄCZENIE ---
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

# --- 4. START ---
df = fetch_data()
if 'selected_kat' not in st.session_state:
    st.session_state.selected_kat = "Jedzenie"

st.title("💰 Mój Portfel")

tab_dodaj, tab_wykres = st.tabs(["➕ Dodaj", "📊 Wykres"])

with tab_dodaj:
    # --- Nagłówek i Suma ---
    if not df.empty:
        lista_m = sorted(df["miesiac"].unique(), reverse=True)
        wybrany_m = st.selectbox("Miesiąc", lista_m, label_visibility="collapsed")
        df_v = df[df["miesiac"] == wybrany_m]
    else:
        wybrany_m = datetime.now().strftime('%Y-%m')
        df_v = df

    suma = df_v['cena'].sum() if not df_v.empty else 0.0
    st.markdown(f"<h2 style='text-align: center; color: #1E88E5;'>{suma:.2f} zł</h2>", unsafe_allow_html=True)

    # --- KATEGORIE (UKŁAD 3x2) ---
    st.write("Wybierz kategorię:")
    kategorie = {"Jedzenie": "🍕", "Transport": "🚗", "Dom": "🏠", "Rozrywka": "🎬", "Inne": "📦", "Zdrowie": "💊"}
    
    # Używamy kolumn, ale ograniczamy ich liczbę do 3 w rzędzie dla stabilności
    cat_cols = st.columns(3)
    for i, (nazwa, ikona) in enumerate(kategorie.items()):
        col_idx = i % 3
        with cat_cols[col_idx]:
            is_selected = st.session_state.selected_kat == nazwa
            if st.button(f"{ikona}\n{nazwa}", key=f"btn_{nazwa}", type="primary" if is_selected else "secondary"):
                st.session_state.selected_kat = nazwa
                st.rerun()

    st.markdown(f"<p style='text-align: center;'>Wybrano: <b>{st.session_state.selected_kat}</b></p>", unsafe_allow_html=True)

    # --- FORMULARZ (Poprawiony układ) ---
    with st.form("dodaj_form", clear_on_submit=True):
        f1, f2 = st.columns([3, 2])
        co = f1.text_input("Co kupiłeś?", placeholder="Kawa")
        ile = f2.number_input("Ile (zł)", min_value=0.0, step=0.5)
        submit = st.form_submit_button("DODAJ WYDATEK 🚀", use_container_width=True)
        
        if submit:
            if co and ile > 0:
                supabase.table("wydatki").insert({
                    "kategoria": st.session_state.selected_kat, 
                    "produkt": co, 
                    "cena": ile
                }).execute()
                st.rerun()

    # --- LISTA (Prosta i czytelna) ---
    st.subheader("📜 Ostatnie")
    if not df_v.empty:
        for _, row in df_v.sort_values("id", ascending=False).iterrows():
            # Używamy kolumn z większym marginesem na przycisk
            l1, l2, l3 = st.columns([4, 3, 1])
            l1.write(f"**{row['produkt']}**")
            l2.write(f"{row['cena']:.2f} zł")
            if l3.button("✕", key=f"del_{row['id']}"):
                usun_wydatek(row['id'])
            st.markdown("---")

with tab_wykres:
    if not df_v.empty:
        fig = px.pie(df_v, values='cena', names='kategoria', hole=0.4)
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
