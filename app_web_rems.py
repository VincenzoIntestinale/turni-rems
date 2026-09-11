# INCOLLA QUESTO BLOCCO NUOVO AL SUO POSTO:
import os
import sqlite3
import streamlit as st
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

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

def init_db():
    conn = sqlite3.connect("database_turni_rems.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS turni (
            data_giorno TEXT, fascia TEXT, slot_index INTEGER, operatore TEXT,
            PRIMARY KEY (data_giorno, fascia, slot_index)
        )
    """)
    conn.commit()
    conn.close()

init_db()

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

date_sett = []
for i in range(7):
    date_sett.append(st.session_state.data_ancora + timedelta(days=i))

lun_str = date_sett[0].strftime('%d/%m/%Y')
dom_str = date_sett[-1].strftime('%d/%m/%Y')

with col_testo:
    st.markdown(f"<h3 style='text-align:center; font-family:Arial;'>📅 SETTIMANA DAL {lun_str} AL {dom_str}</h3>", unsafe_allow_html=True)

def carica_turni_settimana(date_list):
    conn = sqlite3.connect("database_turni_rems.db")
    c = conn.cursor()
    dati = {}
    for dt in date_list:
        k_g = dt.strftime("%Y-%m-%d")
        dati[k_g] = {f: ["- Vuoto -"] * MAX_SLOTS for f in FASCE}
        for fas in FASCE:
            c.execute("SELECT slot_index, operatore FROM turni WHERE data_giorno=? AND fascia=?", (k_g, fas))
            for s_idx, op in c.fetchall():
                if s_idx < MAX_SLOTS:
                    dati[k_g][fas][s_idx] = op
    conn.close()
    return dati

def salva_turno_db(data_g, fascia, slot, operatore):
    conn = sqlite3.connect("database_turni_rems.db")
    c = conn.cursor()
    if operatore != "- Vuoto -":
        c.execute("""
            INSERT INTO turni (data_giorno, fascia, slot_index, operatore) VALUES (?, ?, ?, ?)
            ON CONFLICT(data_giorno, fascia, slot_index) DO UPDATE SET operatore=excluded.operatore
        """, (data_g, fascia, slot, operatore))
    else:
        c.execute("DELETE FROM turni WHERE data_giorno=? AND fascia=? AND slot_index=?", (data_g, fascia, slot))
    conn.commit()
    conn.close()

dati_turni = carica_turni_settimana(date_sett)
lista_ops = ["- Vuoto -"] + list(DB_OPERATORI.keys())
g_nomi = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]

st.markdown("<br/>", unsafe_allow_html=True)

colonne_giorni = st.columns(7)
for idx, dt in enumerate(date_sett):
    k_g = dt.strftime("%Y-%m-%d")
    with colonne_giorni[idx]:
        st.markdown(f"""
            <div style='text-align:center; width:100%; margin-bottom:5px;'>
                <div style='background-color:#1F538D; padding:8px; border-radius:6px; color:white; font-family:Arial; font-size:13px; font-weight:bold;'>
                    {g_nomi[idx]}<br/>{dt.strftime('%d/%m')}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        for fas in FASCE:
            colore_bg = "#FFF1E0" if "09:00" in fas else "#F3E5F5"
            st.markdown(f"""
                <div style='background-color:{colore_bg}; padding:4px; margin-top:8px; border-radius:4px; text-align:center; font-size:11px; font-weight:bold; color:#333; font-family:Arial;'>
                    🕒 {fas}
                </div>
            """, unsafe_allow_html=True)
            
            for s in range(MAX_SLOTS):
                valore_salvato = dati_turni[k_g][fas][s]
                try:
                    def_idx = lista_ops.index(valore_salvato)
                except ValueError:
                    def_idx = 0
                
                scelta = st.selectbox(
                    label=f"hidden_{k_g}_{fas}_{s}",
                    options=lista_ops,
                    index=def_idx,
                    key=f"w_sel_{k_g}_{fas}_{s}",
                    label_visibility="collapsed"
                )
                if scelta != valore_salvato:
                    salva_turno_db(k_g, fas, s, scelta)
                    st.rerun()

st.markdown("<br/><hr/>", unsafe_allow_html=True)
st.subheader("🖨️ Centro Stampa Documenti")

tab1, tab2 = st.tabs(["👁️ Visualizza Tabellone Settimanale", "📊 Visualizza Report Ore"])

with tab1:
    st.markdown("""
        <div style='text-align:center; font-family:Arial; margin-bottom:15px;'>
            <h2 style='color:#1F538D; margin:0; font-weight:bold;'>REMS CALVI RISORTA</h2>
            <h4 style='margin:5px 0; color:#555; font-weight:normal;'>Programmazione Turni Operatori della REMS</h4>
        </div>
    """, unsafe_allow_html=True)
    
    html_tab = "<table style='width:100%; border-collapse:collapse; font-family:Arial;'><tr><th style='background-color:#1F538D; color:white; padding:8px; border:1px solid #1F538D;'>Fascia Oraria</th>"
    for i, d in enumerate(date_sett):
        html_tab += f"<th style='background-color:#1F538D; color:white; padding:8px; border:1px solid #1F538D;'>{g_nomi[i]}<br/>{d.strftime('%d/%m')}</th>"
    html_tab += "</tr>"
    
    for fas in FASCE:
        bg = "#FFF1E0" if "09:00" in fas else "#F3E5F5"
        for s in range(MAX_SLOTS):
            fascia_testo = f"<b>{fas}</b>" if s == 2 else ""
            html_tab += f"<tr style='background-color:{bg}; text-align:center;'><td style='padding:6px; border:1px solid #ddd;'>{fascia_testo}</td>"
            for dt in date_sett:
                v = dati_turni[dt.strftime("%Y-%m-%d")][fas][s]
                html_tab += f"<td style='padding:6px; border:1px solid #ddd;'>{v if v != '- Vuoto -' else ''}</td>"
            html_tab += "</tr>"
    html_tab += "</table><br/>"
    st.markdown(html_tab, unsafe_allow_html=True)
    
    if st.button("🖨️ Apri e Stampa PDF Tabellone", key="univoco_key_pdf_tab", use_container_width=True):
                # Salviamo il file in una cartella temporanea del server web
        path_tab = "Tabellone_Turni_REMS.pdf"
        doc_tab = SimpleDocTemplate(path_tab, pagesize=landscape(letter), leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
        elements_tab = list()
        styles_tab = getSampleStyleSheet()
        t_st_tab = ParagraphStyle('T_Tab', fontName='Helvetica-Bold', fontSize=11, alignment=1, spaceAfter=15)
        c_st_tab = ParagraphStyle('C_Tab', fontName='Helvetica', fontSize=8, alignment=1)
        h_st_tab = ParagraphStyle('H_Tab', fontName='Helvetica-Bold', fontSize=9, alignment=1, textColor=colors.white)
        
        d_inizio = date_sett.strftime('%d/%m/%Y')
        d_fine = date_sett[-1].strftime('%d/%m/%Y')
        elements_tab.append(Paragraph(f"PROGRAMMAZIONE TURNI REMS - SETTIMANA DAL {d_inizio} AL {d_fine}", t_st_tab))
        
        giorni_lista_local = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        headers_pdf = [Paragraph("Fascia Oraria", h_st_tab)]
        for i, d in enumerate(date_sett):
            giorno_testo_col = giorni_lista_local[i]
            headers_pdf.append(Paragraph(f"{giorno_testo_col} {d.strftime('%d/%m')}", h_st_tab))
            
        data_pdf = list()
        data_pdf.append(headers_pdf)
        r_styles = [('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1F538D")), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#DDDDDD"))]
        
        r_idx = 1
        for fas in FASCE:
            bg_c = colors.HexColor("#FFF1E0") if "09:00" in fas else colors.HexColor("#F3E5F5")
            if "09:00" in fas:
                testo_orario = "dalle ore 09:00<br/>alle ore 14:00"
            else:
                testo_orario = "dalle ore 15:00<br/>alle ore 20:00"
                
            for s in range(MAX_SLOTS):
                f_txt = testo_orario if s == 2 else ""
                r = [Paragraph(f_txt, ParagraphStyle('F_Tab', fontName='Helvetica-Bold', fontSize=8, alignment=1))]
                
                for dt in date_sett:
                    v = dati_turni[dt.strftime("%Y-%m-%d")][fas][s]
                    testo_pulito = v if v != "- Vuoto -" else ""
                    if " " in testo_pulito:
                        parti_nome = testo_pulito.split(" ", 1)
                        testo_pulito = f"{parti_nome[0]}<br/>{parti_nome[1]}"
                    r.append(Paragraph(testo_pulito, c_st_tab))
                data_pdf.append(r)
                r_styles.append(('BACKGROUND', (0, r_idx), (-1, r_idx), bg_c))
                r_idx += 1
                
        w_cols = [100, 95, 95, 95, 95, 95, 95, 95]
        t_table = Table(data_pdf, colWidths=w_cols)
        t_table.setStyle(TableStyle(r_styles))
        elements_tab.append(t_table)
        doc_tab.build(elements_tab)
        
        # Mette a disposizione il file pronto per scaricarlo o stamparlo dal browser
        with open(path_tab, "rb") as file:
            st.download_button(
                label="📥 Scarica / Stampa il PDF del Tabellone",
                data=file,
                file_name="Tabellone_Turni_REMS.pdf",
                mime="application/pdf",
                use_container_width=True
            )

with tab2:
    st.markdown("<h3 style='text-align:center;'>REPORT CONTEGGI ORE</h3>", unsafe_allow_html=True)
    
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
                    if g_n_it[idx] not in g_i[op]:
                        g_i[op].append(g_n_it[idx])
                        
    # Creazione tabella Web semplificata a righe corte
    html_rep = "<table style='width:100%; border-collapse:collapse; font-family:Arial;'><tr>"
    html_rep += "<th>OPERATORE</th><th>ORE S.</th><th>PREV.</th><th>EFF.</th><th>GIORNI</th><th>TOT.</th></tr>"
    
    for op, (ore_g, da_f) in DB_OPERATORI.items():
        reg = t_c[op]
        sg = ", ".join(g_i[op]) if g_i[op] else "-"
        if reg > 0:
            html_rep += f"<tr style='text-align:center;'><td><b>{op}</b></td><td>{ore_g}</td><td>{da_f}</td><td>{reg}</td><td>{sg}</td><td><b>{reg*ore_g} ore</b></td></tr>"
    html_rep += "</table><br/>"
    st.markdown(html_rep, unsafe_allow_html=True)
    
    if st.button("📊 Apri e Stampa PDF Report Ore", key="univoco_key_pdf_rep", use_container_width=True):
                path_rep = "Report_Ore_REMS.pdf"
    doc_rep = SimpleDocTemplate(path_rep, pagesize=letter, leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
    elements_rep = list()
    styles_rep = getSampleStyleSheet()
    t_st_rep = ParagraphStyle('T_Rep', fontName='Helvetica-Bold', fontSize=11, alignment=1, spaceAfter=20)
    c_st_rep = ParagraphStyle('C_Rep', fontName='Helvetica', fontSize=9, alignment=1)
    h_st_rep = ParagraphStyle('H_Rep', fontName='Helvetica-Bold', fontSize=10, alignment=1, textColor=colors.white)
        
    data_inizio = date_sett.strftime('%d/%m/%Y')
    data_fine = date_sett[-1].strftime('%d/%m/%Y')
    elements_rep.append(Paragraph(f"REPORT - PROGRAMMAZIONE TURNI REMS - SETTIMANA DAL {data_inizio} AL {data_fine}", t_st_rep))
        
    headers_pdf = [Paragraph("OPERATORE", h_st_rep), Paragraph("ORE S.", h_st_rep), Paragraph("PREV.", h_st_rep), Paragraph("EFF.", h_st_rep), Paragraph("GIORNI", h_st_rep), Paragraph("ORE TOT.", h_st_rep)]
    data_pdf = list()
    data_pdf.append(headers_pdf)
        
    for op, (ore_g, da_f) in DB_OPERATORI.items():
            reg = t_c[op]
            stringa_g = ", ".join(g_i[op]) if g_i[op] else "-"
            op_impaginato = op
            if " " in op_impaginato:
                parti_op = op_impaginato.split(" ", 1)
                op_impaginato = f"{parti_op[0]}<br/>{parti_op[1]}"
                
            if reg > 0:
                data_pdf.append([
                    Paragraph(op_impaginato, ParagraphStyle('L_Rep', fontName='Helvetica', fontSize=9, alignment=0)),
                    Paragraph(str(ore_g), c_st_rep), Paragraph(str(da_f), c_st_rep), Paragraph(str(reg), c_st_rep),
                    Paragraph(stringa_g, c_st_rep), Paragraph(str(reg * ore_g) + " ore", ParagraphStyle('B_Rep', fontName='Helvetica-Bold', fontSize=9, alignment=1))
                ])
                
    w_rep = [140, 55, 55, 55, 120, 75]
    t_rep = Table(data_pdf, colWidths=w_rep)
    t_rep.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1F538D")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F9F9F9")]),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6)
        ]))
    elements_rep.append(t_rep)
    doc_rep.build(elements_rep)
        
        # Mette a disposizione il file pronto per scaricarlo o stamparlo dal browser
    with open(path_rep, "rb") as file:
            st.download_button(
                label="📥 Scarica / Stampa il PDF del Report Ore",
                data=file,
                file_name="Report_Ore_REMS.pdf",
                mime="application/pdf",
                use_container_width=True
            )


