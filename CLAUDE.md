# Custom Component: hausarbeiten

Wiederkehrende Hausarbeiten tracken, Benachrichtigungen senden und Erledigungen im Kalender protokollieren. Veröffentlicht als HACS Custom Integration.

---

## Repository-Struktur

```
.github/workflows/
  hassfest.yaml          CI: HA-Integration validieren (Manifest, Imports, Struktur)
  hacs.yaml              CI: HACS-Anforderungen prüfen

custom_components/hausarbeiten/
  __init__.py            Services registrieren + Platforms laden
  coordinator.py         Kern-Logik (kein DataUpdateCoordinator – eigenes Listener-Muster)
  config_flow.py         2-Schritte-Flow: Aufgabe → Benachrichtigung (+ OptionsFlow)
  const.py               Alle Konstanten (CONF_*, DEFAULT_*, SERVICE_*, EVENT_*)
  binary_sensor.py       is_due → BinarySensor (device_class: problem)
  sensor.py              days_since_last → Sensor (d)
  date.py                due_date → DateEntity (editierbar)
  datetime.py            due_date → DateTimeEntity – NICHT in PLATFORMS, derzeit inaktiv
  button.py              Erledigt + Überspringen → ButtonEntities
  manifest.json          Domain, Version, Abhängigkeiten, codeowners, documentation
  strings.json           Übersetzungs-Template (Deutsch) – Quelle für translations/
  services.yaml          Service-Beschreibungen
  translations/
    de.json              Deutsches Sprachpaket (immer synchron mit strings.json halten)

hacs.json                HACS-Konfiguration (Name, min. HA-Version)
info.md                  Kurztext für HACS-UI-Vorschau
CHANGELOG.md             Release-Verlauf (HACS liest daraus Release-Notes)
LICENSE                  MIT-Lizenz
README.md                Vollständige Dokumentation
```

---

## Coordinator-Muster

`HausarbeitenCoordinator` ist **kein** `DataUpdateCoordinator`. Stattdessen:

```python
# Listener registrieren (in async_added_to_hass jeder Entity)
self.async_on_remove(self._coordinator.async_add_listener(self._handle_update))

# State pushen (im Coordinator nach Zustandsänderung)
self._notify_listeners()  # ruft alle registrierten Callbacks auf
```

State-Persistenz via `homeassistant.helpers.storage.Store` (JSON, key: `hausarbeiten_<entry_id>`).

---

## Zustandsmodell

| Attribut | Typ | Bedeutung |
|---|---|---|
| `due_date` | `date` | Nächstes Fälligkeitsdatum |
| `is_due` | `bool` | Aufgabe aktuell fällig |
| `days_since_last` | `int` | Tage seit letzter Erledigung (-1 = nie) |

Statusübergänge:
- **Fällig prüfen** (`_check_due`): `due_date <= today` → `is_due=True` → Benachrichtigung senden
- **Erledigen** (`async_mark_done`): Kalendereintrag erstellen → `due_date = today + event_days` → `is_due=False`
- **Überspringen** (`async_skip`): `due_date = today + skip_days` → `is_due=False`
- **Erzwingen** (`_force_notify`): `due_date = today` → `is_due=True` → Benachrichtigung senden

Automatische Prüfung täglich um **01:00** und **14:00** (`CHECK_TIMES` in `const.py`).

---

## Benachrichtigungen

Alle Benachrichtigungen laufen über ein externes Skript (`notification_script`, default: `script.notification_notify_duplizieren`). Das Skript erhält Felder wie `notification_tag`, `notification_channel`, `notification_message` usw.

Notification-Actions auf dem Smartphone lösen `mobile_app_notification_action`-Events aus:
- `HAUSARBEITEN_ERLEDIGT` → `async_mark_done()`
- `HAUSARBEITEN_VERSCHOBEN` → `async_skip()`

Benachrichtigungen löschen: selbes Skript aufrufen mit `notification_message: "clear_notification"`.

---

## Neue Entity hinzufügen

1. Neue Datei `custom_components/hausarbeiten/<platform>.py` anlegen (analog `sensor.py`)
2. `async_setup_entry` implementiert, liest `hass.data[DOMAIN][entry.entry_id]`
3. `async_added_to_hass` registriert Listener beim Coordinator
4. `Platform.<NAME>` in `PLATFORMS`-Liste in `__init__.py` eintragen
5. Falls `_attr_translation_key` gesetzt: Schlüssel unter `entity.<platform>.<key>.name` in **beiden** Dateien ergänzen:
   - `custom_components/hausarbeiten/strings.json`
   - `custom_components/hausarbeiten/translations/de.json`

---

## Neue Config-Option hinzufügen

1. Konstante in `const.py` (`CONF_*` + ggf. `DEFAULT_*`)
2. Selector in `config_flow.py` (in `_aufgaben_schema` oder `_notification_schema`)
3. Attribut in `coordinator._update_config()` setzen
4. Label in **beiden** Übersetzungsdateien unter `config.step.<step>.data` und `options.step.<step>.data`:
   - `custom_components/hausarbeiten/strings.json`
   - `custom_components/hausarbeiten/translations/de.json`

---

## Übersetzungen

`strings.json` ist das Template – es definiert alle Schlüssel. `translations/de.json` enthält die aktiven deutschen Texte und muss **immer identischen Inhalt** haben.

Struktur der Übersetzungsdateien:

```
title                          Integrationsname in der HA-UI
config.step.<step>.data.*      Config-Flow-Feldlabels
config.step.<step>.data_description.*   Hilfstexte unter Feldern
options.step.<step>.data.*     Options-Flow-Feldlabels
entity.<platform>.<key>.name   Entity-Name (wenn _attr_translation_key gesetzt)
```

---

## Releases & Versionierung

Versionsnummer liegt in `custom_components/hausarbeiten/manifest.json` → `version`.
HACS erkennt neue Releases über **Git Tags** (`v1.0.0`, `v1.1.0`, …).

Ablauf für ein neues Release:
1. `manifest.json` → `version` erhöhen (Semantic Versioning: MAJOR.MINOR.PATCH)
2. `CHANGELOG.md` um den neuen Abschnitt `## [X.Y.Z] - YYYY-MM-DD` erweitern
3. Commit + Tag `vX.Y.Z` auf GitHub pushen → HACS zeigt das Update automatisch an

---

## Bekannte Besonderheiten

- `datetime.py` ist **nicht in PLATFORMS** – falls aktiviert, kollidiert `unique_id`-Suffix `_naechste_faelligkeit` mit `date.py`. Eines von beiden muss umbenannt werden.
- Kalender-Duplikat-Prüfung in `async_mark_done` schaut nur das aktuelle 24-h-Fenster an.
- `days_since_last` schaut 365 Tage zurück; bei mehr als einem Treffer wird das neueste verwendet.
- `notification_tag` fällt auf `calendar_summary` zurück, wenn leer (Config Flow + `_update_config`).

---

## Nützliche Befehle

```bash
# HA-Config-Syntax prüfen
hass --script check_config -c /config

# YAML-Lint
yamllint custom_components/hausarbeiten/services.yaml

# JSON-Syntax prüfen
python3 -m json.tool custom_components/hausarbeiten/manifest.json
python3 -m json.tool custom_components/hausarbeiten/strings.json
python3 -m json.tool custom_components/hausarbeiten/translations/de.json
```

---

## Coding-Konventionen

- `from __future__ import annotations` in jeder Datei
- Rückgabetyp in Config/Options-Flow-Methoden: `ConfigFlowResult` (aus `homeassistant.config_entries`) – nicht das deprecated `FlowResult` aus `data_entry_flow`
- Typen für alle öffentlichen Methoden und Properties
- Async-Methoden für alle HA-Service-Calls (`blocking=True` wenn Rückgabe benötigt)
- `@callback` für synchrone Event-Handler
- Logging: `_LOGGER.warning` für erwartbare Fehler, `_LOGGER.debug` für Diagnose
- Entity-Namen über `_attr_translation_key` + Eintrag in `strings.json`/`translations/de.json` statt hartkodiertem `_attr_name` (bei zukünftigen Entities)
