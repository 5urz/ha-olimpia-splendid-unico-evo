"""Base entity for Olimpia Splendid UNICO."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_ID, DOMAIN
from .coordinator import UnicoCoordinator
from .identifiers import device_fingerprint


class UnicoEntity(CoordinatorEntity[UnicoCoordinator]):
    """Base class for UNICO entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: UnicoCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._device_identifier = device_fingerprint(entry.data[CONF_DEVICE_ID])

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_identifier)},
            manufacturer="Olimpia Splendid",
            model="UNICO EVO",
            name=self._entry.title,
        )
