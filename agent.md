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

## Erwartetes Ergebnis
- Eine vollstaendig definierte Operator-Chain pro Log-Typ
- Normalisierung auf folgendes Zielmodell:
  - `body` bzw. Splunk `event`: ausschliesslich die eigentliche Log Message
  - Alle weiteren Felder als Attribute bzw. Splunk Fields

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
Die folgenden Dateien werden spaeter mit konkreten Beispielen befuellt und duerfen nicht veraendert werden:

- `tests/fixtures/kv_line.log`
- `tests/fixtures/spring_ecs_flat.json`
- `tests/fixtures/ecs_nested.json`

## Verbotene Aktionen
- Keine manuelle Logik ausserhalb von Stanza Operators
- Kein Vorschlagen von Operatoren ohne zugehoerige Tests
- Kein Verweis auf externe Tools ausser Docker
