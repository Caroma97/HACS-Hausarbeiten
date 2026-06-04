from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import SOURCE_SYSTEM, ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_ENTRY_TYPE,
    DOMAIN,
    ENTRY_TYPE_HUB,
    SERVICE_BENACHRICHTIGEN,
    SERVICE_FIELD_TITLE,
    SERVICE_PRUEFEN,
)
from .coordinator import HausarbeitenCoordinator

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.SENSOR,
    Platform.DATE,
]

_HUB_PLATFORMS: list[Platform] = [Platform.BUTTON, Platform.SENSOR]


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
    hass.data.setdefault(DOMAIN, {})

    if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_HUB:
        await hass.config_entries.async_forward_entry_setups(entry, _HUB_PLATFORMS)
        return True

    coordinator = HausarbeitenCoordinator(hass, entry)
    await coordinator.async_setup()
    hass.data[DOMAIN][entry.entry_id] = coordinator

    hub_exists = any(
        e.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_HUB
        for e in hass.config_entries.async_entries(DOMAIN)
    )
    if not hub_exists and "_hub_creating" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["_hub_creating"] = True
        hass.async_create_task(
            hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_SYSTEM})
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(coordinator.async_config_updated))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_HUB:
        if await hass.config_entries.async_unload_platforms(entry, _HUB_PLATFORMS):
            hass.data[DOMAIN].pop("_hub_creating", None)
            return True
        return False

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator: HausarbeitenCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_teardown()

        remaining_tasks = [
            e for e in hass.config_entries.async_entries(DOMAIN)
            if e.data.get(CONF_ENTRY_TYPE) != ENTRY_TYPE_HUB and e.entry_id != entry.entry_id
        ]
        if not remaining_tasks:
            for hub_entry in hass.config_entries.async_entries(DOMAIN):
                if hub_entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_HUB:
                    hass.async_create_task(hass.config_entries.async_remove(hub_entry.entry_id))

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
