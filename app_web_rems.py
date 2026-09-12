import os
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="Gestione Turni REMS", layout="wide")

DB_OPERATORI = {
    "ALFONSO SANTANGELO": (5, 6), "ANTONELLA DI BAIA": (5, 5), 
    "ANTONIO LUBRANO": (5, 6), "DOMENICA VISCONTE": (3, 6), 
    "GENOVEFFA CAPUANO": (5, 3), "GIULIA ZITIELLO": (5, 5), 
    "MICHELA AIELLO": (5, 5), "MICHELE CARUSONE": (5, 5), 
    "NELLO ROMANUCCI": (5, 5), "PAOLA DE PASCALE": (5, 3), 
    "VALENTINA PEREZ": (5, 1), "VALENTINA ROCCO": (3, 3), 
    "VINCENZO INTESTINALE": (3, 3)
}
FASCE = ["09:00 - 14:00", "15:00 - 20:00"]
MAX_SLOTS = 5

# Dizionario stabile centralizzato per memorizzare i turni
if "archivio_turni_rems" not in st.session_state:
    st.session_state.archivio_turni_rems = {}

if "data_ancora" not in st.session_state:
    oggi = datetime.now()
    st.session_state.data_ancora = oggi - timedelta(days=oggi.weekday())

col_prev, col_testo, col_next = st.columns([1, 2, 1])

with col_prev:
    if st.button("◀ Settimana Prec.", key="nav_sf_prev", use_container_width=True):
        st.session_state.data_ancora -= timedelta(days=7)
        st.rerun()

with col_next:
    if st.button("Settimana Succ. ▶", key="nav_sf_next", use_container_width=True):
        st.session_state.data_ancora += timedelta(days=7)
        st.rerun()

date_sett = [st.session_state.data_ancora + timedelta(days=i) for i in range(7)]
lun_str = date_sett[0].strftime('%d/%m/%Y')
dom_str = date_sett[-1].strftime('%d/%m/%Y')

with col_testo:
    st.markdown(f"<h3 style='text-align:center; font-family:Arial;'>📅 SETTIMANA DAL {lun_str} AL {dom_str}</h3>", unsafe_allow_html=True)

g_nomi = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
lista_ops = [""] + list(DB_OPERATORI.keys())

st.markdown("### 🛠️ Inserimento Rapido Operatori")
st.write("Seleziona il giorno, l'orario e lo slot, poi scegli il nome e premi Salva.")

# Sistema di inserimento lineare a prova di loop
c1, c2, c3, c4 = st.columns(4)
with c1:
    ins_giorno = st.selectbox("1. Scegli il Giorno", options=[d.strftime("%Y-%m-%d") for d in date_sett], format_func=lambda x: g_nomi[[d.strftime("%Y-%m-%d") for d in date_sett].index(x)])
with c2:
    ins_fascia = st.selectbox("2. Scegli la Fascia", options=FASCE)
with c3:
    ins_slot = st.selectbox("3. Postazione / Riga", options=[f"Operatore {i+1}" for i in range(MAX_SLOTS)], index=0)
with c4:
    ins_operatore = st.selectbox("4. Seleziona Nominativo", options=lista_ops)

slot_idx = [f"Operatore {i+1}" for i in range(MAX_SLOTS)].index(ins_slot)

if st.button("💾 REGISTRA NOMINATIVO NEL TABELLONE", use_container_width=True, type="primary"):
    chiave_salvataggio = f"{ins_giorno}_{ins_fascia}_{slot_idx}"
    valore_nome = ins_operatore if ins_operatore != "" else "- Vuoto -"
    st.session_state.archivio_turni_rems[chiave_salvataggio] = valore_nome
    st.success(f"Registrato: {valore_nome} in data {ins_giorno}")
    st.rerun()
# --- RECUPERO DATI PER LE ANTEPRIME E LA STAMPA ---
dati_turni = {}
for dt in date_sett:
    k_g = dt.strftime("%Y-%m-%d")
    dati_turni[k_g] = {}
    for fas in FASCE:
        dati_turni[k_g][fas] = []
        for s in range(MAX_SLOTS):
            ch = f"{k_g}_{fas}_{s}"
            if ch in st.session_state.archivio_turni_rems:
                dati_turni[k_g][fas].append(st.session_state.archivio_turni_rems[ch])
            else:
                dati_turni[k_g][fas].append("- Vuoto -")

st.markdown("<br/><hr/>", unsafe_allow_html=True)
st.subheader("🖨️ Centro Stampa Documenti")
tab1, tab2 = st.tabs(["👁️ Visualizza Tabellone Settimanale", "📊 Visualizza Report Ore"])

with tab1:
    html_tab = f"<div id='sez_stampa_tab'><h2 style='text-align:center; font-family:Arial; color:#1F538D;'>PROGRAMMAZIONE TURNI REMS - SETTIMANA DAL {lun_str} AL {dom_str}</h2>"
    html_tab += "<table style='width:100%; border-collapse:collapse; font-family:Arial;'><tr><th style='background-color:#1F538D; color:white; padding:8px; border:1px solid #1F538D;'>Fascia Oraria</th>"
    for i, d in enumerate(date_sett):
        html_tab += f"<th style='background-color:#1F538D; color:white; padding:8px; border:1px solid #1F538D;'>{g_nomi[i]}<br/>{d.strftime('%d/%m')}</th>"
    html_tab += "</tr>"
    for fas in FASCE:
        bg = "#FFF1E0" if "09:00" in fas else "#F3E5F5"
        txt_orario = "dalle ore 09:00<br/>alle ore 14:00" if "09:00" in fas else "dalle ore 15:00<br/>alle ore 20:00"
        for s in range(MAX_SLOTS):
            f_txt = f"<b>{txt_orario}</b>" if s == 2 else ""
            html_tab += f"<tr style='background-color:{bg}; text-align:center;'><td style='padding:6px; border:1px solid #ddd; font-size:11px;'>{f_txt}</td>"
            for dt in date_sett:
                v = dati_turni[dt.strftime("%Y-%m-%d")][fas][s]
                if " " in v and v != "- Vuoto -":
                    parti_nome = v.split(" ", 1)
                    v_p = f"{parti_nome[0]}<br/>{parti_nome[1]}"
                else:
                    v_p = v if v != "- Vuoto -" else ""
                html_tab += f"<td style='padding:6px; border:1px solid #ddd; font-size:11px; color:black;'>{v_p}</td>"
            html_tab += "</tr>"
    html_tab += "</table></div>"
    st.markdown(html_tab, unsafe_allow_html=True)
    if st.button("🖨️ Stampa Tabellone (A4 Orizzontale)", key="btn_print_tab", use_container_width=True):
        st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

with tab2:
    t_c = {n: 0 for n in DB_OPERATORI.keys()}
    g_i = {n: list() for n in DB_OPERATORI.keys()}
    g_n_it = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
    for idx, dt in enumerate(date_sett):
        k_g = dt.strftime("%Y-%m-%d")
        for fas in FASCE:
            for s in range(MAX_SLOTS):
                op = dati_turni[k_g][fas][s]
                if op in t_c:
                    t_c[op] += 1
                    if g_n_it[idx] not in g_i[op]: g_i[op].append(g_n_it[idx])
                    
    html_rep = f"<div id='sez_stampa_rep'><h2 style='text-align:center; font-family:Arial; color:#1F538D;'>REPORT - PROGRAMMAZIONE TURNI REMS - SETTIMANA DAL {lun_str} AL {dom_str}</h2>"
    html_rep += "<table style='width:100%; border-collapse:collapse; font-family:Arial;'><tr style='background-color:#1F538D; color:white;'><th style='padding:10px;'>OPERATORE</th><th style='padding:10px;'>ORE S.</th><th style='padding:10px;'>PREV.</th><th style='padding:10px;'>EFF.</th><th style='padding:10px;'>GIORNI IMPIEGATI</th><th style='padding:10px;'>ORE TOTALI</th></tr>"
    for op, (ore_g, da_f) in DB_OPERATORI.items():
        reg = t_c[op]
        sg = ", ".join(g_i[op]) if g_i[op] else "-"
        if reg > 0:
            if " " in op:
                parti_op = op.split(" ", 1)
                op_p = f"{parti_op[0]}<br/>{parti_op[1]}"
            else:
                op_p = op
            html_rep += f"<tr style='text-align:center;'><td style='padding:8px; border:1px solid #ccc; text-align:left; font-weight:bold; font-size:12px; color:black;'>{op_p}</td><td style='padding:8px; border:1px solid #ccc; color:black;'>{ore_g}</td><td style='padding:8px; border:1px solid #ccc; color:black;'>{da_f}</td><td style='padding:8px; border:1px solid #ccc; color:black;'>{reg}</td><td style='padding:8px; border:1px solid #ccc; color:black;'>{sg}</td><td style='padding:8px; border:1px solid #ccc; color:#1F538D; font-size:12px;'><b>{reg*ore_g} ore</b></td></tr>"
    html_rep += "</table></div>"
    st.markdown(html_rep, unsafe_allow_html=True)
    if st.button("📊 Stampa Report Ore (A4 Verticale)", key="btn_print_rep", use_container_width=True):
        st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

st.markdown("""
<style>
@media print {
    [data-testid="stSidebar"], [data-testid="stHeader"], .stActionButton, .stSelectbox, div.element-container, div.stBlock, button { display: none !important; }
    iframe, hr { display: none !important; }
    body { background: white; color: black; }
}
</style>
""", unsafe_allow_html=True)
