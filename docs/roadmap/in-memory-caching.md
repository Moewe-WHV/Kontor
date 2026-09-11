# In-Memory-Caching

## Ziel
Teure abgeleitete Berechnungen (`project_cost`, `weekly_report`,
`quality_stats`, ...) cachen statt bei jedem Seitenaufruf neu zu berechnen.

## Ansatz
- Vor der Umsetzung kurz profilen, ob das bei der aktuellen Groesse
  (JSON-Datei, ein Prozess) ueberhaupt spuerbar ist.
- Falls ja: einfacher manueller Cache mit Invalidierung ueber einen
  Aenderungszaehler, der bei `store.save()` hochgezaehlt wird (Cache-Key
  inkl. Zaehler), statt pauschal `functools.lru_cache` auf Store-Methoden
  (die haben veraenderliche `self`-Seiteneffekte).
- Gezielt bei den nachweislich teuersten Funktionen ansetzen, nicht
  pauschal ueber den ganzen Store.

## Betroffene Dateien
`app/store.py`.
