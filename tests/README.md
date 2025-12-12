# Tests

## Ziel
Docker-only Validierung der Stanza-Pipeline gegen die bereitgestellten Fixtures.

## Ablauf
- `./tests/test.sh`
  - startet `docker compose` mit Collector (filelog + Stanza) und MockServer (HEC Endpoint)
  - Collector exportiert:
    - OTLP-Logs als JSON nach `tests/output/logs.json` (File-Exporter), inkl. k8s Metadata aus Pfad
    - HEC-Events an den MockServer (Requests werden via API abgerufen nach `tests/output/hec.json`)
  - Normalisierung/ Vergleich erfolgen in einem `python:3.12-slim` Container gegen `tests/expected/*.json`

## Artefakte
- `tests/fixtures/`: Input-Logs (Containerd Layout)
- `tests/fixtures/var/log/pods/...`: k8s-kompatibles Pfadlayout fuer Containerd Logs (namespace_pod_uid/container/restart.log)
- `tests/expected/`: Erwartete, normalisierte Records (Golden Master)
- `tests/output/`: Laufzeit-Output des File-Exporters und HEC-Mock-Retrieval (gitignored, .gitkeep bleibt)

## Voraussetzungen
- Docker + Docker Compose Plugin
- Vergleich/Parsing laeuft in einem Python-Slim Container (kein lokales `jq` erforderlich)

## Erfolgskriterium
- Skript endet mit `All tests passed.` und Exit-Code 0.
