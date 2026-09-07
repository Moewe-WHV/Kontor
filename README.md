# Kontor – Projektleitstand
[![License: MIT](https://shields.io)](LICENSE)


Ein Mehrprojekt-Werkzeugkasten für Teamleitungen in der Softwareentwicklung:
Portfolio, Kanban, Sprint- & Kapazitätsplanung, Abwesenheiten, Standup,
Stundenbuchung, Burndown & Metriken, Retro, Team-Wetter, Risiken &
Entscheidungen, Releases, Ideen-Speicher, 1:1-Gespräche, Kalender – plus
eine GitHub-PR-Sicht direkt im Dashboard.

Läuft als einzelne Python-Anwendung ([NiceGUI](https://nicegui.io)), Daten
liegen in einer einfachen JSON-Datei – kein Datenbankserver nötig.

> Frisch geklont zeigt die App fiktive Demo-Daten (drei Beispielprojekte,
> Beispiel-Team). Eigene Daten entstehen einfach durch Benutzung – siehe
> [Daten](#daten--persistenz).

## Features

- **Portfolio & Projekte** – mehrere Projekte parallel, Steckbrief/Charter,
  Scope, Erfolgskriterien, Annahmen
- **Kanban-Board** mit Prioritäten, Labels, Blockern, Abhängigkeiten
- **Sprints & Kapazitätsplanung**, Burndown, Velocity
- **Team**: Mitglieder, Abwesenheiten, Auslastung, Stundenbuchung
- **Standup, Retro (mit Aktionspunkten), Team-Wetter** (Stimmungsbarometer)
- **Risiken, Entscheidungen, Change Requests, RAID-Log**
- **Releases, Environments, Deployments, Incidents**
- **Requirements, Roadmap, Milestones, OKRs, RACI**
- **Stakeholder, Meetings, 1:1-Gespräche, Vendors, Dokumente, Lessons Learned**
- **GitHub-Integration**: offene PRs inkl. Review-/CI-Status direkt im
  Dashboard (optional, per Token)
- **Passwort-Login** (optional, für den Produktivbetrieb)

## Tech-Stack

- [NiceGUI](https://nicegui.io) (Python, kein separates Frontend-Build)
- Datenhaltung in `app/data/pm.json`, kein DB-Server
- Docker / Docker Compose für Dev- und Produktivbetrieb
- Caddy als Reverse Proxy mit automatischem HTTPS (Produktivbetrieb)

## Schnellstart (lokal)

Voraussetzung: Docker + Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

Anschließend läuft die App unter <http://localhost:8080> – mit Hot-Reload,
ohne Login (kein `APP_PASSWORD` gesetzt), gefüllt mit Demo-Daten.

Alternativ öffnet sich das Projekt in VS Code direkt als
[Dev Container](.devcontainer/devcontainer.json) ("Reopen in Container").

### Umgebungsvariablen (`.env`, optional)

| Variable         | Bedeutung                                              |
|------------------|---------------------------------------------------------|
| `GITHUB_TOKEN`   | PAT für die GitHub-API (höheres Rate-Limit / private Repos) |
| `GITHUB_REPO`    | Default-Repo `owner/name` für die PR-Ansicht           |
| `STORAGE_SECRET` | Signiert die NiceGUI-Session-Cookies                   |
| `APP_USERNAME`   | Login-Benutzer (Default `admin`)                       |
| `APP_PASSWORD`   | Login-Passwort – leer = kein Login (nur lokal sinnvoll) |

## Deployment

Für den Produktivbetrieb auf einem VPS (Docker + Caddy, automatisches
HTTPS via Let's Encrypt, Pflicht-Login) siehe [DEPLOY.md](DEPLOY.md).

## Daten & Persistenz

Alle Inhalte liegen in `app/data/pm.json`. Existiert die Datei nicht (z. B.
direkt nach dem Klonen), erzeugt die App beim ersten Start automatisch
fiktive Demo-Daten (siehe `seed()` in [`app/store.py`](app/store.py)). Diese
Datei ist bewusst in [`.gitignore`](.gitignore) ausgeschlossen, damit keine
echten Arbeitsdaten versehentlich ins Repository gelangen.

## Lizenz

[MIT](LICENSE)
