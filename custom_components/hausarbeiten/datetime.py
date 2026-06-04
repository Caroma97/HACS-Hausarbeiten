from __future__ import annotations

from datetime import date, datetime

from homeassistant.components.datetime import DateTimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import HausarbeitenCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: HausarbeitenCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HausarbeitFaelligkeitEntity(coordinator, entry)])


class HausarbeitFaelligkeitEntity(DateTimeEntity):
    _attr_has_entity_name = True
    _attr_name = "Nächste Fälligkeit"
    _attr_icon = "mdi:calendar-check"

    def __init__(self, coordinator: HausarbeitenCoordinator, entry: ConfigEntry) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_naechste_faelligkeit"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Hausarbeiten",
            model="Hausarbeit",
        )

    @property
    def native_value(self) -> datetime:
        return datetime.combine(
            self._coordinator.due_date,
            datetime.min.time(),
        ).replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)

    async def async_set_value(self, value: datetime) -> None:
        await self._coordinator.async_set_due_date(value.date())

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._coordinator.async_add_listener(self._handle_update))

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
