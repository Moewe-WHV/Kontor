# Mood-to-Risk Alerts

## Ziel
Anhaltend schlechtes Team-Wetter automatisch als Risiko-Entwurf
vorschlagen, statt dass es im Stillen untergeht.

## Ansatz
- `store.py`: Trend-Erkennung (z. B. Durchschnitt der letzten zwei Sprints
  unter einem Schwellwert) loest einen automatischen `Risk`-Entwurf aus
  ("Team-Stimmung im Keller", verweist auf betroffenen Sprint).
- Hinweis dazu im Fahrplan (`app/views/today.py`) oder Dashboard, sobald
  ein solcher Trend erkannt wird; Verlinkung zu `app/views/raid.py`.

## Betroffene Dateien
`app/store.py`, `app/views/wetter.py`, `app/views/raid.py`,
`app/views/today.py`.
