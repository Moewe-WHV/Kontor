# iCal-Sync

## Ziel
Meilensteine/Sprints/Releases als iCal-Feed abonnierbar machen
(Kalender-Apps wie Google/Outlook/Apple Kalender).

## Ansatz
- Neuer FastAPI-Endpoint `/calendar/<project_id>.ics`, der
  `store.p_milestones`/`p_sprints`/`p_releases` in eine `.ics`-Datei
  rendert (fuer einfache `VEVENT`-Eintraege reicht stdlib
  `email`/manuelles Formatieren, sonst kleine Dependency wie `ics`).
- Link/Kopier-Knopf in `app/views/calendar.py` oder `app/views/settings.py`.

## Betroffene Dateien
`app/main.py` (Route), `app/store.py`, `app/views/calendar.py`.
