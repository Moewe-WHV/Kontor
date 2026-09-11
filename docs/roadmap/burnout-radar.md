# Burnout-Radar

## Ziel
Fruehindikator fuer Ueberlastung ueber mehrere Sprints hinweg (dauerhafte
Ueberbuchung, viele Ueberstunden-Worklogs, schlechte Team-Wetter-Werte).

## Ansatz
- `store.py`: `burnout_signals(member_id)` kombiniert `member_load`-Historie
  ueber mehrere Sprints, Mood-Score-Trend (`moods`) und Haeufung von
  Abwesenheiten kurzfristig vor/nach Belastungsspitzen.
- Ampel/Trend pro Person als Gespraechsvorbereitung in
  `app/views/one_on_ones.py`, oder eigene, kleine Ansicht.

## Betroffene Dateien
`app/store.py`, `app/views/one_on_ones.py`, ggf. neues
`app/views/burnout.py`.
