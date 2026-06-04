from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SIGNAL_STATE_CHANGED
from .coordinator import HausarbeitenCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: HausarbeitenCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [HausarbeitTageSensor(coordinator, entry)]

    if "_hub_sensor_entry_id" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["_hub_sensor_entry_id"] = entry.entry_id
        entities.append(HausarbeitenHubSensor(hass, entry))

    async_add_entities(entities)


class HausarbeitTageSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "tage_seit_erledigung"
    _attr_icon = "mdi:calendar-clock"
    _attr_native_unit_of_measurement = "d"

    def __init__(self, coordinator: HausarbeitenCoordinator, entry: ConfigEntry) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_tage_seit_erledigung"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Hausarbeiten",
            model="Hausarbeit",
        )

    @property
    def native_value(self) -> int | None:
        val = self._coordinator.days_since_last
        return val if val >= 0 else None

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._coordinator.async_add_listener(self._handle_update))

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()


class HausarbeitenHubSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "faellige_hausarbeiten"
    _attr_icon = "mdi:checkbox-multiple-marked"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._hass = hass
        self._attr_unique_id = f"{DOMAIN}_hub_faellige"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, DOMAIN)},
            name="Hausarbeiten",
            manufacturer="Hausarbeiten",
            model="Übersicht",
        )

    @property
    def native_value(self) -> int:
        return sum(
            1
            for val in self._hass.data.get(DOMAIN, {}).values()
            if isinstance(val, HausarbeitenCoordinator) and val.is_due
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_STATE_CHANGED, self._handle_update)
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
