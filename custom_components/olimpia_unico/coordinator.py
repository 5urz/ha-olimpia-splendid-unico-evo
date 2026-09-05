"""Data coordinator for Olimpia Splendid UNICO."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import UnicoClient, UnicoCommunicationError, UnicoReconnectBackoffError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, DP_POWER

_LOGGER = logging.getLogger(__name__)


class UnicoCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll and control one UNICO device."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: UnicoClient) -> None:
        self.client = client
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.hass.async_add_executor_job(self.client.status)
            _LOGGER.debug("UNICO coordinator diagnostics: %s", self.client.diagnostics)
            return data
        except UnicoReconnectBackoffError as err:
            _LOGGER.debug(
                "UNICO coordinator poll skipped during reconnect backoff: %s; diagnostics=%s",
                err,
                self.client.diagnostics,
            )
            if self.data is not None:
                return self.data
            raise UpdateFailed(str(err)) from err
        except UnicoCommunicationError as err:
            diagnostics = self.client.diagnostics
            failures = int(diagnostics.get("consecutive_failures", 0))
            if self.data is not None and failures < 3:
                _LOGGER.debug(
                    "UNICO transient communication failure (%d/3): %s; keeping last state; diagnostics=%s",
                    failures,
                    err,
                    diagnostics,
                )
                return self.data
            raise UpdateFailed(
                f"UNICO unavailable after {failures} consecutive communication failure(s): {err}"
            ) from err

    async def async_daily_maintenance(self) -> None:
        power_state = (self.data or {}).get(str(DP_POWER))
        if not self.last_update_success:
            _LOGGER.debug("UNICO daily 10:00 client rotation skipped: latest device state is unavailable")
            return
        if power_state is not False:
            _LOGGER.debug(
                "UNICO daily 10:00 client rotation skipped: unit is on or power state is unknown (%r)",
                power_state,
            )
            return
        _LOGGER.debug("UNICO daily 10:00 client rotation starting: unit is off")
        await self.hass.async_add_executor_job(
            self.client.planned_rotate,
            "scheduled daily 10:00 rotation while unit is off",
        )
        try:
            data = await self.hass.async_add_executor_job(self.client.status)
        except UnicoCommunicationError as err:
            _LOGGER.debug(
                "UNICO daily 10:00 maintenance status read failed: %s; diagnostics=%s",
                err,
                self.client.diagnostics,
            )
            return
        self.async_set_updated_data(data)
        _LOGGER.debug(
            "UNICO daily 10:00 client rotation completed successfully; diagnostics=%s",
            self.client.diagnostics,
        )

    def _optimistic_update(self, values: dict[int, Any]) -> None:
        current = dict(self.data or {})
        for dp, value in values.items():
            current[str(dp)] = value
        self.async_set_updated_data(current)

    async def async_set_value(self, dp: int, value: Any) -> None:
        try:
            await self.hass.async_add_executor_job(self.client.set_value, dp, value)
        except UnicoReconnectBackoffError as err:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="reconnect_backoff") from err
        except UnicoCommunicationError as err:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="communication_failed") from err
        self._optimistic_update({dp: value})

    async def async_set_values(self, values: dict[int, Any]) -> None:
        try:
            await self.hass.async_add_executor_job(self.client.set_values, values)
        except UnicoReconnectBackoffError as err:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="reconnect_backoff") from err
        except UnicoCommunicationError as err:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="communication_failed") from err
        self._optimistic_update(values)
