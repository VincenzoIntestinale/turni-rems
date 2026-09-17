import os
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

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

# MOTORE DI LETTURA BLINDATO DA GOOGLE SHEETS
def carica_turni_settimana(date_list):
    dati = {dt.strftime("%Y-%m-%d"): {f: ["- Vuoto -"] * MAX_SLOTS for f in FASCE} for dt in date_list}
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl=0)
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                ch = str(row["chiave"]).strip()
                op = str(row["operatore"]).strip()
                if "_" in ch:
                    parti = ch.split("_")
                    g_data = parti[0]
                    if g_data in dati:
                        f_orario = f"{parti[1]}:{parti[2]} - {parti[3]}:{parti[4]}"
                        s_idx = int(parti[5])
                        if f_orario in dati[g_data] and s_idx < MAX_SLOTS:
                            dati[g_data][f_orario][s_idx] = op
    except Exception:
        pass
    return dati

dati_turni = carica_turni_settimana(date_sett)
lista_ops = ["- Vuoto -"] + list(DB_OPERATORI.keys())
g_nomi = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]

st.markdown("<br/>", unsafe_allow_html=True)

# MOTORE DI SCRITTURA CONDIVISO SENZA LOOP
def salva_turno_callback(chiave_widget, data_g, fascia, slot):
    scelta_attuale = st.session_state[chiave_widget]
    f_p = fascia.replace(" ", "").replace(":", "_").replace("-", "_")
    chiave_unica = f"{data_g}_{f_p}_{slot}"
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl=0)
        if df is None or df.empty:
            df = pd.DataFrame(columns=["chiave", "operatore"])
        df = df[df["chiave"].astype(str).str.strip() != chiave_unica]
        if scelta_attuale != "- Vuoto -":
            nuova_riga = pd.DataFrame([{"chiave": chiave_unica, "operatore": scelta_attuale}])
            df = pd.concat([df, nuova_riga], ignore_index=True)
        conn.update(data=df)
    except Exception:
        pass

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
                    label_visibility="collapsed", on_change=save_turno_callback if 'save_turno_callback' in globals() else salva_turno_callback, args=(ch_widget, k_g, fas, s)
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
                v_p = f"{v.split(' ')[0]}<br/>{v.split(' ')[1]}" if " " in v and v != "- Vuoto -" else (v if v != "- Vuoto -" else "")
                html_tab += f"<td style='padding:6px; border:1px solid #ddd; font-size:11px; color:black;'>{v_p}</td>"
            html_tab += "</tr>"
    html_tab += "</table></div><br/>"
    st.markdown(html_tab, unsafe_allow_html=True)
    
    if st.button("🖨️ Genera PDF Tabellone Settimanale", key="gen_pdf_tab_btn", use_container_width=True):
        path_tab = "Tabellone_Turni_REMS.pdf"
        doc_tab = SimpleDocTemplate(path_tab, pagesize=landscape(letter), leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
        elements_tab = []
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
                    testo_pulito = f"{v.split(' ')[0]}<br/>{v.split(' ')[1]}" if " " in v and v != "- Vuoto -" else (v if v != "- Vuoto -" else "")
                    r.append(Paragraph(testo_pulito, c_st_tab))
                data_pdf.append(r)
                r_styles.append(('BACKGROUND', (0, r_idx), (-1, r_idx), bg_c))
                r_idx += 1
                
        t_table = Table(data_pdf, colWidths=[90, 95, 95, 95, 95, 95, 95, 95])
        t_table.setStyle(TableStyle(r_styles))
        elements_tab.append(t_table)
        doc_tab.build(elements_tab)
        with open(path_tab, "rb") as file:
            st.download_button(label="📥 Scarica il PDF del Tabellone", data=file, file_name=f"Tabellone_{lun_str.replace('/', '_')}.pdf", mime="application/pdf", use_container_width=True)

with tab2:
    t_c = {n: 0 for n in DB_OPERATORI.keys()}
    g_i = {n: [] for n in DB_OPERATORI.keys()}
    g_n_it = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
    for idx, dt in enumerate(date_sett):
        k_g = dt.strftime("%Y-%m-%d")
        for fas in FASCE:
            for s in range(MAX_SLOTS):
                op = dati_turni[k_g][fas][s]
                if op in t_c:
                    t_c[op] += 1
                    if g_n_it[idx] not in g_i[op]: g_i[op].append(g_n_it[idx])
                    
html_rep = f"REPORT - TURNI REMS - DAL {lun_str} AL {dom_str}"
html_rep += "OPERATOREORE S.PREV.EFF.GIORNI IMPIEGATIORE TOTALI"
for op, (ore_g, da_f) in DB_OPERATORI.items():
    reg = t_c[op]
    sg = ", ".join(g_i[op]) if g_i[op] else "-"
    if reg > 0:
            op_p = f"{op.split(' ')[0]}{op.split(' ')[1]}" if " " in op else op
html_rep += f"{op_p}{ore_g}{da_f}{reg}{sg}{reg*ore_g} ore"
html_rep += ""
st.markdown(html_rep, unsafe_allow_html=True)
if st.button("📊 Genera PDF Report Ore", key="gen_pdf_rep_btn", use_container_width=True):
    path_rep = "Report_Ore_REMS.pdf"
    doc_rep = SimpleDocTemplate(path_rep, pagesize=letter, leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
    elements_rep = []
    styles_rep = getSampleStyleSheet()
    t_st_rep = ParagraphStyle('T', fontName='Helvetica-Bold', fontSize=11, alignment=1, spaceAfter=20)
    c_st_rep = ParagraphStyle('C', fontName='Helvetica', fontSize=9, alignment=1)
    h_st_rep = ParagraphStyle('H', fontName='Helvetica-Bold', fontSize=10, alignment=1, textColor=colors.white)
    elements_rep.append(Paragraph(f"REPORT - PROGRAMMAZIONE TURNI REMS - DAL {lun_str} AL {dom_str}", t_st_rep))
    headers_pdf = [Paragraph("OPERATORE", h_st_rep), Paragraph("ORE S.", h_st_rep), Paragraph("PREV.", h_st_rep), Paragraph("EFF.", h_st_rep), Paragraph("GIORNI", h_st_rep), Paragraph("ORE TOT.", h_st_rep)]
    data_pdf = [headers_pdf]
    for op, (ore_g, da_f) in DB_OPERATORI.items():
        reg = t_c[op]
        stringa_g = ", ".join(g_i[op]) if g_i[op] else "-"
        if reg > 0:
            op_p = f"{op.split(' ')[0]}{op.split(' ')[1]}" if " " in op else op
            data_pdf.append([Paragraph(op_p, ParagraphStyle('L', fontName='Helvetica', fontSize=9, alignment=0)), Paragraph(str(ore_g), c_st_rep), Paragraph(str(da_f), c_st_rep), Paragraph(str(reg), c_st_rep), Paragraph(stringa_g, c_st_rep), Paragraph(str(reg * ore_g) + " ore", ParagraphStyle('B', fontName='Helvetica-Bold', fontSize=9, alignment=1))])
    t_rep = Table(data_pdf, colWidths=[160, 55, 55, 55, 110, 85])
    t_rep.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1F538D")), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F9F9F9")]), ('BOTTOMPADDING', (0,0), (-1,-1), 6), ('TOPPADDING', (0,0), (-1,-1), 6)]))
    elements_rep.append(t_rep)
    doc_rep.build(elements_rep)
    with open(path_rep, "rb") as file:
        st.download_button(label="📥 Scarica il PDF del Report Ore", data=file, 
                           file_name=f"Report_Ore_{lun_str.replace('/', '_')}.pdf", mime="application/pdf", 
                           use_container_width=True)