# Auto-Backups

## Ziel
Automatische, rotierende Backups von `app/data/pm.json` zusaetzlich zum
manuellen Export in den Einstellungen.

## Ansatz
- `store.save()` um optionales Snapshotting erweitern (z. B. bei der ersten
  Aenderung eines Tages `data/backups/pm-YYYY-MM-DD.json` schreiben, aeltere
  Snapshots nach N Tagen aufraeumen).
- Ein-/Ausschalter + Aufbewahrungsdauer in `app/views/settings.py`.
- Hinweis in `DEPLOY.md`, dass `data/backups/` mit ins Volume/Backup-Konzept
  gehoert.

## Betroffene Dateien
`app/store.py`, `app/views/settings.py`, `DEPLOY.md`.
