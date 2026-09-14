# Auto-Release-Notes

## Ziel
Release Notes automatisch aus erledigten Tasks/PRs seit dem letzten
Release als Textvorschlag generieren (`store.Release.notes`).

## Ansatz
- `store.py`: Helfer, der Tasks mit `done_at` zwischen zwei Releases
  sammelt und nach Label/Epic gruppiert.
- `app/views/releases.py`: Button "Notizen vorschlagen" befuellt das
  `notes`-Feld (vor dem Speichern editierbar).
- Optional: PRs/Commits seit dem letzten Tag ueber `github_client.py`
  einbeziehen.

## Betroffene Dateien
`app/store.py`, `app/views/releases.py`, `app/github_client.py`.
