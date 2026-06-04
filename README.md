# Hausarbeiten

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![GitHub Release](https://img.shields.io/github/v/release/Caroma97/HACS-Hausarbeiten)](https://github.com/Caroma97/HACS-Hausarbeiten/releases)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Verwaltung von wiederkehrenden Hausarbeiten in Home Assistant. Pro Aufgabe wird automatisch ein Gerät mit allen nötigen Entities angelegt. Eine separate Blueprint-Automation oder manuelle `input_*`-Entities sind nicht mehr erforderlich.

---

## Inhaltsverzeichnis

- [Voraussetzungen](#voraussetzungen)
- [Installation](#installation)
- [Konfiguration](#konfiguration)
- [Entities](#entities)
- [Aktionen](#aktionen)
- [Funktionsweise](#funktionsweise)
- [Benachrichtigungen](#benachrichtigungen)
- [Migration von der Blueprint](#migration-von-der-blueprint)
- [Fehlerbehebung](#fehlerbehebung)

---

## Voraussetzungen

| Anforderung | Details |
|---|---|
| Home Assistant | ≥ 2024.1.0 |
| Kalender-Integration | beliebig (z. B. Local Calendar) |
| Benachrichtigungs-Skript | `script.notification_notify_duplizieren` (konfigurierbar) |

---

## Installation

### HACS (empfohlen)

1. [HACS](https://hacs.xyz/) in Home Assistant installieren.
2. Dieses Repository als **Custom Repository** hinzufügen:
   - HACS öffnen → ⋮ → **Benutzerdefinierte Repositories**
   - URL: `https://github.com/Caroma97/HACS-Hausarbeiten`
   - Kategorie: **Integration**
   - **Hinzufügen** klicken.
3. In HACS nach **Hausarbeiten** suchen und installieren.
4. Home Assistant neu starten.
5. Unter **Einstellungen → Integrationen → Integration hinzufügen** nach **Hausarbeiten** suchen.

### Manuell

1. Den Ordner `custom_components/hausarbeiten/` aus diesem Repository in `config/custom_components/` kopieren:

   ```
   config/
   └── custom_components/
       └── hausarbeiten/
           ├── __init__.py
           ├── manifest.json
           ├── const.py
           ├── config_flow.py
           ├── coordinator.py
           ├── binary_sensor.py
           ├── button.py
           ├── sensor.py
           ├── date.py
           ├── services.yaml
           ├── strings.json
           └── translations/
               └── de.json
   ```

2. Home Assistant neu starten.
3. Unter **Einstellungen → Integrationen → Integration hinzufügen** nach **Hausarbeiten** suchen.

---

## Konfiguration

Die Konfiguration erfolgt vollständig über den UI-Dialog in zwei Schritten. Pro Hausarbeit wird ein eigener Integrationseintrag angelegt. Der Eintragsname im Integrationsbereich entspricht dem konfigurierten **Benachrichtigungs-Titel** (Fallback: Kalender-Stichwort).

### Schritt 1: Aufgaben-Einstellungen

| Feld | Beschreibung | Standard |
|---|---|---|
| **Kalender-Stichwort** | Bezeichnung der Aufgabe – wird als Kalender-Event-Titel und Suchbegriff im Kalender verwendet | – |
| **Kalender** | Kalender-Entity, in dem Erledigungen protokolliert werden | – |
| **Fälligkeitsintervall (Tage)** | Nach einer Erledigung wird der nächste Termin um diese Anzahl Tage verschoben | `3` |
| **Verschieben um Tage** | Beim Überspringen wird der nächste Termin um diese Anzahl Tage verschoben | `2` |

### Schritt 2: Benachrichtigungs-Einstellungen

| Feld | Beschreibung | Standard |
|---|---|---|
| **Titel** | Titel der Benachrichtigung – wird auch als Name des Integrationseintrags verwendet | Kalender-Stichwort |
| **Kurznachricht** | Kurzer Nachrichtentext | – |
| **Detaillierte Nachricht** | Ausführlicher Nachrichtentext | – |
| **Benachrichtigungskanal** | Android-Notification-Channel | `Hausarbeiten` |
| **Benachrichtigungsgruppe** | Gruppierung gleichartiger Nachrichten | `Hausarbeiten` |
| **Tag** | Eindeutiger Identifier der Nachricht; wird für die Zuordnung mobiler Notification-Aktionen benötigt (leer = Kalender-Stichwort) | Kalender-Stichwort |
| **MDI Icon** | Icon in der Benachrichtigungsleiste | `mdi:home-automation` |
| **Sperrbildschirm-Sichtbarkeit** | `Öffentlich` / `Privat` / `Secret` | `Privat` |
| **Alert Once** | Aktualisierungen lösen keine erneute Benachrichtigung aus | `false` |
| **Nachrichten-Icon (Pfad)** | Pfad zu einem PNG-Icon | – |
| **Link** | Seite, die bei Klick auf die Nachricht geöffnet wird | `lovelace-yaml/0#notifications` |
| **Benachrichtigungs-Skript** | HA-Skript, das für den Versand und das Löschen von Benachrichtigungen zuständig ist | `script.notification_notify_duplizieren` |

### Einstellungen nachträglich ändern

Unter **Einstellungen → Integrationen → Hausarbeiten → Konfigurieren**. Ändert sich der Benachrichtigungs-Titel, wird der Eintragsname automatisch aktualisiert.

Das Fälligkeitsdatum lässt sich direkt über die `date`-Entity in der Geräteansicht oder per Service-Aufruf anpassen.

---

## Entities

Pro konfigurierter Hausarbeit wird ein **Gerät** mit vier Entities angelegt. Der Gerätename entspricht dem Benachrichtigungs-Titel.

### `binary_sensor.<name>_faellig`

Zeigt an, ob die Aufgabe aktuell fällig ist.

| Attribut | Wert |
|---|---|
| Device Class | `problem` |
| Icon | `mdi:alert-circle` |
| `on` | Aufgabe ist fällig |
| `off` | Aufgabe ist nicht fällig |

### `button.<name>_erledigt`

Markiert die Aufgabe als erledigt. Beim Drücken:
1. Alle Benachrichtigungen zu dieser Aufgabe werden gelöscht (mobil + persistente).
2. Duplikat-Prüfung: Falls noch kein Kalendereintrag für heute vorhanden, wird `calendar.create_event` aufgerufen.
3. Fälligkeitsdatum wird auf `heute + Fälligkeitsintervall` gesetzt.
4. Binary Sensor wechselt auf `off`.

### `button.<name>_ueberspringen`

Verschiebt die Fälligkeit ohne Kalendereintrag. Beim Drücken:
1. Alle Benachrichtigungen zu dieser Aufgabe werden gelöscht (mobil + persistente).
2. Fälligkeitsdatum wird auf `heute + Verschieben-Tage` gesetzt.
3. Binary Sensor wechselt auf `off`.

### `sensor.<name>_tage_seit_erledigung`

Gibt an, wie viele Tage seit der letzten Erledigung vergangen sind. Der Wert wird durch Suche nach dem Kalender-Stichwort in den letzten 365 Tagen des konfigurierten Kalenders berechnet. Zeigt `unavailable`, wenn noch kein passender Eintrag existiert.

| Attribut | Wert |
|---|---|
| Einheit | `d` (Tage) |
| Icon | `mdi:calendar-clock` |

### `date.<name>_naechste_faelligkeit`

Zeigt das nächste Fälligkeitsdatum (nur Tag, keine Uhrzeit) und erlaubt die direkte Bearbeitung über die HA-UI oder per Service-Aufruf.

```yaml
action: date.set_value
target:
  entity_id: date.badezimmer_reinigen_naechste_faelligkeit
data:
  date: "2026-06-15"
```

---

## Aktionen

Die Integration registriert zwei HA-Aktionen, aufrufbar über **Entwicklerwerkzeuge → Aktionen** oder in Automatisierungen.

### `hausarbeiten.pruefen`

Prüft für **alle** konfigurierten Hausarbeiten, ob das Fälligkeitsdatum heute oder in der Vergangenheit liegt. Entspricht dem internen Zeitplan-Trigger (01:00 / 14:00 Uhr). Sendet ggf. eine Benachrichtigung und setzt den Binary Sensor auf `on`.

```yaml
action: hausarbeiten.pruefen
```

### `hausarbeiten.benachrichtigen`

Erzwingt eine Benachrichtigung unabhängig vom Fälligkeitsdatum. Setzt das Fälligkeitsdatum auf **heute** und den Binary Sensor auf `on`.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `title` | `string` (optional) | Benachrichtigungs-Titel der Aufgabe. Leer lassen für alle konfigurierten Hausarbeiten. |

```yaml
# Alle Hausarbeiten benachrichtigen
action: hausarbeiten.benachrichtigen

# Nur eine bestimmte Aufgabe
action: hausarbeiten.benachrichtigen
data:
  title: "Badezimmer reinigen"
```

### Mobile-Notification-Aktionen

Der HA Companion App antwortet auf gesendete Benachrichtigungen mit `mobile_app_notification_action`-Events. Diese werden von der Integration automatisch ausgewertet und der richtigen Aufgabe über den konfigurierten **Tag** zugeordnet:

| `action` | Effekt |
|---|---|
| `HAUSARBEITEN_ERLEDIGT` | Identisch mit Button „Erledigt" |
| `HAUSARBEITEN_VERSCHOBEN` | Identisch mit Button „Überspringen" |

---

## Funktionsweise

### Fälligkeitsprüfung (automatisch)

Die Integration prüft täglich um **01:00 Uhr** und **14:00 Uhr**:

```
Fälligkeitsdatum ≤ heute
  → Binary Sensor: off → on
  → Benachrichtigung senden
```

Der Zustand (`due_date`, `is_due`) wird in `.storage/hausarbeiten_<entry_id>` gespeichert und übersteht einen HA-Neustart.

### Erledigung

```
Button "Erledigt" oder Mobile-Action "HAUSARBEITEN_ERLEDIGT"
  │
  ├─ 1. Benachrichtigungs-Skript mit message=clear_notification aufrufen (blocking)
  ├─ 2. persistent_notification.dismiss aufrufen
  ├─ 3. Duplikat-Prüfung im Kalender (nächste 24 h)
  │      Kein Duplikat → calendar.create_event für heute anlegen
  ├─ 4. due_date = heute + Fälligkeitsintervall
  ├─ 5. is_due = False → Binary Sensor: on → off
  └─ 6. Tage-seit-Erledigung aus Kalender aktualisieren
```

### Überspringen

```
Button "Überspringen" oder Mobile-Action "HAUSARBEITEN_VERSCHOBEN"
  │
  ├─ 1. Benachrichtigungs-Skript mit message=clear_notification aufrufen (blocking)
  ├─ 2. persistent_notification.dismiss aufrufen
  ├─ 3. due_date = heute + Verschieben-Tage
  └─ 4. is_due = False → Binary Sensor: on → off
```

### Benachrichtigung erzwingen (`hausarbeiten.benachrichtigen`)

```
Aktion hausarbeiten.benachrichtigen (optional: title)
  │
  ├─ due_date = heute
  ├─ is_due = True → Binary Sensor: off → on
  └─ Benachrichtigung senden
```

---

## Benachrichtigungen

### Senden

Das konfigurierte Skript wird mit folgenden Parametern aufgerufen:

```yaml
notification_channel: "Hausarbeiten"
notification_group: "Hausarbeiten"
notification_tag: "<tag>"
notification_mdi_icon: "mdi:home-automation"
notification_visibility: "private"
notification_alert_once: false
notification_title: "<titel>"
notification_subject: "<kurznachricht>"
notification_message: "<detaillierte nachricht>"
notification_png_icon: null
notification_link: "lovelace-yaml/0#notifications"
notification_actions:
  - action: HAUSARBEITEN_ERLEDIGT
    title: "Erledigt ✅"
  - action: HAUSARBEITEN_VERSCHOBEN
    title: "Verschieben ❌"
```

### Löschen

Beim Erledigen oder Überspringen wird zuerst das Skript mit `notification_message: "clear_notification"` aufgerufen (`blocking=True`), danach `persistent_notification.dismiss`. Die Reihenfolge stellt sicher, dass eine vom Skript erzeugte persistente Benachrichtigung danach ebenfalls entfernt wird.

```yaml
notification_message: "clear_notification"
notification_alert_once: true
notification_actions: []
# alle übrigen Felder werden unverändert mitgegeben
```

Das Skript muss `notification_message` unverändert als `message` an den `notify`-Service weiterleiten, damit der Companion App die Benachrichtigung auf dem Gerät entfernt.

---

## Migration von der Blueprint

### Schritt-für-Schritt

1. Custom Component installieren und HA neu starten.
2. Für jede bestehende Blueprint-Instanz unter **Integrationen → Hausarbeiten** einen neuen Eintrag anlegen und die Werte übernehmen.
3. Das initiale Fälligkeitsdatum über die `date`-Entity setzen (entspricht dem bisherigen `input_datetime`).
4. Blueprint-Automationen deaktivieren und nach einem Testzeitraum löschen.
5. Nicht mehr benötigte `input_boolean`, `input_datetime` und `input_button` Entities entfernen.

### Mapping Blueprint → Integration

| Blueprint-Input | Integration |
|---|---|
| `calendar_summary` | Kalender-Stichwort (Schritt 1) |
| `calendar_entity` | Kalender (Schritt 1) |
| `event_days` | Fälligkeitsintervall (Schritt 1) |
| `skip_days` | Verschieben um Tage (Schritt 1) |
| `input_date` | `date.<name>_naechste_faelligkeit` (automatisch) |
| `input_bool` | `binary_sensor.<name>_faellig` (automatisch) |
| `input_skip` | `button.<name>_ueberspringen` (automatisch) |
| `notification_*` | Benachrichtigungs-Einstellungen (Schritt 2) |
| `HAUSARBEITEN_AUSLÖSER` (Event) | `hausarbeiten.pruefen` (Aktion) |
| `HAUSARBEITEN_AUSLÖSER_FORCE` (Event) | `hausarbeiten.benachrichtigen` (Aktion) |

---

## Fehlerbehebung

### Keine Benachrichtigung erhalten

- Prüfen ob das konfigurierte Skript existiert: **Entwicklerwerkzeuge → Zustände** → nach `script.notification_notify_duplizieren` suchen.
- HA-Log nach `WARNING homeassistant.components.hausarbeiten` durchsuchen.

### Persistente Benachrichtigung zeigt „clear_notification" als Text

- Das Benachrichtigungs-Skript schreibt `notification_message` unverändert als `message` in eine persistente HA-Benachrichtigung, statt sie nur an mobile Geräte weiterzuleiten.
- Das Skript muss `message: clear_notification` erkennen und in diesem Fall `persistent_notification.dismiss` aufrufen statt `persistent_notification.create`.

### Mobile Benachrichtigung wird nicht gelöscht

- Das Skript muss `message: "clear_notification"` unverändert an den `notify`-Service weiterleiten; der Companion App entfernt die Nachricht mit übereinstimmendem Tag.
- HA-Log nach `DEBUG homeassistant.components.hausarbeiten` durchsuchen (Log-Level auf `debug` setzen).

### Fälligkeitsdatum wird nach Neustart nicht wiederhergestellt

- Dateisystem-Berechtigungen für `.storage/` prüfen.
- HA-Log auf Schreibfehler (`async_save`) prüfen.

### Kein Kalendereintrag nach Erledigung

- Prüfen ob die Kalender-Integration Schreibzugriff unterstützt (`calendar.create_event`). Nicht alle Kalender-Integrationen erlauben das Anlegen von Events.
- HA-Log nach `ERROR homeassistant.components.hausarbeiten` durchsuchen.

### `sensor.tage_seit_erledigung` zeigt `unavailable`

- Im konfigurierten Kalender wurde in den letzten 365 Tagen kein Event gefunden, dessen `summary` das Kalender-Stichwort enthält (Teilstring, case-insensitive).
- Nach dem ersten erfolgreichen Erledigen verschwindet `unavailable` automatisch.
