import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="Portfel PRO", page_icon="💳", layout="centered")

# --- 🔥 DARK UI ---
st.markdown("""
<style>

/* Tło */
body, .stApp {
    background-color: #0f1117;
    color: white;
}

/* Kontener */
.block-container {
    padding: 1rem 0.6rem !important;
}

/* KARTY */
.card {
    background: #1a1d26;
    padding: 12px;
    border-radius: 14px;
    margin-bottom: 10px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}

/* SUMA */
.big-number {
    font-size: 28px;
    font-weight: 600;
    text-align: center;
}

/* Kategorie */
div.stButton > button {
    width: 100%;
    height: 52px;
    border-radius: 12px;
    background: #1a1d26;
    color: white;
    border: 1px solid #2a2f3a;
    font-size: 12px;
}

/* Kliknięta kategoria */
div.stButton > button:focus {
    border: 2px solid #4da3ff;
    background: #162033;
}

/* Input */
input {
    background: #1a1d26 !important;
    color: white !important;
    border-radius: 10px !important;
}

/* Separator */
hr {
    border: none;
    border-top: 1px solid #2a2f3a;
    margin: 6px 0;
}

/* Lista */
.item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0;
}

.price {
    color: #4da3ff;
    font-weight: 500;
}

</style>
""", unsafe_allow_html=True)

# --- SUPABASE ---
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
            df["created_at"] = pd.to_datetime(df.get("created_at", datetime.now().isoformat()))
            df["miesiac"] = df["created_at"].dt.strftime('%Y-%m')
        return df
    except:
        return pd.DataFrame(columns=["id","kategoria","produkt","cena","miesiac"])

def usun(row_id):
    supabase.table("wydatki").delete().eq("id", row_id).execute()
    st.rerun()

def wybierz(k):
    st.session_state.kat = k

# --- STATE ---
df = fetch_data()
if "kat" not in st.session_state:
    st.session_state.kat = "Jedzenie"

# --- HEADER ---
st.markdown("<h2 style='text-align:center;'>💳 Mój Portfel</h2>", unsafe_allow_html=True)

# --- MIESIĄC ---
if not df.empty:
    m = sorted(df["miesiac"].unique(), reverse=True)
    sel = st.selectbox("Miesiąc", m, label_visibility="collapsed")
    df_v = df[df["miesiac"] == sel]
else:
    df_v = df

# --- 💳 KARTA SUMY ---
suma = df_v["cena"].sum() if not df_v.empty else 0

st.markdown(f"""
<div class="card">
    <div style="text-align:center; opacity:0.6;">Suma</div>
    <div class="big-number">{suma:.2f} zł</div>
</div>
""", unsafe_allow_html=True)

# --- KATEGORIE ---
kategorie = {
    "Jedzenie": "🍕",
    "Transport": "🚗",
    "Dom": "🏠",
    "Rozrywka": "🎬",
    "Inne": "📦"
}

cols = st.columns(len(kategorie))
for i,(nazwa,ikona) in enumerate(kategorie.items()):
    cols[i].button(f"{ikona} {nazwa}", on_click=wybierz, args=(nazwa,))

st.markdown(f"<div style='text-align:center; font-size:12px;'>Wybrano: <b>{st.session_state.kat}</b></div>", unsafe_allow_html=True)

# --- FORM ---
with st.form("f", clear_on_submit=True):
    c1,c2 = st.columns([3,2])
    co = c1.text_input("Nazwa", placeholder="np. Kawa")
    ile = c2.number_input("zł", min_value=0.0, step=0.01)

    if st.form_submit_button("Dodaj ➕", use_container_width=True):
        if co and ile>0:
            supabase.table("wydatki").insert({
                "kategoria": st.session_state.kat,
                "produkt": co,
                "cena": ile
            }).execute()
            st.rerun()

# --- LISTA ---
st.markdown("<br><b>📜 Ostatnie</b>", unsafe_allow_html=True)

if not df_v.empty:
    for _,row in df_v.sort_values("id", ascending=False).iterrows():
        c1,c2,c3 = st.columns([4,2,1])

        c1.markdown(f"<div class='item'><span>{row['produkt']}</span></div>", unsafe_allow_html=True)
        c2.markdown(f"<span class='price'>{row['cena']:.2f} zł</span>", unsafe_allow_html=True)

        if c3.button("❌", key=row["id"]):
            usun(row["id"])

        st.markdown("<hr>", unsafe_allow_html=True)

# --- WYKRES ---
st.markdown("<br><b>📊 Wykres</b>", unsafe_allow_html=True)

if not df_v.empty:
    fig = px.pie(df_v, values="cena", names="kategoria", hole=0.6)

    fig.update_layout(
        paper_bgcolor="#0f1117",
        plot_bgcolor="#0f1117",
        font_color="white",
        margin=dict(t=10,b=10,l=10,r=10)
    )

    st.plotly_chart(fig, use_container_width=True)
