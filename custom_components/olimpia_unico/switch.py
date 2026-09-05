"""Switch platform for Olimpia Splendid UNICO."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DP_DISPLAY, DP_ECO, DP_SILENT
from .coordinator import UnicoCoordinator
from .entity import UnicoEntity

PARALLEL_UPDATES = 1


@dataclass(frozen=True)
class UnicoSwitchDescription:
    key: str
    name: str
    dp: int
    icon: str


SWITCHES = (
    UnicoSwitchDescription("display", "Display", DP_DISPLAY, "mdi:monitor"),
    UnicoSwitchDescription("eco", "Eco", DP_ECO, "mdi:leaf"),
    UnicoSwitchDescription("silent", "Silent", DP_SILENT, "mdi:volume-low"),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: UnicoCoordinator = entry.runtime_data
    async_add_entities(UnicoSwitch(coordinator, entry, description) for description in SWITCHES)


class UnicoSwitch(UnicoEntity, SwitchEntity):
    def __init__(self, coordinator: UnicoCoordinator, entry: ConfigEntry, description: UnicoSwitchDescription) -> None:
        super().__init__(coordinator, entry)
        self._description = description
        self._attr_name = description.name
        self._attr_icon = description.icon
        self._attr_unique_id = f"{self._device_identifier}_{description.key}"

    @property
    def is_on(self) -> bool:
        return bool((self.coordinator.data or {}).get(str(self._description.dp), False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_value(self._description.dp, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_value(self._description.dp, False)
