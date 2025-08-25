# PV-Übergabe & Komponentenregister – Vor-Ort-App

**Hinweis zu Streamlit Cloud/Python-Version**  
Wenn dein Deployment-Log Python **3.13** zeigt, pinne die Runtime auf **3.12**, da einige Wheels (z. B. pandas) auf 3.13 Probleme machen können.

## Quickstart
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Deployment (Streamlit Cloud)
Lege **eine** der folgenden Dateien ins Repo:
- `runtime.txt` mit Inhalt: `3.12`
- **oder** `.python-version` mit Inhalt: `3.12.0`
