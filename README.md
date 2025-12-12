# OpenTelemetry Collector fuer Containerd Logs zu Splunk HEC

## Zielsetzung
Testgetriebener OpenTelemetry Collector, der Kubernetes Containerd Logs mit Stanza Operators normiert. Fokus: vollautomatische, dockerisierte Tests.

## Relevante Doku
- Stanza Operators (opentelemetry-collector-contrib): https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/pkg/stanza/docs/operators

## Architekturuebersicht
- **Input**: Containerd file-basierte Logs (CRI Layout)
- **Processing**: Stanza Operator Chain (container parser, json/kv parsing, Flattening)
- **Output**: aktuell File-Exporter (tests/output/logs.json) als golden source; spaeter Splunk HEC

Zielmodell:
- Body/Event = reine Log Message
- Alle Metadaten als Attributes/Fields

## Unterstuetzte Log-Formate
1. Key-Value Line Logs
2. Spring Boot ECS-like Logs, nicht nested
3. Vollstaendig ECS-kompatible, nested Logs

Jeder Log-Typ wird isoliert getestet.

## Projektstruktur
```
.
├── collector/
│   └── docker/otel-collector.yaml  # Aktuelle, getestete Pipeline
├── tests/
│   ├── fixtures/
│   │   ├── kv_line.log
│   │   ├── spring_ecs_flat.json
│   │   └── ecs_nested.json
│   ├── expected/
│   │   ├── kv_line.json
│   │   ├── spring_ecs_flat.json
│   │   └── ecs_nested.json
│   ├── output/                     # File-Exporter Ziel (gitignored, .gitkeep)
│   └── test.sh                     # Docker-basierter Test-Runner
├── docker-compose.yaml
├── agent.md
└── README.md
```

## Testkonzept
- Docker-only: `./tests/test.sh` startet `docker compose`, sammelt OTLP-File-Export (`tests/output/logs.json`), normalisiert per `jq`, diff gegen `tests/expected/*.json`.
- Fixtures sind bindend; Operator-Chain verarbeitet ausschliesslich diese Beispiele.
- File-Exporter dient als Golden Master. HEC-Anbindung kann spaeter auf Basis desselben Outputs erfolgen.

### Voraussetzungen
- Docker + Docker Compose Plugin
- `jq` lokal (Test-Script nutzt es ausserhalb des Containers)

### Ausfuehrung
```
./tests/test.sh
```

### Erwartete Ergebnisse
- Exit-Code 0, Meldung `All tests passed.`
- Ausgegebene Datei `tests/output/logs.json` (OTLP JSON vom File-Exporter)

## Designprinzipien
- Deterministisch
- Reproduzierbar
- Keine impliziten Defaults
- Keine versteckte Logik

## Aktueller Pipeline-Stand (docker/otel-collector.yaml)
- `receiver.filelog`: container parser (containerd) -> router (strukturbasiert: JSON vs. KV) -> branch-spezifische Parser -> gemeinsame Cleanup-Phase (Removal von Container-Metadaten).
- `exporter.file`: schreibt nach `/output/logs.json` (gemountet auf `tests/output/logs.json`).
- `processor.batch`: Standard-Batching.

## Naechste Schritte
1. Splunk HEC Exporter einhaengen und Test-Runner erweitern, um HEC-Payload zu validieren.
