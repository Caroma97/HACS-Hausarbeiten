from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    SERVICE_BENACHRICHTIGEN,
    SERVICE_FIELD_TITLE,
    SERVICE_PRUEFEN,
)
from .coordinator import HausarbeitenCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.SENSOR,
    Platform.DATE,
]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    async def handle_pruefen(call: ServiceCall) -> None:
        title: str | None = call.data.get(SERVICE_FIELD_TITLE)
        for coordinator in hass.data.get(DOMAIN, {}).values():
            if not isinstance(coordinator, HausarbeitenCoordinator):
                continue
            if title is None or coordinator.notification_title == title:
                await coordinator.async_pruefen()

    async def handle_benachrichtigen(call: ServiceCall) -> None:
        title: str | None = call.data.get(SERVICE_FIELD_TITLE)
        for coordinator in hass.data.get(DOMAIN, {}).values():
            if not isinstance(coordinator, HausarbeitenCoordinator):
                continue
            if title is None or coordinator.notification_title == title:
                await coordinator.async_benachrichtigen()

    hass.services.async_register(
        DOMAIN,
        SERVICE_PRUEFEN,
        handle_pruefen,
        schema=vol.Schema({vol.Optional(SERVICE_FIELD_TITLE): cv.string}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_BENACHRICHTIGEN,
        handle_benachrichtigen,
        schema=vol.Schema({vol.Optional(SERVICE_FIELD_TITLE): cv.string}),
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = HausarbeitenCoordinator(hass, entry)
    await coordinator.async_setup()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(coordinator.async_config_updated))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator: HausarbeitenCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_teardown()
        domain_data = hass.data[DOMAIN]
        if domain_data.get("_hub_sensor_entry_id") == entry.entry_id:
            domain_data.pop("_hub_sensor_entry_id", None)
        if domain_data.get("_hub_button_entry_id") == entry.entry_id:
            domain_data.pop("_hub_button_entry_id", None)
    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    _LOGGER.debug(
        "Migrating %s config entry from version %s.%s",
        DOMAIN,
        config_entry.version,
        config_entry.minor_version,
    )
    if config_entry.version > 1:
        return False
    return True
