"""Olimpia Splendid UNICO local integration."""

from __future__ import annotations

from datetime import datetime
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.event import async_track_time_change

from .client import UnicoClient
from .const import (
    CONF_DEVICE_ID,
    CONF_LOCAL_KEY,
    DAILY_MAINTENANCE_HOUR,
    DAILY_MAINTENANCE_MINUTE,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import UnicoCoordinator
from .identifiers import device_fingerprint

_LOGGER = logging.getLogger(__name__)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate raw Device IDs out of Home Assistant registry identifiers."""
    if entry.version != 1:
        return True

    raw_device_id = entry.data[CONF_DEVICE_ID]
    fingerprint = device_fingerprint(raw_device_id)

    device_registry = dr.async_get(hass)
    for device in dr.async_entries_for_config_entry(
        device_registry, config_entry_id=entry.entry_id
    ):
        new_identifiers = {
            (DOMAIN, fingerprint)
            if domain == DOMAIN and identifier == raw_device_id
            else (domain, identifier)
            for domain, identifier in device.identifiers
        }
        if new_identifiers != device.identifiers:
            device_registry.async_update_device(
                device.id, new_identifiers=new_identifiers
            )

    entity_registry = er.async_get(hass)
    for entity in er.async_entries_for_config_entry(
        entity_registry, config_entry_id=entry.entry_id
    ):
        prefix = f"{raw_device_id}_"
        if entity.unique_id.startswith(prefix):
            entity_registry.async_update_entity(
                entity.entity_id,
                new_unique_id=f"{fingerprint}_{entity.unique_id[len(prefix):]}",
            )

    hass.config_entries.async_update_entry(
        entry,
        unique_id=fingerprint,
        version=2,
    )
    _LOGGER.debug("Migrated UNICO registry identifiers to a device fingerprint")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Olimpia Splendid UNICO from a config entry."""
    client = UnicoClient(
        entry.data[CONF_HOST],
        entry.data[CONF_DEVICE_ID],
        entry.data[CONF_LOCAL_KEY],
    )
    coordinator = UnicoCoordinator(hass, entry, client)
    entry.runtime_data = coordinator

    # Do not use async_config_entry_first_refresh() here. A temporary Tuya/LAN
    # failure during Home Assistant startup would recreate the client on each
    # setup retry and defeat the reconnect behavior tested with this Wi-Fi module.
    #
    # A normal async_refresh() records the failed update in the coordinator but
    # lets the integration stay loaded. The entities are then unavailable and
    # the same coordinator/client can recover on a later scheduled poll.
    await coordinator.async_refresh()
    if not coordinator.last_update_success:
        _LOGGER.debug(
            "UNICO initial refresh failed; integration remains loaded and will "
            "retry with the existing client/backoff state"
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def _daily_maintenance_callback(now: datetime) -> None:
        _LOGGER.debug("UNICO daily maintenance trigger at %s", now.isoformat())
        await coordinator.async_daily_maintenance()

    entry.async_on_unload(
        async_track_time_change(
            hass,
            _daily_maintenance_callback,
            hour=DAILY_MAINTENANCE_HOUR,
            minute=DAILY_MAINTENANCE_MINUTE,
            second=0,
        )
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and close its persistent Tuya session."""
    coordinator: UnicoCoordinator = entry.runtime_data
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await hass.async_add_executor_job(coordinator.client.close)
    return unloaded
