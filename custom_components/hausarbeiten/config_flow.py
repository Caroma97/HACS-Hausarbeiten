from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
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
)


def _aufgaben_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema({
        vol.Required(
            CONF_CALENDAR_SUMMARY,
            default=defaults.get(CONF_CALENDAR_SUMMARY, ""),
        ): selector.TextSelector(selector.TextSelectorConfig()),
        vol.Required(
            CONF_CALENDAR_ENTITY,
            default=defaults.get(CONF_CALENDAR_ENTITY, ""),
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="calendar")
        ),
        vol.Optional(
            CONF_EVENT_DAYS,
            default=defaults.get(CONF_EVENT_DAYS, DEFAULT_EVENT_DAYS),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=100, unit_of_measurement="Tage", mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Optional(
            CONF_SKIP_DAYS,
            default=defaults.get(CONF_SKIP_DAYS, DEFAULT_SKIP_DAYS),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=30, unit_of_measurement="Tage", mode=selector.NumberSelectorMode.BOX)
        ),
    })


def _notification_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema({
        vol.Optional(
            CONF_NOTIFICATION_TITLE,
            default=defaults.get(CONF_NOTIFICATION_TITLE, ""),
        ): selector.TextSelector(selector.TextSelectorConfig()),
        vol.Optional(
            CONF_NOTIFICATION_SUBJECT,
            default=defaults.get(CONF_NOTIFICATION_SUBJECT, ""),
        ): selector.TextSelector(selector.TextSelectorConfig()),
        vol.Optional(
            CONF_NOTIFICATION_MESSAGE,
            default=defaults.get(CONF_NOTIFICATION_MESSAGE, ""),
        ): selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
        vol.Optional(
            CONF_NOTIFICATION_CHANNEL,
            default=defaults.get(CONF_NOTIFICATION_CHANNEL, DEFAULT_NOTIFICATION_CHANNEL),
        ): selector.TextSelector(selector.TextSelectorConfig()),
        vol.Optional(
            CONF_NOTIFICATION_GROUP,
            default=defaults.get(CONF_NOTIFICATION_GROUP, DEFAULT_NOTIFICATION_GROUP),
        ): selector.TextSelector(selector.TextSelectorConfig()),
        vol.Optional(
            CONF_NOTIFICATION_TAG,
            default=defaults.get(CONF_NOTIFICATION_TAG, ""),
        ): selector.TextSelector(selector.TextSelectorConfig()),
        vol.Optional(
            CONF_NOTIFICATION_MDI_ICON,
            default=defaults.get(CONF_NOTIFICATION_MDI_ICON, DEFAULT_NOTIFICATION_MDI_ICON),
        ): selector.IconSelector(),
        vol.Optional(
            CONF_NOTIFICATION_VISIBILITY,
            default=defaults.get(CONF_NOTIFICATION_VISIBILITY, DEFAULT_NOTIFICATION_VISIBILITY),
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    selector.SelectOptionDict(value="public", label="Öffentlich"),
                    selector.SelectOptionDict(value="private", label="Privat"),
                    selector.SelectOptionDict(value="secret", label="Secret"),
                ]
            )
        ),
        vol.Optional(
            CONF_NOTIFICATION_ALERT_ONCE,
            default=defaults.get(CONF_NOTIFICATION_ALERT_ONCE, DEFAULT_NOTIFICATION_ALERT_ONCE),
        ): selector.BooleanSelector(),
        vol.Optional(
            CONF_NOTIFICATION_PNG_ICON,
            default=defaults.get(CONF_NOTIFICATION_PNG_ICON, ""),
        ): selector.TextSelector(selector.TextSelectorConfig()),
        vol.Optional(
            CONF_NOTIFICATION_LINK,
            default=defaults.get(CONF_NOTIFICATION_LINK, DEFAULT_NOTIFICATION_LINK),
        ): selector.TextSelector(selector.TextSelectorConfig()),
        vol.Optional(
            CONF_NOTIFICATION_SCRIPT,
            default=defaults.get(CONF_NOTIFICATION_SCRIPT, DEFAULT_NOTIFICATION_SCRIPT),
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="script")
        ),
    })


class HausarbeitenConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_notification()
        return self.async_show_form(
            step_id="user",
            data_schema=_aufgaben_schema({}),
        )

    async def async_step_notification(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            tag = user_input.get(CONF_NOTIFICATION_TAG) or self._data[CONF_CALENDAR_SUMMARY]
            for entry in self.hass.config_entries.async_entries(DOMAIN):
                entry_tag = {**entry.data, **entry.options}.get(CONF_NOTIFICATION_TAG) or entry.data.get(CONF_CALENDAR_SUMMARY, "")
                if entry_tag == tag:
                    errors[CONF_NOTIFICATION_TAG] = "tag_not_unique"
                    break
            if not errors:
                if not user_input.get(CONF_NOTIFICATION_TAG):
                    user_input[CONF_NOTIFICATION_TAG] = self._data[CONF_CALENDAR_SUMMARY]
                if not user_input.get(CONF_NOTIFICATION_TITLE):
                    user_input[CONF_NOTIFICATION_TITLE] = self._data[CONF_CALENDAR_SUMMARY]
                self._data.update(user_input)
                title = self._data.get(CONF_NOTIFICATION_TITLE) or self._data[CONF_CALENDAR_SUMMARY]
                return self.async_create_entry(title=title, data=self._data)

        return self.async_show_form(
            step_id="notification",
            data_schema=_notification_schema({
                CONF_NOTIFICATION_TITLE: self._data.get(CONF_CALENDAR_SUMMARY, ""),
                CONF_NOTIFICATION_TAG: self._data.get(CONF_CALENDAR_SUMMARY, ""),
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return HausarbeitenOptionsFlow(config_entry)


class HausarbeitenOptionsFlow(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry
        self._data: dict[str, Any] = {}

    def _current(self) -> dict[str, Any]:
        return {**self._config_entry.data, **self._config_entry.options}

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_notification()
        return self.async_show_form(
            step_id="init",
            data_schema=_aufgaben_schema(self._current()),
        )

    async def async_step_notification(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            tag = user_input.get(CONF_NOTIFICATION_TAG) or self._current().get(CONF_CALENDAR_SUMMARY, "")
            for entry in self.hass.config_entries.async_entries(DOMAIN):
                if entry.entry_id == self._config_entry.entry_id:
                    continue
                entry_tag = {**entry.data, **entry.options}.get(CONF_NOTIFICATION_TAG) or entry.data.get(CONF_CALENDAR_SUMMARY, "")
                if entry_tag == tag:
                    errors[CONF_NOTIFICATION_TAG] = "tag_not_unique"
                    break
            if not errors:
                self._data.update(user_input)
                current = self._current()
                new_title = self._data.get(CONF_NOTIFICATION_TITLE) or current.get(CONF_CALENDAR_SUMMARY, "")
                self.hass.config_entries.async_update_entry(self._config_entry, title=new_title)
                return self.async_create_entry(data=self._data)
        return self.async_show_form(
            step_id="notification",
            data_schema=_notification_schema({**self._current(), **self._data}),
            errors=errors,
        )
