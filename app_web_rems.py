import os
import json
import base64
import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

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
FILE_DATI = "archivio_turni_rems_cloud.json"

TOKEN_GITHUB = st.secrets.get("chiave_github", "").strip()
REPO_GITHUB = "vincenzointestinale/turni-rems"

if "data_ancora" not in st.session_state:
    oggi = datetime.now()
    st.session_state.data_ancora = oggi - timedelta(days=oggi.weekday())

col_prev, col_testo, col_next = st.columns(3)

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

def carica_turni_settimana():
    if not TOKEN_GITHUB:
        if os.path.exists(FILE_DATI):
            try:
                with open(FILE_DATI, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception: pass
        return {}
        url = "https://" + "://github.com" + f"{REPO_GITHUB}/contents/{FILE_DATI}"
    headers = {"Authorization": f"token {TOKEN_GITHUB}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            content = res.json()
            return json.loads(base64.b64decode(content["content"]).decode("utf-8"))
    except Exception: pass
    return {}

archivio_globale = carica_turni_settimana()
lista_ops = ["- Vuoto -"] + list(DB_OPERATORI.keys())
g_nomi = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]

st.markdown("<br/>", unsafe_allow_html=True)

def invia_archivio_github(nuovo_db):
    if not TOKEN_GITHUB:
        try:
            with open(FILE_DATI, "w", encoding="utf-8") as f:
                json.dump(nuovo_db, f, ensure_ascii=False, indent=4)
        except Exception: pass
        return
        url = "https://" + "://github.com" + f"{REPO_GITHUB}/contents/{FILE_DATI}"
    headers = {"Authorization": f"token {TOKEN_GITHUB}"}
    sha = None
    try:
        res_get = requests.get(url, headers=headers)
        if res_get.status_code == 200:
            sha = res_get.json().get("sha")
        
        payload = {
            "message": "Aggiornamento automatico turni REMS",
            "content": base64.b64encode(json.dumps(nuovo_db, ensure_ascii=False, indent=4).encode("utf-8")).decode("utf-8")
        }
        if sha:
            payload["sha"] = sha
        requests.put(url, headers=headers, json=payload)
    except Exception: pass

def salva_turno_callback(ch_w, dt_g, fas, sl):
    scelta = st.session_state[ch_w]
    tag_f = "mattino" if "09:00" in fas else "pomeriggio"
    chiave_unica = f"{dt_g}_{tag_f}_{sl}"
    db = carica_turni_settimana()
    if scelta != "- Vuoto -":
        db[chiave_unica] = scelta
    else:
        if chiave_unica in db: del db[chiave_unica]
    invia_archivio_github(db)

dati_turni = {dt.strftime("%Y-%m-%d"): {f: ["- Vuoto -"] * MAX_SLOTS for f in FASCE} for dt in date_sett}
for k, operatore_nome in archivio_globale.items():
    for dt in date_sett:
        k_g = dt.strftime("%Y-%m-%d")
        if k.startswith(k_g):
            f_orario = "09:00 - 14:00" if "mattino" in k else "15:00 - 20:00"
            try:
                s_idx = int(k.split("_")[-1])
                if s_idx < MAX_SLOTS:
                    dati_turni[k_g][f_orario][s_idx] = operatore_nome
            except Exception: pass

colonne_giorni = st.columns(7)
for idx, dt in enumerate(date_sett):
    k_g = dt.strftime("%Y-%m-%d")
    with colonne_giorni[idx]:
        st.markdown(f"<div style='text-align:center; background-color:#1F538D; padding:8px; border-radius:6px; color:white; font-family:Arial; font-size:13px; font-weight:bold;'>{g_nomi[idx]}<br/>{dt.strftime('%d/%m')}</div>", unsafe_allow_html=True)
        for fas in FASCE:
            bg_c = "#FFF1E0" if "09:00" in fas else "#F3E5F5"
            st.markdown(f"<div style='background-color:{bg_c}; padding:4px; margin-top:8px; border-radius:4px; text-align:center; font-size:11px; font-weight:bold; color:#333; font-family:Arial;'>🕒 {fas}</div>", unsafe_allow_html=True)
            for s in range(MAX_SLOTS):
                tag_f = "mattino" if "09:00" in fas else "pomeriggio"
                valore_attuale = dati_turni[k_g][fas][s]
                def_idx = lista_ops.index(valore_attuale) if valore_attuale in lista_ops else 0
                ch_widget = f"w_sel_{k_g}_{tag_f}_{s}"
                st.selectbox(
                    label=ch_widget, options=lista_ops, index=def_idx, key=ch_widget,
                    label_visibility="collapsed", on_change=salva_turno_callback, args=(ch_widget, k_g, fas, s)
                )
st.markdown("<br/><hr/>", unsafe_allow_html=True)
st.subheader("🖨️ Centro Stampa Documenti")
tab1, tab2 = st.tabs(["👁️ Visualizza Tabellone Settimanale", "📊 Visualizza Report Ore"])

with tab1:
    html_tab = f"<div id='sez_stampa_tab'><h2 style='text-align:center; font-family:Arial; color:#1F538D;'>PROGRAMMAZIONE TURNI REMS - SETTIMANA DAL {lun_str} AL {dom_str}</h2>"
    html_tab += "<table style='width:100%; border-collapse:collapse; font-family:Arial; border:1px solid #1F538D;'><thead><tr style='background-color:#1F538D; color:white;'><th style='padding:8px; border:1px solid #1F538D; width:12%;'>Fascia Oraria</th>"
    for i, d in enumerate(date_sett):
        html_tab += f"<th style='padding:8px; border:1px solid #1F538D; width:12.5%;'>{g_nomi[i]}<br/>{d.strftime('%d/%m')}</th>"
    html_tab += "</tr></thead><tbody>"
    for fas in FASCE:
        bg = "#FFF1E0" if "09:00" in fas else "#F3E5F5"
        txt_orario = "MATTINO<br/>dalle ore 09:00<br/>alle ore 14:00" if "09:00" in fas else "POMERIGGIO<br/>dalle ore 15:00<br/>alle ore 20:00"
        for s in range(MAX_SLOTS):
            f_txt = f"<b>{txt_orario}</b>" if s == 2 else ""
            html_tab += f"<tr style='background-color:{bg}; text-align:center;'><td style='padding:6px; border:1px solid #ddd; font-size:11px;'>{f_txt}</td>"
            for dt in date_sett:
                tag_f = "mattino" if "09:00" in fas else "pomeriggio"
                ch_u = f"{dt.strftime('%Y-%m-%d')}_{tag_f}_{s}"
                v = dati_turni[dt.strftime("%Y-%m-%d")][fas][s]
                v_p = f"{v.split(' ', 1)[0]}<br/>{v.split(' ', 1)[1]}" if (" " in v and v != "- Vuoto -" and len(v.split(' ', 1)) > 1) else (v if v != "- Vuoto -" else "")
                html_tab += f"<td style='padding:6px; border:1px solid #ddd; font-size:11px; color:black; font-weight:bold;'>{v_p}</td>"
            html_tab += "</tr>"
    html_tab += "</tbody></table></div><br/>"
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
            testo_orario = "MATTINO<br/>dalle 09:00 alle 14:00" if "09:00" in fas else "POMERIGGIO<br/>dalle 15:00 alle 20:00"
            for s in range(MAX_SLOTS):
                f_txt = testo_orario if s == 2 else ""
                r = [Paragraph(f_txt, ParagraphStyle('F', fontName='Helvetica-Bold', fontSize=7, alignment=1))]
                for dt in date_sett:
                    v = dati_turni[dt.strftime("%Y-%m-%d")][fas][s]
                    testo_pulito = v if v != "- Vuoto -" else ""
                    if " " in testo_pulito and len(testo_pulito.split(" ", 1)) > 1:
                        p_n = testo_pulito.split(" ", 1)
                        testo_pulito = f"{p_n[0]}<br/>{p_n[1]}"
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
                if op in t_c:
                    t_c[op] += 1
                    if g_n_it[idx] not in g_i[op]: g_i[op].append(g_n_it[idx])
                    
    html_rep = f"<div id='sez_stampa_rep'><h2 style='text-align:center; font-family:Arial; color:#1F538D;'>REPORT - TURNI REMS - DAL {lun_str} AL {dom_str}</h2>"
    html_rep += "<table style='width:100%; border-collapse:collapse; font-family:Arial; border:1px solid #ccc;'><tr style='background-color:#1F538D; color:white;'><th style='padding:10px;'>OPERATORE</th><th style='padding:10px;'>ORE S.</th><th style='padding:10px;'>PREV.</th><th style='padding:10px;'>EFF.</th><th style='padding:10px;'>GIORNI IMPIEGATI</th><th style='padding:10px;'>ORE TOTALI</th></tr>"
    for op, (ore_g, da_f) in DB_OPERATORI.items():
        reg = t_c[op]
        sg = ", ".join(g_i[op]) if g_i[op] else "-"
        if reg > 0:
            op_p = f"{op.split(' ', 1)[0]}<br/>{op.split(' ', 1)[1]}" if (" " in op and len(op.split(' ', 1)) > 1) else op
            html_rep += f"<tr style='text-align:center;'><td style='padding:8px; border:1px solid #ccc; text-align:left; font-weight:bold; font-size:12px; color:black;'>{op_p}</td><td style='padding:8px; border:1px solid #ccc;'>{ore_g}</td><td style='padding:8px; border:1px solid #ccc;'>{da_f}</td><td style='padding:8px; border:1px solid #ccc;'>{reg}</td><td style='padding:8px; border:1px solid #ccc;'>{sg}</td><td style='padding:8px; border:1px solid #ccc; color:#1F538D;'><b>{reg*ore_g} ore</b></td></tr>"
    html_rep += "</table></div><br/>"
    st.markdown(html_rep, unsafe_allow_html=True)
    
    if st.button("📊 Genera PDF Report Ore", key="gen_pdf_rep_btn", use_container_width=True):
        path_rep = "Report_Ore_REMS.pdf"
        doc_rep = SimpleDocTemplate(path_rep, pagesize=letter, leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
        elements_rep = list()
        styles_rep = getSampleStyleSheet()
        t_st_rep = ParagraphStyle('T', fontName='Helvetica-Bold', fontSize=11, alignment=1, spaceAfter=20)
        c_st_rep = ParagraphStyle('C', fontName='Helvetica', fontSize=9, alignment=1)
        h_st_rep = ParagraphStyle('H', fontName='Helvetica-Bold', fontSize=10, alignment=1, textColor=colors.white)
        
        elements_rep.append(Paragraph(f"REPORT - PROGRAMMAZIONE TURNI REMS - DAL {lun_str} AL {dom_str}", t_st_rep))
        headers_pdf = [Paragraph("OPERATORE", h_st_rep), Paragraph("ORE S.", h_st_rep), Paragraph("PREV.", h_st_rep), Paragraph("EFF.", h_st_rep), Paragraph("GIORNI IMPIEGATI", h_st_rep), Paragraph("ORE TOT.", h_st_rep)]
        data_pdf = [headers_pdf]
        
        for op, (ore_g, da_f) in DB_OPERATORI.items():
            reg = t_c[op]
            stringa_g = ", ".join(g_i[op]) if g_i[op] else "-"
            if reg > 0:
                op_p = f"{op.split(' ', 1)[0]} {op.split(' ', 1)[1]}" if (" " in op and len(op.split(' ', 1)) > 1) else op
                data_pdf.append([
                    Paragraph(op_p, ParagraphStyle('L', fontName='Helvetica', fontSize=9, alignment=0)),
                    Paragraph(str(ore_g), c_st_rep), Paragraph(str(da_f), c_st_rep), Paragraph(str(reg), c_st_rep),
                    Paragraph(stringa_g, c_st_rep), Paragraph(str(reg * ore_g) + " ore", ParagraphStyle('B', fontName='Helvetica-Bold', fontSize=9, alignment=1))
                ])
                
        w_rep = [140, 50, 50, 50, 150, 60]
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
        with open(path_rep, "rb") as file:
            st.download_button(label="📥 Scarica il PDF del Report Ore", data=file, file_name=f"Report_Ore_{lun_str.replace('/', '_')}.pdf", mime="application/pdf", use_container_width=True)
