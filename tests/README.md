# Tests

## Ziel
Docker-only Validierung der Stanza-Pipeline gegen die bereitgestellten Fixtures.

## Ablauf
- `./tests/test.sh`
  - startet `docker compose` mit Collector (filelog + Stanza) und HEC-Mock
  - Collector exportiert:
    - OTLP-Logs als JSON nach `tests/output/logs.json` (File-Exporter)
    - HEC-Events an den Mock (`tests/output/hec.ndjson`)
  - Normalisierung/ Vergleich erfolgen in einem `python:3.12-slim` Container gegen `tests/expected/*.json`

## Artefakte
- `tests/fixtures/`: Input-Logs (Containerd Layout)
- `tests/expected/`: Erwartete, normalisierte Records (Golden Master)
- `tests/output/`: Laufzeit-Output des File-Exporters und HEC-Mock (gitignored, .gitkeep bleibt)

## Voraussetzungen
- Docker + Docker Compose Plugin
- Vergleich/Parsing laeuft in einem Python-Slim Container (kein lokales `jq` erforderlich)

## Erfolgskriterium
- Skript endet mit `All tests passed.` und Exit-Code 0.
