# Agent Instructions fuer Codex

## Ziel
Du entwickelst einen OpenTelemetry Collector mit Stanza Operators, welcher Containerd file-basierte Kubernetes Logs verarbeitet und an Splunk via HEC sendet.

Unterstuetzte Log-Formate:
1. Line-Logging mit Key-Value-Pairs im Application Log
2. ECS-aehnliche Spring-Boot-Logs, nicht nested (Spring Boot 3.4.4)
3. ECS-kompatible, nested JSON Logs

## Verbindliche Arbeitsweise
- **Testgetrieben**: Jede Operator-Chain wird ausschliesslich anhand automatisierter Tests entwickelt.
- **Docker-only**: Alle Tests und Ausfuehrungen muessen vollstaendig in Docker Containern laufen. Keine lokalen Abhaengigkeiten.
- **Keine ungetesteten Vorschlaege**: Du darfst ausschliesslich Konfigurationen, Operatoren und Anpassungen vorschlagen, die durch die vorhandenen Tests validiert sind.
- **Keine Annahmen**: Verarbeite ausschliesslich die bereitgestellten Test-Log-Beispiele.
- **Struktur-basiert**: Routing/Parsing orientiert sich an Struktur bzw. vorhandenen Feldern (z.B. JSON vs. KV Layout) – keine inhaltlichen Pattern auf der Log-Message selbst.
- **Gute Praxis**: Nutze Router + klar getrennte Pipelines; entferne Container-Metadaten; halte Body als reine Message, Attribute als Felder; keine unnoetigen Dateien im Repo; Dokumentation kurz und verfuegbar (README, tests/README, collector/README).
- **Systemunabhaengig testen**: Vergleiche werden in Containern ausgefuehrt (Python-Slim), keine lokalen Tools wie `jq` noetig; Container-Logs muessen immer sichtbar sein.
- **Keine Inline-Skripte**: Hilfslogik fuer Tests (Parsing/Compare) liegt in eigenen Files (z.B. `tests/compare.py`), nicht als Inline-Heredoc in Shell-Skripten.
- **Stabile, robuste Abhaengigkeiten**: Images versionieren (Collector, MockServer), Healthchecks/Depends-On fuer Mocks und API-basierte Assertions (MockServer statt Eigenbau), Aushaengepunkte fuer Payload-Retrieval in Tests.

## Erwartetes Ergebnis
- Eine vollstaendig definierte Operator-Chain pro Log-Typ
- Normalisierung auf folgendes Zielmodell:
  - `body` bzw. Splunk `event`: ausschliesslich die eigentliche Log Message
  - Alle weiteren Felder als Attribute bzw. Splunk Fields
- sämtliche Interaktionen mit dem Repo sind in kurzen & knakigen readme (untereinander verlinkt) beschrieben. Beschreibung in Deutch, CH Rechtschreibung.

## Teststrategie
- Verwende den offiziellen OpenTelemetry Collector Contrib Docker Image
- Tests bestehen aus:
  - Input: File-basierte Logs (Containerd-Layout)
  - Verarbeitung: Stanza Operators
  - Output:
    - entweder gemockter Splunk HEC Endpoint
    - oder validierter Export Payload (JSON) vor HEC-Serialisierung
- Tests schlagen fehl, wenn:
  - Felder fehlen oder falsch gemappt sind
  - die Message nicht korrekt extrahiert wurde
  - das Schema vom erwarteten Zielmodell abweicht

## Platzhalter fuer Testfaelle
Die folgenden Dateien enthalten deine Testfälle:

- `tests/fixtures/kv_line.log`
- `tests/fixtures/spring_ecs_flat.json`
- `tests/fixtures/ecs_nested.json`

## Verbotene Aktionen
- Keine manuelle Logik ausserhalb von Stanza Operators
- Kein Vorschlagen von Operatoren ohne zugehoerige Tests
- Kein Verweis auf externe Tools ausser Docker
