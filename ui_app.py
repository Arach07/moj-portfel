import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Mój Portfel Mobilny", page_icon="📱")

# --- INICJALIZACJA DANYCH W PAMIĘCI ---
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Data", "Kategoria", "Produkt", "Cena"])

# --- FUNKCJA DO EXCELA (W RAMACH PAMIĘCI) ---
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# --- UI ---
st.title("📱 Portfel w Telefonie")

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "➕ Wydatki", "💾 Kopia Zapasowa"])

with tab1:
    df = st.session_state.df
    if not df.empty:
        df["Cena"] = pd.to_numeric(df["Cena"])
        st.metric("Suma wydatków", f"{df['Cena'].sum():.2f} zł")
        fig = px.pie(df, values='Cena', names='Kategoria', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Brak danych. Wgraj plik lub dodaj wydatki.")

with tab2:
    with st.form("dodaj_form", clear_on_submit=True):
        kat = st.selectbox("Kategoria", ["Jedzenie", "Dom", "Transport", "Rozrywka", "Inne"])
        co = st.text_input("Co kupiłeś?")
        ile = st.number_input("Kwota", min_value=0.0)
        if st.form_submit_button("Dodaj do listy"):
            nowy = pd.DataFrame([{"Data": datetime.now().strftime("%Y-%m-%d"), "Kategoria": kat, "Produkt": co, "Cena": ile}])
            st.session_state.df = pd.concat([st.session_state.df, nowy], ignore_index=True)
            st.rerun()

    st.divider()
    # Usuwanie przyciskami (działa na telefonie)
    for index, row in st.session_state.df.iloc[::-1].iterrows():
        cols = st.columns([3, 1, 1])
        cols[0].write(f"{row['Produkt']}")
        cols[1].write(f"{row['Cena']}zł")
        if cols[2].button("❌", key=f"del_{index}"):
            st.session_state.df = st.session_state.df.drop(index)
            st.rerun()

with tab3:
    st.subheader("💾 Zarządzanie danymi")
    
    # 1. POBIERANIE (Z komputera/serwera na telefon)
    excel_data = to_excel(st.session_state.df)
    st.download_button(
        label="📥 Pobierz kopię do pamięci telefonu",
        data=excel_data,
        file_name=f"wydatki_{datetime.now().strftime('%d_%m')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.divider()
    
    # 2. WGRYWANIE (Z telefonu do apki)
    uploaded_file = st.file_uploader("📂 Wgraj plik z pamięci telefonu", type="xlsx")
    if uploaded_file:
        st.session_state.df = pd.read_excel(uploaded_file)
        st.success("Dane wczytane!")
        st.rerun()

    if st.button("🔥 WYCZYŚĆ WSZYSTKO"):
        st.session_state.df = pd.DataFrame(columns=["Data", "Kategoria", "Produkt", "Cena"])
        st.rerun()