from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ENTRY_TYPE, DOMAIN, ENTRY_TYPE_HUB, SERVICE_BENACHRICHTIGEN, SERVICE_PRUEFEN
from .coordinator import HausarbeitenCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_HUB:
        async_add_entities([
            HausarbeitenHubPruefenButton(entry),
            HausarbeitenHubBenachrichtigenButton(entry),
        ])
        return

    coordinator: HausarbeitenCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        HausarbeitErledigtButton(coordinator, entry),
        HausarbeitUeberspringenButton(coordinator, entry),
    ])


class _HausarbeitButton(ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: HausarbeitenCoordinator, entry: ConfigEntry) -> None:
        self._coordinator = coordinator
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Hausarbeiten",
            model="Hausarbeit",
        )


class HausarbeitErledigtButton(_HausarbeitButton):
    _attr_translation_key = "erledigt"
    _attr_icon = "mdi:check-circle"

    def __init__(self, coordinator: HausarbeitenCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_erledigt"

    async def async_press(self) -> None:
        await self._coordinator.async_mark_done()


class HausarbeitUeberspringenButton(_HausarbeitButton):
    _attr_translation_key = "ueberspringen"
    _attr_icon = "mdi:skip-next-circle"

    def __init__(self, coordinator: HausarbeitenCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_ueberspringen"

    async def async_press(self) -> None:
        await self._coordinator.async_skip()


_HUB_DEVICE = DeviceInfo(
    identifiers={(DOMAIN, DOMAIN)},
    name="Hausarbeiten",
    manufacturer="Hausarbeiten",
    model="Übersicht",
)


class HausarbeitenHubPruefenButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "alle_pruefen"
    _attr_icon = "mdi:refresh-circle"

    def __init__(self, entry: ConfigEntry) -> None:
        self._attr_unique_id = f"{DOMAIN}_hub_pruefen"
        self._attr_device_info = _HUB_DEVICE

    async def async_press(self) -> None:
        await self.hass.services.async_call(DOMAIN, SERVICE_PRUEFEN, {})


class HausarbeitenHubBenachrichtigenButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "alle_benachrichtigen"
    _attr_icon = "mdi:bell-ring"

    def __init__(self, entry: ConfigEntry) -> None:
        self._attr_unique_id = f"{DOMAIN}_hub_benachrichtigen"
        self._attr_device_info = _HUB_DEVICE

    async def async_press(self) -> None:
        await self.hass.services.async_call(DOMAIN, SERVICE_BENACHRICHTIGEN, {})
