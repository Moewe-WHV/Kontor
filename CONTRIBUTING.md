# Contributing

Kontor ist in erster Linie ein persönliches Projekt – gebaut für den
eigenen Bedarf und als Showcase veröffentlicht. Es gibt keinen festen
Fahrplan und keine Verpflichtung, Beiträge zu betreuen.

## Issues

Bug-Reports und Vorschläge sind willkommen. Bitte kurz beschreiben:

- Was erwartet, was passiert stattdessen
- Schritte zur Reproduktion
- relevante Umgebung (lokal via Docker Compose / Produktivbetrieb)

## Pull Requests

Kleine, klar begründete PRs (Bugfixes, kleinere Verbesserungen) sind
willkommen, werden aber nicht zeitnah garantiert gemerged. Für größere
Änderungen bitte vorher ein Issue eröffnen und kurz die Idee abstimmen,
bevor viel Arbeit hineinfließt.

## Lokale Entwicklung

```bash
cp .env.example .env
docker compose up --build
```

Details siehe [README.md](README.md#schnellstart-lokal).
