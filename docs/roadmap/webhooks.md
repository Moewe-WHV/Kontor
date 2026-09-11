# Ausgehende Webhooks

## Ziel
Ausgehende Webhooks bei definierten Ereignissen (Task fertig, Incident
eroeffnet, Release live, ...).

## Ansatz
- `Store._listeners` (siehe `store.on_change`) feuert aktuell nur ein
  generisches "irgendwas hat sich geaendert" ohne Ereignistyp – fuer
  gezielte Webhooks wird ein typisiertes Event noetig (z. B.
  `store.emit('task.done', task)` an den bestehenden Mutationsstellen).
- Neues `app/webhooks.py`: konfigurierbare Ziel-URLs je Ereignistyp
  (Verwaltung in `app/views/settings.py`), HMAC-Signatur im Payload,
  Retry mit Backoff.

## Betroffene Dateien
`app/store.py` (Event-Typen), neues `app/webhooks.py`,
`app/views/settings.py`.
