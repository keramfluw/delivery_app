import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import mm

st.set_page_config(page_title='PV-Übergabe & Komponentenregister', layout='wide')

def compute_garantieende(row):
    try:
        gb = pd.to_datetime(row.get('Garantiebeginn'))
        jahre = float(row.get('Garantiedauer (Jahre)', 0) or 0)
        if pd.isna(gb):
            return ''
        return (gb + pd.to_timedelta(int(jahre * 365.25), unit='D')).date().isoformat()
    except Exception:
        return ''

def df_default():
    return pd.DataFrame([{
        'Komponente': '', 'Hersteller': '', 'Modell': '', 'Seriennummer': '',
        'Herstellungsdatum': '', 'Lieferdatum': '', 'Rechnungsdatum': '',
        'Inbetriebnahmedatum': '', 'Garantiebeginn': '', 'Garantiedauer (Jahre)': 0,
        'Firmware/Softwarestand': '', 'Ablageort Garantieunterlagen': '', 'Bemerkungen': ''
    }])

def make_pdf(project, docs, df_components, rechtsgrundlagen):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=18*mm, bottomMargin=18*mm)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph(f'Übergabedokumentation & Komponentenregister – Projekt {project.get("projekt_nr","")}', styles['Title']))
    story.append(Spacer(1, 6))
    lines = [
        f"<b>Projekt-Nr.:</b> {project.get('projekt_nr','')}",
        f"<b>Kunde:</b> {project.get('kunde_name','')}",
        f"<b>Objektadresse:</b> {project.get('objekt_strasse','')} {project.get('objekt_hausnr','')}, {project.get('objekt_plz','')} {project.get('objekt_ort','')}",
        f"<b>Inbetriebnahme:</b> {project.get('inbetriebnahme','')}",
        f"<b>Abnahme:</b> {project.get('abnahme','')}",
        f"<b>Techniker:</b> {project.get('techniker','')} ({project.get('techniker_kontakt','')})"
    ]
    story.append(Paragraph('<br/>'.join(lines), styles['Normal']))
    story.append(Spacer(1, 12))
    story.append(Paragraph('1. Dokumentationspflicht bei Übergabe', styles['Heading2']))
    bullets = []
    for k, v in docs.items():
        if isinstance(v, dict):
            for sk, sv in v.items():
                mark = '✔︎' if sv else '—'
                bullets.append(f'{mark} {k}: {sk}')
        else:
            mark = '✔︎' if v else '—'
            bullets.append(f'{mark} {k}')
    for b in bullets:
        story.append(Paragraph(f'• {b}', styles['Normal']))
    story.append(Spacer(1, 12))
    story.append(Paragraph('2. Komponentenregister (Garantie & Gewährleistung)', styles['Heading2']))
    df = df_components.copy()
    if 'Garantiebeginn' in df.columns and 'Garantiedauer (Jahre)' in df.columns:
        df['Garantieende'] = df.apply(compute_garantieende, axis=1)
    cols = ['Komponente','Hersteller','Modell','Seriennummer','Herstellungsdatum','Lieferdatum','Rechnungsdatum','Inbetriebnahmedatum','Garantiebeginn','Garantiedauer (Jahre)','Garantieende','Firmware/Softwarestand','Ablageort Garantieunterlagen','Bemerkungen']
    df = df[cols]
    table_data = [cols] + df.fillna('').astype(str).values.tolist()
    tbl = Table(table_data, repeatRows=1)
    tbl.setStyle(TableStyle([('FONT',(0,0),(-1,0),'Helvetica-Bold',9),('FONT',(0,1),(-1,-1),'Helvetica',8),('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('GRID',(0,0),(-1,-1),0.25,colors.grey),('VALIGN',(0,0),(-1,-1),'TOP')]))
    story.append(tbl)
    story.append(Spacer(1, 12))
    story.append(Paragraph('4. Rechtliche / normative Bezugspunkte', styles['Heading2']))
    for rg in rechtsgrundlagen:
        story.append(Paragraph(f'• {rg}', styles['Normal']))
    story.append(Spacer(1, 18))
    story.append(Paragraph(f'Erstellt am {date.today().isoformat()} über die Vor-Ort-App.', styles['Italic']))
    doc.build(story)
    buffer.seek(0)
    return buffer

def make_excel(project, df_components):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        info = pd.DataFrame({
            'Feld': ['Projekt-Nr.','Kunde','Objektadresse','Inbetriebnahme','Abnahme','Techniker'],
            'Wert': [
                project.get('projekt_nr',''),
                project.get('kunde_name',''),
                f"{project.get('objekt_strasse','')} {project.get('objekt_hausnr','')}, {project.get('objekt_plz','')} {project.get('objekt_ort','')}",
                project.get('inbetriebnahme',''),
                project.get('abnahme',''),
                f"{project.get('techniker','')} ({project.get('techniker_kontakt','')})"
            ]
        })
        info.to_excel(writer, sheet_name='Projekt', index=False)
        df = df_components.copy()
        if 'Garantiebeginn' in df.columns and 'Garantiedauer (Jahre)' in df.columns:
            df['Garantieende'] = df.apply(compute_garantieende, axis=1)
        df.to_excel(writer, sheet_name='Komponentenregister', index=False)
    output.seek(0)
    return output

st.title('PV-Übergabe & Komponentenregister – Qrauts AG')

with st.sidebar:
    st.header('Projekt-Metadaten')
    projekt_nr = st.text_input('Projekt-Nr.', placeholder='z.B. 2025-08-25-001')
    kunde_name = st.text_input('Kunde / Auftraggeber')
    objekt_strasse = st.text_input('Objekt – Straße')
    objekt_hausnr = st.text_input('Hausnummer')
    objekt_plz = st.text_input('PLZ')
    objekt_ort = st.text_input('Ort')
    inbetriebnahme = st.date_input('Datum Inbetriebnahme', value=date.today())
    abnahme = st.date_input('Datum Abnahme', value=date.today())
    techniker = st.text_input('Techniker (Name)')
    techniker_kontakt = st.text_input('Techniker Kontakt (Tel./E-Mail)')

st.subheader('1) Dokumentationspflicht bei Übergabe')
col1, col2, col3 = st.columns(3)
with col1:
    ibp_ok = st.checkbox('Inbetriebnahmeprotokoll (VDE-AR-N 4105) vorhanden?')
with col2:
    pruef_ok = st.checkbox('Prüfprotokolle (VDE 0100-600 / 0126-23) vorhanden?')
with col3:
    uebergabe_ok = st.checkbox('Übergabeprotokoll mit Einweisung vorhanden?')

st.markdown('---')
st.subheader('2) Komponentenregister – Pflichtangaben & sinnvolle Ergänzungen')

if 'df_components' not in st.session_state:
    st.session_state.df_components = df_default()

date_columns = [
    'Herstellungsdatum',
    'Lieferdatum',
    'Rechnungsdatum',
    'Inbetriebnahmedatum',
    'Garantiebeginn'
]

for col in date_columns:
    if col in st.session_state.df_components.columns:
        st.session_state.df_components[col] = pd.to_datetime(
            st.session_state.df_components[col], errors='coerce'
        )
edited_df = st.data_editor(
    st.session_state.df_components,
    num_rows='dynamic',
    use_container_width=True,
    column_config={
        'Herstellungsdatum': st.column_config.DateColumn('Herstellungsdatum', format='YYYY-MM-DD'),
        'Lieferdatum': st.column_config.DateColumn('Lieferdatum', format='YYYY-MM-DD'),
        'Rechnungsdatum': st.column_config.DateColumn('Rechnungsdatum', format='YYYY-MM-DD'),
        'Inbetriebnahmedatum': st.column_config.DateColumn('Inbetriebnahmedatum', format='YYYY-MM-DD'),
        'Garantiebeginn': st.column_config.DateColumn('Garantiebeginn', format='YYYY-MM-DD'),
        'Garantiedauer (Jahre)': st.column_config.NumberColumn('Garantiedauer (Jahre)', min_value=0, step=1)
    },
    hide_index=True
)
st.session_state.df_components = edited_df

st.markdown('---')
st.subheader('4) Rechtliche / normative Bezugspunkte (Auszug)')
rechtsgrundlagen = [
    'BGB §§ 434 ff. – Sachmangel/Gewährleistung',
    'VOB/B § 13 – Mängelansprüche (falls vereinbart)',
    'Produkthaftungsgesetz (ProdHaftG)',
    'DIN VDE 0100, 0126, 4105 – Inbetriebnahme-/Prüfpflichten',
    'Herstellerbedingungen – Seriennummern/Registrierungen (z. B. SMA, BYD)'
]
st.write('\n'.join([f'- {r}' for r in rechtsgrundlagen]))

st.markdown('---')
colA, colB = st.columns(2)
with colA:
    if st.button('📄 PDF generieren'):
        project = {
            'projekt_nr': projekt_nr, 'kunde_name': kunde_name,
            'objekt_strasse': objekt_strasse, 'objekt_hausnr': objekt_hausnr,
            'objekt_plz': objekt_plz, 'objekt_ort': objekt_ort,
            'inbetriebnahme': inbetriebnahme.isoformat(),
            'abnahme': abnahme.isoformat(),
            'techniker': techniker, 'techniker_kontakt': techniker_kontakt
        }
        docs = {'Inbetriebnahmeprotokoll': {'vorhanden': ibp_ok}, 'Prüfprotokolle': {'vorhanden': pruef_ok}, 'Übergabeprotokoll': {'vorhanden': uebergabe_ok}}
        pdf = make_pdf(project, docs, st.session_state.df_components, rechtsgrundlagen)
        st.download_button('PDF herunterladen', data=pdf.getvalue(), file_name=f"{projekt_nr or 'projekt'}_Uebergabe-Komponentenregister.pdf", mime='application/pdf')
with colB:
    if st.button('📊 Excel generieren'):
        project = {
            'projekt_nr': projekt_nr, 'kunde_name': kunde_name,
            'objekt_strasse': objekt_strasse, 'objekt_hausnr': objekt_hausnr,
            'objekt_plz': objekt_plz, 'objekt_ort': objekt_ort,
            'inbetriebnahme': inbetriebnahme.isoformat(),
            'abnahme': abnahme.isoformat(),
            'techniker': techniker, 'techniker_kontakt': techniker_kontakt
        }
        excel = make_excel(project, st.session_state.df_components)
        st.download_button('Excel herunterladen', data=excel.getvalue(), file_name=f"{projekt_nr or 'projekt'}_Komponentenregister.xlsx", mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

st.caption('© 2025 – Vor-Ort-App für PV-Übergabe & Komponentenregister')
