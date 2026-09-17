import os
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from sqlalchemy import text

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

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

if "data_ancora" not in st.session_state:
    oggi = datetime.now()
    st.session_state.data_ancora = oggi - timedelta(days=oggi.weekday())

col_prev, col_testo, col_next = st.columns()

with col_prev:
    if st.button("◀ Settimana Prec.", key="nav_sf_prev", use_container_width=True):
        st.session_state.data_ancora -= timedelta(days=7)
        st.rerun()

with col_next:
    if st.button("Settimana Succ. ▶", key="nav_sf_next", use_container_width=True):
        st.session_state.data_ancora += timedelta(days=7)
        st.rerun()

date_sett = [st.session_state.data_ancora + timedelta(days=i) for i in range(7)]
lun_str = date_sett.strftime('%d/%m/%Y')
dom_str = date_sett[-1].strftime('%d/%m/%Y')

with col_testo:
    st.markdown(f"<h3 style='text-align:center; font-family:Arial;'>📅 SETTIMANA DAL {lun_str} AL {dom_str}</h3>", unsafe_allow_html=True)

# Connessione al database cloud protetto
conn = st.connection("sql")

# Inizializza l'archivio sul server internet
with conn.session as session:
    session.execute(text("CREATE TABLE IF NOT EXISTS turni_rems (chiave TEXT PRIMARY KEY, operatore TEXT);"))
    session.commit()

# Lettura in tempo reale condivisa
def carica_turni_settimana(date_list):
    dati = {dt.strftime("%Y-%m-%d"): {f: ["- Vuoto -"] * MAX_SLOTS for f in FASCE} for dt in date_list}
    try:
        df = conn.query("SELECT chiave, operatore FROM turni_rems;", ttl=0)
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                ch = str(row["chiave"]).strip()
                op = str(row["operatore"]).strip()
                if "_" in ch:
                    parti = ch.split("_")
                    g_data = parti
                    if g_data in dati:
                        f_orario = "09:00 - 14:00" if "09_00" in ch else "15:00 - 20:00"
                        s_idx = int(parti[-1])
                        if s_idx < MAX_SLOTS:
                            dati[g_data][f_orario][s_idx] = op
    except Exception:
        pass
    return dati

dati_turni = carica_turni_settimana(date_sett)
lista_ops = ["- Vuoto -"] + list(DB_OPERATORI.keys())
g_nomi = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]

st.markdown("<br/>", unsafe_allow_html=True)

# Scrittura immediata sul Cloud condiviso
def salva_turno_callback(chiave_widget, data_g, fascia, slot):
    scelta_attuale = st.session_state[chiave_widget]
    f_p = fascia.replace(" ", "").replace(":", "_").replace("-", "_")
    chiave_unica = f"{data_g}_{f_p}_{slot}"
    with conn.session as session:
        session.execute(text("DELETE FROM turni_rems WHERE chiave = :chiave;"), {"chiave": chiave_unica})
        if scelta_attuale != "- Vuoto -":
            session.execute(text("INSERT INTO turni_rems (chiave, operatore) VALUES (:chiave, :operatore);"), {"chiave": chiave_unica, "operatore": scelta_attuale})
        session.commit()

colonne_giorni = st.columns(7)
for idx, dt in enumerate(date_sett):
    k_g = dt.strftime("%Y-%m-%d")
    with colonne_giorni[idx]:
        st.markdown(f"<div style='text-align:center; background-color:#1F538D; padding:8px; border-radius:6px; color:white; font-family:Arial; font-size:13px; font-weight:bold;'>{g_nomi[idx]}<br/>{dt.strftime('%d/%m')}</div>", unsafe_allow_html=True)
        for fas in FASCE:
            bg_c = "#FFF1E0" if "09:00" in fas else "#F3E5F5"
            st.markdown(f"<div style='background-color:{bg_c}; padding:4px; margin-top:8px; border-radius:4px; text-align:center; font-size:11px; font-weight:bold; color:#333; font-family:Arial;'>🕒 {fas}</div>", unsafe_allow_html=True)
            for s in range(MAX_SLOTS):
                valore_attuale = dati_turni[k_g][fas][s]
                def_idx = lista_ops.index(valore_attuale) if valore_attuale in lista_ops else 0
                ch_widget = f"w_sel_{k_g}_{fas.replace(' ', '').replace(':', '_').replace('-', '_')}_{s}"
                st.selectbox(
                    label=f"h_{ch_widget}", options=lista_ops, index=def_idx, key=ch_widget,
                    label_visibility="collapsed", on_change=salva_turno_callback, args=(ch_widget, k_g, fas, s)
                )

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
                    v_p = f"{parti_nome}<br/>{parti_nome}"
                else:
                    v_p = v if v != "- Vuoto -" else ""
                html_tab += f"<td style='padding:6px; border:1px solid #ddd; font-size:11px; color:black;'>{v_p}</td>"
            html_tab += "</tr>"
    html_tab += "</table></div><br/>"
    st.markdown(html_tab, unsafe_allow_html=True)
    
    if st.button("🖨️ Genera PDF Tabellone Settimanale", key="gen_pdf_tab_btn", use_container_width=True):
        path_tab = "Tabellone_Turni_REMS.pdf"
        doc_tab = SimpleDocTemplate(path_tab, pagesize=landscape(letter), leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
        elements_tab = list()
        styles_tab = getSampleStyleSheet()
        t_st_tab = ParagraphStyle('T', fontName='Helvetica-Bold', fontSize=11, alignment=1, spaceAfter=15)
        c_st_tab = ParagraphStyle('C', fontName='Helvetica', fontSize=8, alignment=1)
        h_st_tab = ParagraphStyle('H', fontName='Helvetica-Bold', fontSize=9, alignment=1, textColor=colors.white)
        
        elements_tab.append(Paragraph(f"PROGRAMMAZIONE TURNI REMS - SETTIMANA DAL {lun_str} AL {dom_str}", t_st_tab))
        headers_pdf = [Paragraph("Fascia Oraria", h_st_tab)]
        for i, d in enumerate(date_sett):
            headers_pdf.append(Paragraph(f"{g_nomi[i]} {d.strftime('%d/%m')}", h_st_tab))
        data_pdf = [headers_pdf]
        r_styles = [('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1F538D")), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#DDDDDD"))]
        
        r_idx = 1
        for fas in FASCE:
            bg_c = colors.HexColor("#FFF1E0") if "09:00" in fas else colors.HexColor("#F3E5F5")
            testo_orario = "dalle ore 09:00<br/>alle ore 14:00" if "09:00" in fas else "dalle ore 15:00<br/>alle ore 20:00"
            for s in range(MAX_SLOTS):
                f_txt = testo_orario if s == 2 else ""
                r = [Paragraph(f_txt, ParagraphStyle('F', fontName='Helvetica-Bold', fontSize=8, alignment=1))]
                for dt in date_sett:
                    v = dati_turni[dt.strftime("%Y-%m-%d")][fas][s]
                    testo_pulito = v if v != "- Vuoto -" else ""
                    if " " in testo_pulito:
                        p_n = testo_pulito.split(" ", 1)
                        testo_pulito = f"{p_n}<br/>{p_n}"
                    r.append(Paragraph(testo_pulito, c_st_tab))
                data_pdf.append(r)
                r_styles.append(('BACKGROUND', (0, r_idx), (-1, r_idx), bg_c))
                r_idx += 1
                
        w_cols = [110, 92, 92, 92, 92, 92, 92, 92]
        t_table = Table(data_pdf, colWidths=w_cols)
        t_table.setStyle(TableStyle(r_styles))
        elements_tab.append(t_table)
        doc_tab.build(elements_tab)
        with open(path_tab, "rb") as file:
            st.download_button(label="📥 Scarica il PDF del Tabellone", data=file, file_name=f"Tabellone_{lun_str.replace('/', '_')}.pdf", mime="application/pdf", use_container_width=True)

with tab2:
    t_c = {n: 0 for n in DB_OPERATORI.keys()}
    g_i = {n: list() for n in DB_OPERATORI.keys()}
    g_n_it = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
    for idx, dt in enumerate(date_sett):
        k_g = dt.strftime("%Y-%m-%d")
        for fas in FASCE:
            for s in range(MAX_SLOTS):
                op = dati_turni[k_g][fas][s]
import os
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from sqlalchemy import text

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

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

if "data_ancora" not in st.session_state:
    oggi = datetime.now()
    st.session_state.data_ancora = oggi - timedelta(days=oggi.weekday())

col_prev, col_testo, col_next = st.columns()

with col_prev:
    if st.button("◀ Settimana Prec.", key="nav_sf_prev", use_container_width=True):
        st.session_state.data_ancora -= timedelta(days=7)
        st.rerun()

with col_next:
    if st.button("Settimana Succ. ▶", key="nav_sf_next", use_container_width=True):
        st.session_state.data_ancora += timedelta(days=7)
        st.rerun()

date_sett = [st.session_state.data_ancora + timedelta(days=i) for i in range(7)]
lun_str = date_sett.strftime('%d/%m/%Y')
dom_str = date_sett[-1].strftime('%d/%m/%Y')

with col_testo:
    st.markdown(f"<h3 style='text-align:center; font-family:Arial;'>📅 SETTIMANA DAL {lun_str} AL {dom_str}</h3>", unsafe_allow_html=True)

# Connessione al database cloud protetto
conn = st.connection("sql")

# Inizializza l'archivio sul server internet
with conn.session as session:
    session.execute(text("CREATE TABLE IF NOT EXISTS turni_rems (chiave TEXT PRIMARY KEY, operatore TEXT);"))
    session.commit()

# Lettura in tempo reale condivisa
def carica_turni_settimana(date_list):
    dati = {dt.strftime("%Y-%m-%d"): {f: ["- Vuoto -"] * MAX_SLOTS for f in FASCE} for dt in date_list}
    try:
        df = conn.query("SELECT chiave, operatore FROM turni_rems;", ttl=0)
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                ch = str(row["chiave"]).strip()
                op = str(row["operatore"]).strip()
                if "_" in ch:
                    parti = ch.split("_")
                    g_data = parti
                    if g_data in dati:
                        f_orario = "09:00 - 14:00" if "09_00" in ch else "15:00 - 20:00"
                        s_idx = int(parti[-1])
                        if s_idx < MAX_SLOTS:
                            dati[g_data][f_orario][s_idx] = op
    except Exception:
        pass
    return dati

dati_turni = carica_turni_settimana(date_sett)
lista_ops = ["- Vuoto -"] + list(DB_OPERATORI.keys())
g_nomi = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]

st.markdown("<br/>", unsafe_allow_html=True)

# Scrittura immediata sul Cloud condiviso
def salva_turno_callback(chiave_widget, data_g, fascia, slot):
    scelta_attuale = st.session_state[chiave_widget]
    f_p = fascia.replace(" ", "").replace(":", "_").replace("-", "_")
    chiave_unica = f"{data_g}_{f_p}_{slot}"
    with conn.session as session:
        session.execute(text("DELETE FROM turni_rems WHERE chiave = :chiave;"), {"chiave": chiave_unica})
        if scelta_attuale != "- Vuoto -":
            session.execute(text("INSERT INTO turni_rems (chiave, operatore) VALUES (:chiave, :operatore);"), {"chiave": chiave_unica, "operatore": scelta_attuale})
        session.commit()

colonne_giorni = st.columns(7)
for idx, dt in enumerate(date_sett):
    k_g = dt.strftime("%Y-%m-%d")
    with colonne_giorni[idx]:
        st.markdown(f"<div style='text-align:center; background-color:#1F538D; padding:8px; border-radius:6px; color:white; font-family:Arial; font-size:13px; font-weight:bold;'>{g_nomi[idx]}<br/>{dt.strftime('%d/%m')}</div>", unsafe_allow_html=True)
        for fas in FASCE:
            bg_c = "#FFF1E0" if "09:00" in fas else "#F3E5F5"
            st.markdown(f"<div style='background-color:{bg_c}; padding:4px; margin-top:8px; border-radius:4px; text-align:center; font-size:11px; font-weight:bold; color:#333; font-family:Arial;'>🕒 {fas}</div>", unsafe_allow_html=True)
            for s in range(MAX_SLOTS):
                valore_attuale = dati_turni[k_g][fas][s]
                def_idx = lista_ops.index(valore_attuale) if valore_attuale in lista_ops else 0
                ch_widget = f"w_sel_{k_g}_{fas.replace(' ', '').replace(':', '_').replace('-', '_')}_{s}"
                st.selectbox(
                    label=f"h_{ch_widget}", options=lista_ops, index=def_idx, key=ch_widget,
                    label_visibility="collapsed", on_change=salva_turno_callback, args=(ch_widget, k_g, fas, s)
                )

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
                    v_p = f"{parti_nome}<br/>{parti_nome}"
                else:
                    v_p = v if v != "- Vuoto -" else ""
                html_tab += f"<td style='padding:6px; border:1px solid #ddd; font-size:11px; color:black;'>{v_p}</td>"
            html_tab += "</tr>"
    html_tab += "</table></div><br/>"
    st.markdown(html_tab, unsafe_allow_html=True)
    
    if st.button("🖨️ Genera PDF Tabellone Settimanale", key="gen_pdf_tab_btn", use_container_width=True):
        path_tab = "Tabellone_Turni_REMS.pdf"
        doc_tab = SimpleDocTemplate(path_tab, pagesize=landscape(letter), leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
        elements_tab = list()
        styles_tab = getSampleStyleSheet()
        t_st_tab = ParagraphStyle('T', fontName='Helvetica-Bold', fontSize=11, alignment=1, spaceAfter=15)
        c_st_tab = ParagraphStyle('C', fontName='Helvetica', fontSize=8, alignment=1)
        h_st_tab = ParagraphStyle('H', fontName='Helvetica-Bold', fontSize=9, alignment=1, textColor=colors.white)
        
        elements_tab.append(Paragraph(f"PROGRAMMAZIONE TURNI REMS - SETTIMANA DAL {lun_str} AL {dom_str}", t_st_tab))
        headers_pdf = [Paragraph("Fascia Oraria", h_st_tab)]
        for i, d in enumerate(date_sett):
            headers_pdf.append(Paragraph(f"{g_nomi[i]} {d.strftime('%d/%m')}", h_st_tab))
        data_pdf = [headers_pdf]
        r_styles = [('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1F538D")), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#DDDDDD"))]
        
        r_idx = 1
        for fas in FASCE:
            bg_c = colors.HexColor("#FFF1E0") if "09:00" in fas else colors.HexColor("#F3E5F5")
            testo_orario = "dalle ore 09:00<br/>alle ore 14:00" if "09:00" in fas else "dalle ore 15:00<br/>alle ore 20:00"
            for s in range(MAX_SLOTS):
                f_txt = testo_orario if s == 2 else ""
                r = [Paragraph(f_txt, ParagraphStyle('F', fontName='Helvetica-Bold', fontSize=8, alignment=1))]
                for dt in date_sett:
                    v = dati_turni[dt.strftime("%Y-%m-%d")][fas][s]
                    testo_pulito = v if v != "- Vuoto -" else ""
                    if " " in testo_pulito:
                        p_n = testo_pulito.split(" ", 1)
                        testo_pulito = f"{p_n}<br/>{p_n}"
                    r.append(Paragraph(testo_pulito, c_st_tab))
                data_pdf.append(r)
                r_styles.append(('BACKGROUND', (0, r_idx), (-1, r_idx), bg_c))
                r_idx += 1
                
        w_cols = [110, 92, 92, 92, 92, 92, 92, 92]
        t_table = Table(data_pdf, colWidths=w_cols)
        t_table.setStyle(TableStyle(r_styles))
        elements_tab.append(t_table)
        doc_tab.build(elements_tab)
        with open(path_tab, "rb") as file:
            st.download_button(label="📥 Scarica il PDF del Tabellone", data=file, file_name=f"Tabellone_{lun_str.replace('/', '_')}.pdf", mime="application/pdf", use_container_width=True)

with tab2:
    t_c = {n: 0 for n in DB_OPERATORI.keys()}
    g_i = {n: list() for n in DB_OPERATORI.keys()}
    g_n_it = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
    for idx, dt in enumerate(date_sett):
        k_g = dt.strftime("%Y-%m-%d")
        for fas in FASCE:
            for s in range(MAX_SLOTS):
                op = dati_turni[k_g][fas][s]
