## Hausarbeiten

Verwalte wiederkehrende Hausarbeiten direkt in Home Assistant.

Pro Aufgabe wird automatisch ein **Gerät** mit diesen Entities angelegt:

| Entity | Beschreibung |
|---|---|
| Binary Sensor „Fällig" | `on` wenn Fälligkeitsdatum erreicht |
| Datum „Nächste Fälligkeit" | Editierbares Fälligkeitsdatum |
| Button „Erledigt" | Erstellt Kalendereintrag, setzt nächsten Termin |
| Button „Überspringen" | Verschiebt Termin ohne Kalendereintrag |
| Sensor „Tage seit Erledigung" | Tage seit letztem Kalendereintrag |

Benachrichtigungen mit „Erledigt"- und „Verschieben"-Aktionen für die HA Companion App sind integriert. Der Zustand wird persistent gespeichert und übersteht HA-Neustarts.

**Mindestanforderungen:** Home Assistant ≥ 2024.1.0 · Kalender-Integration · Benachrichtigungs-Skript
