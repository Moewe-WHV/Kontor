# Planning Poker

## Ziel
Gemeinsames Schaetzen von Story-Stunden/Punkten im Sprint-Planning
(Karten verdeckt waehlen, dann gemeinsam aufdecken).

## Ansatz
- Leichter Realtime-Session-State (NiceGUI eignet sich dafuer gut): pro
  Task laufende Abstimmung mit Stimmen je `member_id` und
  `revealed: bool`. Bewusst NICHT in `pm.json` persistieren (fluechtiger
  Session-State reicht, Ergebnis wird am Ende manuell in
  `Task.estimate_h` uebernommen).
- Neue Ansicht `app/views/poker.py`, verlinkt aus Board/Sprint-Planung.

## Betroffene Dateien
Neues `app/views/poker.py`, `app/components.py` (Nav-Eintrag/Verlinkung
aus dem Task-Dialog).
