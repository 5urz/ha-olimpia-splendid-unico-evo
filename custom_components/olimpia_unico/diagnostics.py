"""Diagnostics support for Olimpia Splendid UNICO."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .const import CONF_DEVICE_ID, CONF_LOCAL_KEY
from .coordinator import UnicoCoordinator

TO_REDACT = {
    CONF_HOST,
    CONF_DEVICE_ID,
    CONF_LOCAL_KEY,
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry with connection secrets redacted."""
    coordinator: UnicoCoordinator = entry.runtime_data
    return {
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "device_data": dict(coordinator.data or {}),
        "communication": coordinator.client.diagnostics,
    }
