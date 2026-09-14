# Changelog

## 2.5

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
- **Echter Projektzugriff pro Login** (`app/store.py`: `ProjectAccess`,
  `app/views/project_access.py`, neuer Bereich „Projektzugriff"): eine
  Teamleitung kann Kolleg:innen einen Zugang geben, der nur das jeweilige
  Projekt zeigt (Header-Umschalter und Projektliste filtern jetzt danach)
  und dort rollenspezifisch (Teamleitung/Mitglied) Führungsbereiche
  (Budget, Stakeholder, RACI, Lieferanten, Änderungen, 1:1s, Flotte,
  Steckbrief) ein-/ausblendet. Ersetzt für konfigurierte Projekte die
  bisherige, frei wählbare „Als wer arbeitest du?"-Session-Auswahl durch
  die echte, am Login hängende Rolle. Bestehende Projekte ohne
  konfigurierten Zugriff bleiben unverändert für alle offen.
- **Planning-Poker-Fix** (`app/views/poker.py`): die Task-Auswahl wurde
  vom Live-Poll (alle 1,5 s) unterbrochen, sobald man das Dropdown gerade
  offen hatte. Panel rendert jetzt nur noch neu, wenn sich der
  Abstimmungsstand tatsächlich geändert hat.
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
