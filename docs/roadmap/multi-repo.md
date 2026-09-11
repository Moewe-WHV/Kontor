# Multi-Repo-Unterstuetzung

## Ziel
Mehr als ein GitHub-Repository pro Projekt verknuepfen (aktuell ist
`settings.github_repo` ein einzelner String).

## Ansatz
- `store.Project`: `repos: list[str]` ergaenzen (`settings.github_repo`
  bleibt als globaler Fallback fuer Projekte ohne eigene Liste).
- `app/github_client.py`: PR-Abfrage ueber mehrere Repos aggregieren.
- `app/views/dashboard.py`: PR-Liste nach Repo gruppieren/kennzeichnen.

## Betroffene Dateien
`app/store.py`, `app/github_client.py`, `app/views/dashboard.py`,
`app/views/settings.py`.
