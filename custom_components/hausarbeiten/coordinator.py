from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CHECK_TIMES,
    CONF_CALENDAR_ENTITY,
    CONF_CALENDAR_SUMMARY,
    CONF_EVENT_DAYS,
    CONF_NOTIFICATION_ALERT_ONCE,
    CONF_NOTIFICATION_CHANNEL,
    CONF_NOTIFICATION_GROUP,
    CONF_NOTIFICATION_LINK,
    CONF_NOTIFICATION_MDI_ICON,
    CONF_NOTIFICATION_MESSAGE,
    CONF_NOTIFICATION_PNG_ICON,
    CONF_NOTIFICATION_SCRIPT,
    CONF_NOTIFICATION_SUBJECT,
    CONF_NOTIFICATION_TAG,
    CONF_NOTIFICATION_TITLE,
    CONF_NOTIFICATION_VISIBILITY,
    CONF_SKIP_DAYS,
    DEFAULT_EVENT_DAYS,
    DEFAULT_NOTIFICATION_ALERT_ONCE,
    DEFAULT_NOTIFICATION_CHANNEL,
    DEFAULT_NOTIFICATION_GROUP,
    DEFAULT_NOTIFICATION_LINK,
    DEFAULT_NOTIFICATION_MDI_ICON,
    DEFAULT_NOTIFICATION_SCRIPT,
    DEFAULT_NOTIFICATION_VISIBILITY,
    DEFAULT_SKIP_DAYS,
    DOMAIN,
    EVENT_ACTION_DONE,
    EVENT_ACTION_SKIP,
    SIGNAL_STATE_CHANGED,
    STORAGE_KEY_PREFIX,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)


class HausarbeitenCoordinator:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY_PREFIX}{entry.entry_id}")
        self._unsubs: list[Any] = []
        self._listeners: list[Callable[[], None]] = []

        self.is_due: bool = False
        self.days_since_last: int = -1
        self._update_config()
        self.due_date: date = date.today() + timedelta(days=self.event_days)

    def _update_config(self) -> None:
        data = {**self.entry.data, **self.entry.options}
        self.calendar_entity: str = data[CONF_CALENDAR_ENTITY]
        self.calendar_summary: str = data[CONF_CALENDAR_SUMMARY]
        self.event_days: int = int(data.get(CONF_EVENT_DAYS, DEFAULT_EVENT_DAYS))
        self.skip_days: int = int(data.get(CONF_SKIP_DAYS, DEFAULT_SKIP_DAYS))
        self.notification_title: str = data.get(CONF_NOTIFICATION_TITLE) or self.calendar_summary
        self.notification_subject: str = data.get(CONF_NOTIFICATION_SUBJECT, "")
        self.notification_message: str = data.get(CONF_NOTIFICATION_MESSAGE, "")
        self.notification_channel: str = data.get(CONF_NOTIFICATION_CHANNEL, DEFAULT_NOTIFICATION_CHANNEL)
        self.notification_group: str = data.get(CONF_NOTIFICATION_GROUP, DEFAULT_NOTIFICATION_GROUP)
        self.notification_tag: str = data.get(CONF_NOTIFICATION_TAG) or self.calendar_summary
        self.notification_mdi_icon: str = data.get(CONF_NOTIFICATION_MDI_ICON, DEFAULT_NOTIFICATION_MDI_ICON)
        self.notification_visibility: str = data.get(CONF_NOTIFICATION_VISIBILITY, DEFAULT_NOTIFICATION_VISIBILITY)
        self.notification_alert_once: bool = data.get(CONF_NOTIFICATION_ALERT_ONCE, DEFAULT_NOTIFICATION_ALERT_ONCE)
        self.notification_png_icon: str = data.get(CONF_NOTIFICATION_PNG_ICON) or ""
        self.notification_link: str = data.get(CONF_NOTIFICATION_LINK, DEFAULT_NOTIFICATION_LINK)
        self.notification_script: str = data.get(CONF_NOTIFICATION_SCRIPT, DEFAULT_NOTIFICATION_SCRIPT)

    async def async_setup(self) -> None:
        stored = await self._store.async_load()
        if stored:
            try:
                self.due_date = date.fromisoformat(stored["due_date"])
                self.is_due = stored.get("is_due", False)
            except (KeyError, ValueError):
                pass

        for t in CHECK_TIMES:
            self._unsubs.append(
                async_track_time_change(
                    self.hass,
                    self._handle_time_trigger,
                    hour=t["hour"],
                    minute=t["minute"],
                    second=t["second"],
                )
            )

        self._unsubs.append(
            self.hass.bus.async_listen("mobile_app_notification_action", self._handle_notification_action)
        )

        self.hass.async_create_task(self._update_days_since_last())

    async def async_teardown(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()

    async def async_config_updated(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self._update_config()

    @callback
    def async_add_listener(self, update_callback: Any) -> Any:
        @callback
        def remove_listener() -> None:
            self._listeners.remove(update_callback)

        self._listeners.append(update_callback)
        return remove_listener

    def _notify_listeners(self) -> None:
        for listener in self._listeners:
            listener()
        async_dispatcher_send(self.hass, SIGNAL_STATE_CHANGED)

    async def _save_state(self) -> None:
        await self._store.async_save({"due_date": self.due_date.isoformat(), "is_due": self.is_due})

    @callback
    def _handle_time_trigger(self, now: datetime) -> None:
        self.hass.async_create_task(self._check_due())

    @callback
    def _handle_notification_action(self, event: Any) -> None:
        if event.data.get("tag") != self.notification_tag:
            return
        action = event.data.get("action")
        if action == EVENT_ACTION_DONE:
            self.hass.async_create_task(self.async_mark_done())
        elif action == EVENT_ACTION_SKIP:
            self.hass.async_create_task(self.async_skip())

    async def async_pruefen(self) -> None:
        """Öffentliche Aktion: Fälligkeit prüfen und ggf. benachrichtigen."""
        await self._check_due()

    async def async_benachrichtigen(self) -> None:
        """Öffentliche Aktion: Benachrichtigung unabhängig vom Fälligkeitsdatum erzwingen."""
        await self._force_notify()

    async def _check_due(self) -> None:
        if self.due_date <= date.today():
            self.is_due = True
            await self._save_state()
            await self._send_notification()
        await self._update_days_since_last()

    async def _force_notify(self) -> None:
        self.due_date = date.today()
        self.is_due = True
        await self._save_state()
        self._notify_listeners()
        await self._send_notification()

    async def _send_notification(self) -> None:
        parts = self.notification_script.split(".", 1)
        if len(parts) != 2:
            _LOGGER.warning("Invalid notification_script: %s", self.notification_script)
            return
        domain, service = parts
        try:
            await self.hass.services.async_call(
                domain,
                service,
                {
                    "notification_channel": self.notification_channel,
                    "notification_group": self.notification_group,
                    "notification_tag": self.notification_tag,
                    "notification_mdi_icon": self.notification_mdi_icon,
                    "notification_visibility": self.notification_visibility,
                    "notification_alert_once": self.notification_alert_once,
                    "notification_title": self.notification_title,
                    "notification_subject": self.notification_subject,
                    "notification_message": self.notification_message,
                    "notification_png_icon": self.notification_png_icon,
                    "notification_link": self.notification_link,
                    "notification_actions": [
                        {"action": EVENT_ACTION_DONE, "title": "Erledigt ✅"},
                        {"action": EVENT_ACTION_SKIP, "title": "Verschieben ❌"},
                    ],
                },
                blocking=False,
            )
        except Exception as err:
            _LOGGER.warning("Notification konnte nicht gesendet werden: %s", err)

    async def async_mark_done(self) -> None:
        today = date.today()

        await self._clear_notifications()

        # Duplikat-Prüfung: kein zweiter Kalendereintrag für heute
        already_logged = False
        try:
            result = await self.hass.services.async_call(
                "calendar",
                "get_events",
                {
                    "start_date_time": today.strftime("%Y-%m-%dT00:00:00"),
                    "end_date_time": today.strftime("%Y-%m-%dT23:59:59"),
                },
                target={"entity_id": self.calendar_entity},
                blocking=True,
                return_response=True,
            )
            events = (result or {}).get(self.calendar_entity, {}).get("events", [])
            already_logged = any(
                self.calendar_summary.lower() in e.get("summary", "").lower() for e in events
            )
        except Exception as err:
            _LOGGER.warning("Kalender-Duplikat-Prüfung fehlgeschlagen: %s", err)

        if not already_logged:
            try:
                await self.hass.services.async_call(
                    "calendar",
                    "create_event",
                    {
                        "summary": self.calendar_summary,
                        "start_date": today.isoformat(),
                        "end_date": (today + timedelta(days=1)).isoformat(),
                    },
                    target={"entity_id": self.calendar_entity},
                    blocking=True,
                )
            except Exception as err:
                _LOGGER.error("Kalendereintrag konnte nicht erstellt werden: %s", err)

        self.due_date = today + timedelta(days=self.event_days)
        self.is_due = False
        await self._save_state()
        await self._update_days_since_last()

    async def async_skip(self) -> None:
        await self._clear_notifications()
        self.due_date = date.today() + timedelta(days=self.skip_days)
        self.is_due = False
        await self._save_state()
        self._notify_listeners()

    async def async_set_due_date(self, new_date: date) -> None:
        self.due_date = new_date
        await self._save_state()
        self._notify_listeners()

    async def _clear_notifications(self) -> None:
        """Persistente und mobile Benachrichtigungen dieser Aufgabe löschen."""
        parts = self.notification_script.split(".", 1)
        if len(parts) == 2:
            domain, service = parts
            try:
                # blocking=True, damit das Skript vollständig abgeschlossen ist,
                # bevor die persistente Benachrichtigung danach gedismisst wird.
                await self.hass.services.async_call(
                    domain,
                    service,
                    {
                        "notification_tag": self.notification_tag,
                        "notification_channel": self.notification_channel,
                        "notification_group": self.notification_group,
                        "notification_title": self.notification_title,
                        "notification_subject": "",
                        "notification_message": "clear_notification",
                        "notification_mdi_icon": self.notification_mdi_icon,
                        "notification_visibility": self.notification_visibility,
                        "notification_alert_once": True,
                        "notification_png_icon": self.notification_png_icon,
                        "notification_link": self.notification_link,
                        "notification_actions": [],
                    },
                    blocking=True,
                )
            except Exception as err:
                _LOGGER.debug("Mobile-Benachrichtigung konnte nicht gelöscht werden: %s", err)

        try:
            await self.hass.services.async_call(
                "persistent_notification",
                "dismiss",
                {"notification_id": self.calendar_summary},
                blocking=False,
            )
        except Exception:
            pass

    async def _update_days_since_last(self) -> None:
        try:
            now = dt_util.now()
            result = await self.hass.services.async_call(
                "calendar",
                "get_events",
                {
                    "start_date_time": (now - timedelta(days=365)).strftime("%Y-%m-%dT00:00:00"),
                    "end_date_time": now.strftime("%Y-%m-%dT23:59:59"),
                },
                target={"entity_id": self.calendar_entity},
                blocking=True,
                return_response=True,
            )
            events = (result or {}).get(self.calendar_entity, {}).get("events", [])
            matching = sorted(
                [e for e in events if self.calendar_summary.lower() in e.get("summary", "").lower()],
                key=lambda e: e.get("start", ""),
                reverse=True,
            )
            if matching:
                last_date = date.fromisoformat(matching[0]["start"][:10])
                self.days_since_last = (date.today() - last_date).days
            else:
                self.days_since_last = -1
        except Exception as err:
            _LOGGER.debug("Kalenderhistorie konnte nicht abgerufen werden: %s", err)

        self._notify_listeners()
