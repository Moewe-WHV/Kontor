# CI/CD-Visualizer

## Ziel
Sichtbarkeit von CI/CD-Laeufen (GitHub Actions) im Leitstand: Status je
Workflow/Branch, letzter Lauf, Dauer.

## Ansatz
- `app/github_client.py` um die Workflow-Runs-API erweitern
  (`GET /repos/{repo}/actions/runs`).
- Neue Ansicht `app/views/cicd.py`: Liste/Ampel je Workflow mit Link zum
  Lauf auf GitHub.
- Nav-Eintrag in `app/components.py` (Gruppe "Maschinenraum" passt thematisch).

## Betroffene Dateien
`app/github_client.py`, neues `app/views/cicd.py`, `app/components.py`,
`app/main.py` (Route registrieren).
