# Anonymes Team-Wetter

## Ziel
Team-Wetter (Stimmung) anonym abgeben koennen, damit ehrliches Feedback
wahrscheinlicher wird.

## Ansatz
- `store.Mood` um `anonymous: bool` erweitern; bei `anonymous=True` wird
  der Eintrag zwar weiter unter `member_id` gespeichert (fuer Duplikat-
  Vermeidung/Bearbeiten), aber in der UI nie namentlich angezeigt.
- `app/views/wetter.py`: Auswahl "anonym abgeben"; Aggregat-Ansicht
  (Durchschnitt/Verteilung) statt Namensliste, sobald anonyme Eintraege
  vorhanden sind.

## Betroffene Dateien
`app/store.py`, `app/views/wetter.py`.
