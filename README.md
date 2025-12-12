# OpenTelemetry Collector fuer Containerd Logs zu Splunk HEC

## Zielsetzung
Dieses Projekt implementiert einen testgetriebenen OpenTelemetry Collector, der Kubernetes Containerd Logs verarbeitet und normiert an Splunk via HTTP Event Collector (HEC) weiterleitet.

Der Fokus liegt auf reproduzierbaren, vollautomatisierten Tests innerhalb von Docker Containern.

## Relevante Doku
- Stanza Operators (opentelemetry-collector-contrib): https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/pkg/stanza/docs/operators

## Architekturuebersicht
- **Input**: Containerd file-basierte Logs
- **Processing**: Stanza Operator Chains (pro Log-Format)
- **Output**: Splunk HEC kompatibles Event-Format

Splunk Zielmodell:
- Log Message ausschliesslich als Message (Event Body)
- Saemtliche Metadaten und extrahierte Felder als Attribute

## Unterstuetzte Log-Formate
1. Key-Value Line Logs
2. Spring Boot ECS-like Logs, nicht nested
3. Vollstaendig ECS-kompatible, nested Logs

Jeder Log-Typ wird isoliert getestet.

## Projektstruktur
```
.
├── collector/
│   ├── config/
│   │   ├── kv_line.yaml
│   │   ├── spring_ecs_flat.yaml
│   │   └── ecs_nested.yaml
│   └── docker/
│       └── otel-collector.yaml
├── tests/
│   ├── fixtures/
│   │   ├── kv_line.log              # Platzhalter
│   │   ├── spring_ecs_flat.json     # Platzhalter
│   │   └── ecs_nested.json          # Platzhalter
│   ├── expected/
│   │   ├── kv_line.json
│   │   ├── spring_ecs_flat.json
│   │   └── ecs_nested.json
│   └── test.sh
├── docker-compose.yaml
├── agent.md
└── README.md
```

## Testkonzept
- Jeder Test:
  - Mountet ein Beispiel-Logfile
  - Startet den Collector mit spezifischer Operator-Chain
  - Faengt den Output ab (Mock-HEC oder JSON Export)
  - Vergleicht gegen erwartetes Resultat

- Tests laufen ausschliesslich via:
```
docker compose up --build --abort-on-container-exit
```

## Platzhalter fuer Log-Beispiele
Die folgenden Dateien muessen durch reale Beispiele ersetzt werden:

- `tests/fixtures/kv_line.log`
- `tests/fixtures/spring_ecs_flat.json`
- `tests/fixtures/ecs_nested.json`

Die Struktur dieser Dateien definiert verbindlich die Operator-Logik.

## Splunk HEC Annahmen
- Token, Endpoint und Index werden via Environment Variablen gesetzt
- Im Testbetrieb wird ein Mock oder Dry-Run Export verwendet
- Kein direkter Write in produktives Splunk waehrend Tests

## Designprinzipien
- Deterministisch
- Reproduzierbar
- Keine impliziten Defaults
- Keine versteckte Logik

## Naechste Schritte
1. Log-Beispiele einfuegen
2. Erwartete Output-JSONs definieren
3. Operator-Chains implementieren
4. Tests iterativ gruenden lassen
