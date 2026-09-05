"""Sensor platform for Olimpia Splendid UNICO."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DP_CURRENT_TEMP, DP_DIAG_101, DP_DIAG_102, DP_DIAG_103, DP_DIAG_104, DP_DIAG_105, DP_DIAG_107, DP_DIAG_110, DP_DIAG_111, DP_DIAG_115, DP_DIAG_117, DP_ERROR, DP_TEMP_UNIT
from .coordinator import UnicoCoordinator
from .entity import UnicoEntity

PARALLEL_UPDATES = 0
ValueFn = Callable[[Any], Any]


def _identity(value: Any) -> Any:
    return value


def _as_float(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def _as_int(value: Any) -> int | None:
    return int(value) if isinstance(value, (int, float)) else None


@dataclass(frozen=True)
class UnicoSensorDescription:
    key: str
    name: str
    dp: int
    value_fn: ValueFn = _identity
    native_unit: str | None = None
    icon: str | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None
    entity_category: EntityCategory | None = None


SENSORS = (
    UnicoSensorDescription("current_temperature", "Raumtemperatur", DP_CURRENT_TEMP, _as_float, UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
    UnicoSensorDescription("temperature_unit", "Temperatureinheit", DP_TEMP_UNIT, lambda value: str(value).upper() if value is not None else None, icon="mdi:thermometer-lines", entity_category=EntityCategory.DIAGNOSTIC),
    UnicoSensorDescription("error_code", "Fehlercode", DP_ERROR, _as_int, icon="mdi:alert-circle-outline", entity_category=EntityCategory.DIAGNOSTIC),
    UnicoSensorDescription("dp_101", "Außen-/Ansauglufttemperatur (DP101, unsicher)", DP_DIAG_101, _as_float, UnitOfTemperature.CELSIUS, "mdi:thermometer", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, EntityCategory.DIAGNOSTIC),
    UnicoSensorDescription("dp_102", "Innenwärmetauschertemperatur (DP102)", DP_DIAG_102, _as_float, UnitOfTemperature.CELSIUS, "mdi:thermometer", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, EntityCategory.DIAGNOSTIC),
    UnicoSensorDescription("dp_103", "Außenwärmetauschertemperatur (DP103)", DP_DIAG_103, _as_float, UnitOfTemperature.CELSIUS, "mdi:thermometer", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, EntityCategory.DIAGNOSTIC),
    UnicoSensorDescription("dp_104", "Kompressor-/Heißgastemperatur (DP104, unsicher)", DP_DIAG_104, _as_float, UnitOfTemperature.CELSIUS, "mdi:thermometer-high", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, EntityCategory.DIAGNOSTIC),
    UnicoSensorDescription("dp_105", "Kompressorfrequenz (DP105)", DP_DIAG_105, _as_float, "Hz", "mdi:sine-wave", state_class=SensorStateClass.MEASUREMENT, entity_category=EntityCategory.DIAGNOSTIC),
    UnicoSensorDescription("dp_107", "Expansionsventil-Position (DP107, unsicher)", DP_DIAG_107, _as_int, "steps", "mdi:valve", state_class=SensorStateClass.MEASUREMENT, entity_category=EntityCategory.DIAGNOSTIC),
    UnicoSensorDescription("dp_110", "Innenlüfterdrehzahl (DP110)", DP_DIAG_110, _as_int, "rpm", "mdi:fan", state_class=SensorStateClass.MEASUREMENT, entity_category=EntityCategory.DIAGNOSTIC),
    UnicoSensorDescription("dp_111", "Außenlüfterdrehzahl (DP111, unsicher)", DP_DIAG_111, _as_int, "rpm", "mdi:fan", state_class=SensorStateClass.MEASUREMENT, entity_category=EntityCategory.DIAGNOSTIC),
    UnicoSensorDescription("dp_115", "Diagnosewert DP115 (unbekannt)", DP_DIAG_115, _as_int, icon="mdi:help-circle-outline", entity_category=EntityCategory.DIAGNOSTIC),
    UnicoSensorDescription("dp_117", "Diagnosewert DP117 (unbekannt)", DP_DIAG_117, _as_int, icon="mdi:help-circle-outline", entity_category=EntityCategory.DIAGNOSTIC),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: UnicoCoordinator = entry.runtime_data
    async_add_entities(UnicoSensor(coordinator, entry, description) for description in SENSORS)
    async_add_entities([
        UnicoCommunicationSensor(coordinator, entry, "last_response_ms", "Letzte Antwortzeit", "mdi:timer-outline", "ms"),
        UnicoCommunicationSensor(coordinator, entry, "consecutive_failures", "Aufeinanderfolgende Kommunikationsfehler", "mdi:alert-outline"),
        UnicoCommunicationSensor(coordinator, entry, "session_age_seconds", "Tuya-Sitzungsalter", "mdi:clock-outline", UnitOfTime.SECONDS),
        UnicoCommunicationSensor(coordinator, entry, "seconds_since_last_success", "Zeit seit letzter erfolgreicher Kommunikation", "mdi:lan-check", UnitOfTime.SECONDS),
        UnicoCommunicationSensor(coordinator, entry, "total_failures", "Kommunikationsfehler gesamt", "mdi:counter"),
        UnicoCommunicationSensor(coordinator, entry, "planned_rotations", "Geplante Client-Rotationen", "mdi:restart"),
        UnicoCommunicationSensor(coordinator, entry, "seconds_since_planned_rotation", "Zeit seit geplanter Client-Rotation", "mdi:clock-check-outline", UnitOfTime.SECONDS),
    ])


class UnicoSensor(UnicoEntity, SensorEntity):
    def __init__(self, coordinator: UnicoCoordinator, entry: ConfigEntry, description: UnicoSensorDescription) -> None:
        super().__init__(coordinator, entry)
        self._description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{self._device_identifier}_{description.key}"
        self._attr_native_unit_of_measurement = description.native_unit
        self._attr_icon = description.icon
        self._attr_device_class = description.device_class
        self._attr_state_class = description.state_class
        self._attr_entity_category = description.entity_category
        if description.entity_category == EntityCategory.DIAGNOSTIC:
            self._attr_entity_registry_enabled_default = False

    @property
    def native_value(self) -> Any:
        return self._description.value_fn((self.coordinator.data or {}).get(str(self._description.dp)))


class UnicoCommunicationSensor(UnicoEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: UnicoCoordinator, entry: ConfigEntry, key: str, name: str, icon: str, unit: str | None = None) -> None:
        super().__init__(coordinator, entry)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{self._device_identifier}_comm_{key}"
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self) -> Any:
        return self.coordinator.client.diagnostics.get(self._key)
