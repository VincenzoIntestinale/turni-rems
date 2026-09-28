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
                    if " " in testo_pulito:
                        parti_n = testo_pulito.split(" ", 1)
                        testo_pulito = f"{parti_n[0]}<br/>{parti_n[1]}" if len(parti_n) > 1 else testo_pulito
                    r.append(Paragraph(testo_pulito, c_st_tab))
                data_pdf.append(r)
                r_styles.append(('BACKGROUND', (0, r_idx), (-1, r_idx), bg_c))
                r_idx += 1
                
        w_cols = [110] + [92] * 7
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
                    if g_n_it[idx] not in g_i[op]: 
                        g_i[op].append(g_n_it[idx])
                    
    html_rep = f"<div id='sez_stampa_rep'><h2 style='text-align:center; font-family:Arial; color:#1F538D;'>REPORT - PROGRAMMAZIONE TURNI REMS - SETTIMANA DAL {lun_str} AL {dom_str}</h2>"
    html_rep += "<table style='width:100%; border-collapse:collapse; font-family:Arial;'><tr style='background-color:#1F538D; color:white;'><th style='padding:10px;'>OPERATORE</th><th style='padding:10px;'>ORE S.</th><th style='padding:10px;'>PREV.</th><th style='padding:10px;'>EFF.</th><th style='padding:10px;'>GIORNI IMPIEGATI</th><th style='padding:10px;'>ORE TOTALI</th></tr>"
    for op, (ore_g, da_f) in DB_OPERATORI.items():
        reg = t_c[op]
        sg = ", ".join(g_i[op]) if g_i[op] else "-"
        if reg > 0:
            if " " in op:
                parti_op = op.split(" ", 1)
                op_p = f"{parti_op[0]}<br/>{parti_op[1]}" if len(parti_op) > 1 else op
            else:
                op_p = op
            html_rep += f"<tr style='text-align:center;'><td style='padding:8px; border:1px solid #ccc; text-align:left; font-weight:bold; font-size:12px; color:black;'>{op_p}</td><td style='padding:8px; border:1px solid #ccc; color:black;'>{ore_g}</td><td style='padding:8px; border:1px solid #ccc; color:black;'>{da_f}</td><td style='padding:8px; border:1px solid #ccc; color:black;'>{reg}</td><td style='padding:8px; border:1px solid #ccc; color:black;'>{sg}</td><td style='padding:8px; border:1px solid #ccc; color:#1F538D; font-size:12px;'><b>{reg*ore_g} ore</b></td></tr>"
    html_rep += "</table></div><br/>"
    st.markdown(html_rep, unsafe_allow_html=True)
    
    if st.button("📊 Genera PDF Report Ore", key="gen_pdf_rep_btn", use_container_width=True):
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        
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
                if " " in op:
                    parti_op = op.split(" ", 1)
                    op_p = f"{parti_op[0]}<br/>{parti_op[1]}" if len(parti_op) > 1 else op
                else:
                    op_p = op
                data_pdf.append([
                    Paragraph(op_p, ParagraphStyle('L', fontName='Helvetica', fontSize=9, alignment=0)),
                    Paragraph(str(ore_g), c_st_rep), Paragraph(str(da_f), c_st_rep), Paragraph(str(reg), c_st_rep),
                    Paragraph(stringa_g, c_st_rep), Paragraph(str(reg * ore_g) + " ore", ParagraphStyle('B', fontName='Helvetica-Bold', fontSize=9, alignment=1))
                ])
                
        w_rep = [140, 60, 60, 60, 110, 80]
        t_rep = Table(data_pdf, colWidths=w_rep)
        t_rep.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1F538D")), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F9F9F9")]),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6), ('TOPPADDING', (0,0), (-1,-1), 6)
        ]))
        elements_rep.append(t_rep)
        doc_rep.build(elements_rep)
        with open(path_rep, "rb") as file:
            st.download_button(label="📥 Scarica il PDF del Report Ore", data=file, file_name=f"Report_Ore_{lun_str.replace('/', '_')}.pdf", mime="application/pdf", use_container_width=True)
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
                    if " " in testo_pulito:
                        parti_n = testo_pulito.split(" ", 1)
                        testo_pulito = f"{parti_n[0]}<br/>{parti_n[1]}" if len(parti_n) > 1 else testo_pulito
                    r.append(Paragraph(testo_pulito, c_st_tab))
                data_pdf.append(r)
                r_styles.append(('BACKGROUND', (0, r_idx), (-1, r_idx), bg_c))
                r_idx += 1
                
        w_cols = [110] + [92] * 7
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
                    if g_n_it[idx] not in g_i[op]: 
                        g_i[op].append(g_n_it[idx])
                    
    html_rep = f"<div id='sez_stampa_rep'><h2 style='text-align:center; font-family:Arial; color:#1F538D;'>REPORT - PROGRAMMAZIONE TURNI REMS - SETTIMANA DAL {lun_str} AL {dom_str}</h2>"
    html_rep += "<table style='width:100%; border-collapse:collapse; font-family:Arial;'><tr style='background-color:#1F538D; color:white;'><th style='padding:10px;'>OPERATORE</th><th style='padding:10px;'>ORE S.</th><th style='padding:10px;'>PREV.</th><th style='padding:10px;'>EFF.</th><th style='padding:10px;'>GIORNI IMPIEGATI</th><th style='padding:10px;'>ORE TOTALI</th></tr>"
    for op, (ore_g, da_f) in DB_OPERATORI.items():
        reg = t_c[op]
        sg = ", ".join(g_i[op]) if g_i[op] else "-"
        if reg > 0:
            if " " in op:
                parti_op = op.split(" ", 1)
                op_p = f"{parti_op[0]}<br/>{parti_op[1]}" if len(parti_op) > 1 else op
            else:
                op_p = op
            html_rep += f"<tr style='text-align:center;'><td style='padding:8px; border:1px solid #ccc; text-align:left; font-weight:bold; font-size:12px; color:black;'>{op_p}</td><td style='padding:8px; border:1px solid #ccc; color:black;'>{ore_g}</td><td style='padding:8px; border:1px solid #ccc; color:black;'>{da_f}</td><td style='padding:8px; border:1px solid #ccc; color:black;'>{reg}</td><td style='padding:8px; border:1px solid #ccc; color:black;'>{sg}</td><td style='padding:8px; border:1px solid #ccc; color:#1F538D; font-size:12px;'><b>{reg*ore_g} ore</b></td></tr>"
    html_rep += "</table></div><br/>"
    st.markdown(html_rep, unsafe_allow_html=True)
    
    if st.button("📊 Genera PDF Report Ore", key="gen_pdf_rep_btn", use_container_width=True):
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        
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
                if " " in op:
                    parti_op = op.split(" ", 1)
                    op_p = f"{parti_op[0]}<br/>{parti_op[1]}" if len(parti_op) > 1 else op
                else:
                    op_p = op
                data_pdf.append([
                    Paragraph(op_p, ParagraphStyle('L', fontName='Helvetica', fontSize=9, alignment=0)),
                    Paragraph(str(ore_g), c_st_rep), Paragraph(str(da_f), c_st_rep), Paragraph(str(reg), c_st_rep),
                    Paragraph(stringa_g, c_st_rep), Paragraph(str(reg * ore_g) + " ore", ParagraphStyle('B', fontName='Helvetica-Bold', fontSize=9, alignment=1))
                ])
                
        w_rep = [140, 60, 60, 60, 110, 80]
        t_rep = Table(data_pdf, colWidths=w_rep)
        t_rep.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1F538D")), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F9F9F9")]),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6), ('TOPPADDING', (0,0), (-1,-1), 6)
        ]))
        elements_rep.append(t_rep)
        doc_rep.build(elements_rep)
        with open(path_rep, "rb") as file:
            st.download_button(label="📥 Scarica il PDF del Report Ore", data=file, file_name=f"Report_Ore_{lun_str.replace('/', '_')}.pdf", mime="application/pdf", use_container_width=True)
