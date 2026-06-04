# Changelog

## [1.0.2] - 2026-06-04

### Fixed
- Übersicht-Gerät wird jetzt korrekt als eigenständiges Gerät in der HA-Geräteliste angezeigt und nicht mehr einem Aufgaben-Gerät zugeordnet

## [1.0.0] - 2026-06-03

### Added
- Initiale Veröffentlichung als HACS Custom Integration
- Pro Aufgabe: Gerät mit Binary Sensor, Datum-Entity, Erledigt/Überspringen-Buttons und Tage-Sensor
- Persistente Zustandsspeicherung via HA Storage (übersteht Neustarts)
- Automatische Fälligkeitsprüfung täglich um 01:00 und 14:00 Uhr
- Kalendereintrag bei Erledigung (mit Duplikat-Prüfung)
- Mobile Benachrichtigungen mit Aktions-Buttons (Erledigt / Verschieben)
- HA-Aktionen `hausarbeiten.pruefen` und `hausarbeiten.benachrichtigen`
- Vollständige deutsche UI-Übersetzung
