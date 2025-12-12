# Collector

## Docker Runtime
- Konfiguration: `collector/docker/otel-collector.yaml`
- Eingehende Logs: `/fixtures/*.log` und `/fixtures/*.json` (Containerd CRI)
- Ausgehende Logs: File-Exporter nach `/output/logs.json` (gemountet auf `tests/output/logs.json`)

## Pipeline (kurz)
- `container` parser (format: containerd, ohne Pfad-Metadaten)
- Escape-Fixes fuer das verschachtelte ECS-Beispiel
- `json_parser` fuer JSON Bodies
- `key_value_parser` fuer KV-Line-Logs (`ts=...; sev=...; ...; msg="..."`)
- Normalisierung: Message nach `body`, Metadaten nach Attributes, Entfernen von Container-Metadaten
- `batch` processor, `file` exporter

## Per-Log-Typ Config Platzhalter
`collector/config/*.yaml` sind reserviert fuer spaetere, dedizierte Pipelines je Log-Format.
