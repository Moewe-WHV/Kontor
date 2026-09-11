# Changelog

## 2.1 (unreleased)

Aufbauend auf 2.0 (siehe [docs/V2.md](docs/V2.md)) wurden drei Feature-Branches
zusammengeführt sowie 18 weitere als Roadmap-Einträge dokumentiert.

### Neu

- **Englische Übersetzung / i18n** (`app/i18n.py`): Die komplette Navigation,
  Handbuch- und Einstellungs-Oberfläche läuft jetzt über
  Übersetzungsschlüssel (`t()`), Deutsch und Englisch umschaltbar.
- **Solo-Modus** (`app/store.py`, `app/views/projects.py`,
  `app/views/team.py`): Projekte lassen sich als „Solo" statt „Team"
  anlegen; Rollen-/Führungsbereiche werden dafür automatisch angepasst
  (`viewer_is_leader`, `Project.mode`).
- **Nutzer & Rechte / Auth-Härtung** (`app/auth.py`, `app/oidc.py`,
  `app/views/users.py`): Rollenbasierte Sichtbarkeit (`auth.has_role`),
  neuer `/users`-Bereich (nur für Admins sichtbar), OIDC-Grundgerüst.
- **Planning Poker** (`app/views/poker.py`, siehe
  [docs/roadmap/planning-poker.md](docs/roadmap/planning-poker.md)):
  gemeinsame, flüchtige Schätzrunde pro Projekt (Kartendeck in Stunden,
  verdeckt abstimmen, gemeinsam aufdecken, Mittelwert/Median direkt als
  `Task.estimate_h` übernehmen), verlinkt aus dem Task-Dialog.
- **Kleinere Fixes**: Nav-Drawer überdeckte auf Handy-Breite die ganze
  Seite; GitHub-PR-Kachel auf dem Leitstand konnte durch unbegrenzte
  Listen beliebig lang werden und teilte ihren Zustand versehentlich
  zwischen allen angemeldeten Nutzern; Daten-Reset/-Import ohne
  Admin-Rechte möglich; fehlende Datum-Validierung bei Abwesenheiten/
  Sprints/Epics; ~20 Formulare ohne Speichern-Bestätigung.

### Roadmap (dokumentiert, noch nicht implementiert)

Siehe `docs/roadmap/`: anonymous-weather, auto-backups,
auto-release-notes, burnout-radar, cicd-visualizer,
crdt-conflict-resolution, ical-sync, in-memory-caching,
mood-to-risk-alerts, multi-repo, oidc-oauth2, overbooking-warner,
prometheus-metrics, skills-matrix, slack-discord-bots,
webhooks, zero-downtime-reload.

### Basis

- **2.0**: Hell-/Dunkel-Ansicht, Einstellungsbereich (`/settings`), Module
  je Projekt (`/modules`) — siehe [docs/V2.md](docs/V2.md).

## 2.0

Siehe [docs/V2.md](docs/V2.md).
