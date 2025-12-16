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
1. Key-Value Line Logs (z. B. `ts=...; sev=INFO; ...`) – Level wird aus `sev=` via Regex geparsed.
2. Plain Spring Boot Logs (mehrzeilig) – Timestamp + `- LEVEL` am Zeilenanfang, Level aus dem Prefix.
3. Apache HTTPD Log-Style – Timestamp gefolgt von `[...][ssl:<level>]...`, Level aus dem `[mod:<level>]` Block.
4. Spring Boot ECS-like Logs, nicht nested
5. Vollstaendig ECS-kompatible, nested Logs

Jeder Log-Typ wird isoliert getestet.

## Projektstruktur
```
.
├── collector/
│   └── docker/otel-collector.yaml  # Aktuelle, getestete Pipeline
├── tests/
│   ├── fixtures/var/log/pods/...    # k8s Containerd Pfadlayout (Namespace_Pod_UID/Container/Restart.log)
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
- Docker-only: `./tests/test.sh` startet `docker compose`, sammelt OTLP-File-Export (`tests/output/logs.json`) und HEC-Mock (`tests/output/hec.json`), normalisiert/vergleicht im `python:3.12-slim` Container gegen `tests/expected/*.json` (inkl. k8s Metadata aus Pfad).
- Fixtures sind bindend; Operator-Chain verarbeitet ausschliesslich diese Beispiele.
- File-Exporter dient als Golden Master; HEC wird parallel verifiziert.

### Voraussetzungen
- Docker + Docker Compose Plugin
- Keine lokalen Parser-Tools noetig; Vergleich laeuft in Containern

### Ausfuehrung
```
./tests/test.sh
```

### Erwartete Ergebnisse
- Exit-Code 0, Meldung `All tests passed.`
- Ausgegebene Dateien unter `tests/output/` (OTLP JSON + HEC NDJSON)

## Designprinzipien
- Deterministisch
- Reproduzierbar
- Keine impliziten Defaults
- Keine versteckte Logik

## Aktueller Pipeline-Stand (docker/otel-collector.yaml)
- `receiver.filelog`: container parser (containerd) -> router (strukturbasiert: JSON vs. KV/plain) -> branch-spezifische Parser -> gemeinsame Cleanup-Phase (Removal von Container-Metadaten).
- `exporter.file`: schreibt nach `/output/logs.json` (gemountet auf `tests/output/logs.json`).
- `exporter.splunk_hec`: sendet an HEC-Mock (http://hec-mock:8088/services/collector).
- `processor.batch`: Standard-Batching.

### Parsing-Details (plain/KV)
- Multiline-Recombine erkennt neue Eintraege via Timestamp, JSON-Start oder GKE-Style `IWE` Prefix.
- Level-Erkennung:
  - Plain Spring: Regex auf `YYYY-MM-DD HH:MM:SS.mmm - LEVEL`.
- Apache: Regex auf `[...]` Blocks mit `mod:<level>` (z. B. `[ssl:warn]`).
  - KV: Regex auf `sev=<LEVEL>` falls noch kein Level gesetzt.
- Gefundene Level werden nach `attributes["log.level"]` verschoben.

## Naechste Schritte
1. Optional: Ressource-Attribute anreichern (k8s metadata) und in HEC-Tests reflektieren.
