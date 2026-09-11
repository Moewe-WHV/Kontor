# Zero-Downtime Reload

## Ziel
Config-/Daten-Reload ohne Verbindungsabbruch bestehender NiceGUI-Sessions
(z. B. nach einem Deploy oder externer Aenderung an `pm.json`).

## Ausgangslage
`/healthz` und `/readyz` existieren bereits (siehe
`feature/security-multiuser-ops`), aktuell rein statisch/liveness-artig.

## Ansatz
- SIGHUP-Handler, der `store.load()` erneut aufruft statt eines
  Prozess-Neustarts (Store ist bereits Thread-safe via `self._lock`).
- `/readyz` waehrend des Reloads kurz auf "reloading" setzen, damit ein
  Loadbalancer/Caddy in dem Moment keinen neuen Traffic schickt.
- Dokumentation fuer Rolling-Restarts (2 Replikas + graceful drain) in
  `DEPLOY.md`/`Caddyfile` ergaenzen.

## Betroffene Dateien
`app/main.py`, `app/store.py`, `DEPLOY.md`, `Caddyfile`.
