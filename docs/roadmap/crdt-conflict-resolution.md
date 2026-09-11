# CRDT-Konfliktloesung

## Ziel
Konfliktfreies Zusammenfuehren, wenn zwei Instanzen gleichzeitig
`pm.json` aendern (z. B. Multi-Instance-Deployment oder ein
offline-faehiger Client).

## Ansatz
- Groesserer Architektur-Schnitt: die JSON-Datei durch eine CRDT-taugliche
  Struktur ersetzen (z. B. Last-Write-Wins je Feld mit Vektor-/Lamport-Uhr)
  oder ein bestehendes Format/Bibliothek (Automerge-, Yjs-inspiriert)
  heranziehen.
- Erst sinnvoll priorisieren, sobald es ueberhaupt mehrere gleichzeitige
  Schreiber gibt – haengt an Entscheidungen aus
  `feature/zero-downtime-reload` bzw. einer Mehrinstanz-Architektur.

## Betroffene Dateien
`app/store.py` (grundlegend), Datenformat `pm.json` (Breaking Change,
Migration noetig, siehe `SCHEMA`-Mechanismus).
