# Tests

## Ziel
Docker-only Validierung der Stanza-Pipeline gegen die bereitgestellten Fixtures.

## Ablauf
- `./tests/test.sh`
  - startet `docker compose` mit Collector (filelog + Stanza) und HEC-Mock
  - Collector exportiert OTLP-Logs als JSON nach `tests/output/logs.json`
  - `jq` normalisiert die Records (`message` + `attributes`) und vergleicht mit `tests/expected/*.json`

## Artefakte
- `tests/fixtures/`: Input-Logs (Containerd Layout)
- `tests/expected/`: Erwartete, normalisierte Records (Golden Master)
- `tests/output/`: Laufzeit-Output des File-Exporters (gitignored, .gitkeep bleibt)

## Voraussetzungen
- Docker + Docker Compose Plugin
- `jq` lokal

## Erfolgskriterium
- Skript endet mit `All tests passed.` und Exit-Code 0.
