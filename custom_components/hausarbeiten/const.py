from __future__ import annotations

DOMAIN = "hausarbeiten"

CONF_CALENDAR_ENTITY = "calendar_entity"
CONF_CALENDAR_SUMMARY = "calendar_summary"
CONF_EVENT_DAYS = "event_days"
CONF_SKIP_DAYS = "skip_days"
CONF_NOTIFICATION_TITLE = "notification_title"
CONF_NOTIFICATION_SUBJECT = "notification_subject"
CONF_NOTIFICATION_MESSAGE = "notification_message"
CONF_NOTIFICATION_CHANNEL = "notification_channel"
CONF_NOTIFICATION_GROUP = "notification_group"
CONF_NOTIFICATION_TAG = "notification_tag"
CONF_NOTIFICATION_MDI_ICON = "notification_mdi_icon"
CONF_NOTIFICATION_VISIBILITY = "notification_visibility"
CONF_NOTIFICATION_ALERT_ONCE = "notification_alert_once"
CONF_NOTIFICATION_PNG_ICON = "notification_png_icon"
CONF_NOTIFICATION_LINK = "notification_link"
CONF_NOTIFICATION_SCRIPT = "notification_script"

DEFAULT_EVENT_DAYS = 3
DEFAULT_SKIP_DAYS = 2
DEFAULT_NOTIFICATION_CHANNEL = "Hausarbeiten"
DEFAULT_NOTIFICATION_GROUP = "Hausarbeiten"
DEFAULT_NOTIFICATION_MDI_ICON = "mdi:home-automation"
DEFAULT_NOTIFICATION_VISIBILITY = "private"
DEFAULT_NOTIFICATION_ALERT_ONCE = False
DEFAULT_NOTIFICATION_LINK = "lovelace-yaml/0#notifications"
DEFAULT_NOTIFICATION_SCRIPT = "script.notification_notify_duplizieren"

STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = f"{DOMAIN}_"

EVENT_ACTION_DONE = "HAUSARBEITEN_ERLEDIGT"
EVENT_ACTION_SKIP = "HAUSARBEITEN_VERSCHOBEN"

SERVICE_PRUEFEN = "pruefen"
SERVICE_BENACHRICHTIGEN = "benachrichtigen"
SERVICE_FIELD_TITLE = "title"

CHECK_TIMES = [
    {"hour": 1, "minute": 0, "second": 0},
    {"hour": 14, "minute": 0, "second": 0},
]

SIGNAL_STATE_CHANGED = f"{DOMAIN}_state_changed"

CONF_ENTRY_TYPE = "entry_type"
ENTRY_TYPE_HUB = "hub"
