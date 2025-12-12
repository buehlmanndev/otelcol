# Collector

## Docker Runtime
- Konfiguration: `collector/docker/otel-collector.yaml`
- Eingehende Logs: `/fixtures/*.log` und `/fixtures/*.json` (Containerd CRI)
- Ausgehende Logs: File-Exporter nach `/output/logs.json` (gemountet auf `tests/output/logs.json`)

## Pipeline (kurz)
- `container` parser (format: containerd, ohne Pfad-Metadaten)
- `router` mit strukturellem Split:
  - JSON/ECS-Route: Escape-Fixes, `json_parser`, Flatten von `log.*`/`process.*`, Message nach `body`
  - KV-Route: `key_value_parser` fuer `ts=...; sev=...; ...; msg="..."`, Cleanup/Trim, Message nach `body`
  - Default: direkte Weiterleitung in gemeinsame Cleanup
- Gemeinsames Cleanup: Entfernt Container-Metadaten (`log.*`, `logtag`) und Restfelder (`message`/`msg` nach Move)
- `batch` processor, `file` exporter
