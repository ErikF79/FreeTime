# FreeTime

Piattaforma multi-gioco per attivita ricreative, sfide e team building (Flask + PWA).

## Avvio locale

```bat
cd /d C:\percorso\FreeTime
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Apri http://127.0.0.1:5000/

## Test

```bat
python test_rulesets.py
python test_tictactoe.py
python test_connect4.py
```

## PWA

L'app e installabile dal browser (Chrome/Edge) come PWA grazie a manifest e service worker.

## Deploy

Backend Flask: Render/Railway/altro. Frontend statico e PWA metadata inclusi.
