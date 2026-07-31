# Changelog

## [1.0.6] - 2026-07-31

### Added
- Benachrichtigungs-Titel, -Betreff und -Nachricht unterstützen jetzt Jinja-Templates (z. B. `{{ states('sensor.<aufgabe>_tage_seit_erledigung') }}`), sodass Sensorwerte direkt in den Text eingesetzt werden können

## [1.0.5] - 2026-07-31

### Changed
- Benachrichtigungs-Tags müssen nicht mehr eindeutig sein – mehrere Aufgaben dürfen denselben Tag verwenden (z. B. um Benachrichtigungen zu gruppieren/zu überschreiben)

## [1.0.4] - 2026-07-31

### Changed
- Maximales Fälligkeitsintervall von 100 auf 365 Tage erhöht (ermöglicht z. B. jährliche Aufgaben)

## [1.0.3] - 2026-06-04

### Fixed
- Übersicht-Gerät ist jetzt ein vollständig eigenständiger Eintrag (eigener System-Config-Entry) und nicht mehr an Task-Geräte gebunden
- Veraltete Verknüpfungen des Übersicht-Geräts mit Task-Entries werden beim Integration-Reload automatisch bereinigt

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
