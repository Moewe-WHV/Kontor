# Prometheus Metrics

## Ziel
`/metrics`-Endpoint im Prometheus-Textformat fuer Basismonitoring.

## Ausgangslage
`/metrics` steht bereits in `auth.UNRESTRICTED` (siehe
`feature/security-multiuser-ops`), ist aber noch nicht registriert.

## Ansatz
- `prometheus_client` als Dependency ergaenzen.
- Neues `app/metrics_exporter.py`: Counter/Gauges definieren (z. B.
  `kontor_projects_total`, `kontor_open_incidents`, `kontor_open_bugs_by_severity`,
  Request-Counter ueber eine kleine Middleware).
- In `main.py` unter `/metrics` registrieren.
- Domain-Gauges aus `store.py`-Helfern ableiten (`quality_stats`,
  `open_incidents`, ...) statt Kennzahlen doppelt zu pflegen.

## Betroffene Dateien
`app/main.py`, neues `app/metrics_exporter.py`, `app/requirements.txt`.
