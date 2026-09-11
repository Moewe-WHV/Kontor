# Overbooking-Warner

## Ziel
Warnung, wenn einem Crew-Mitglied im aktiven Sprint mehr Stunden zugewiesen
sind als Kapazitaet/Richtwert hergeben.

## Ausgangslage
`store.member_load()` und `store.member_richtwert()` existieren bereits.

## Ansatz
- Neuer Helfer `store.overbooked_members(sprint)` liefert je Mitglied die
  Differenz Zuweisung vs. Richtwert/erklaerte Kapazitaet.
- UI-Warnung (Badge/Tooltip) in `app/views/capacity.py` und
  `app/views/board.py` bei Ueberbuchung.
- Hinweis im Fahrplan (`app/views/today.py`), wenn im aktiven Sprint jemand
  ueberbucht ist.

## Betroffene Dateien
`app/store.py`, `app/views/capacity.py`, `app/views/board.py`,
`app/views/today.py`.
