"""Config flow for Olimpia Splendid UNICO."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from .client import UnicoCommunicationError, validate_connection
from .const import CONF_DEVICE_ID, CONF_LOCAL_KEY, DOMAIN, DP_POWER, DP_TARGET_TEMP
from .identifiers import device_fingerprint

_LOGGER = logging.getLogger(__name__)


class UnicoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for UNICO."""

    VERSION = 2

    async def _async_validate(
        self, host: str, device_id: str, local_key: str
    ) -> str | None:
        """Validate a local UNICO connection and return a config-flow error key."""
        try:
            dps = await self.hass.async_add_executor_job(
                validate_connection,
                host,
                device_id,
                local_key,
            )
            if str(DP_POWER) not in dps or str(DP_TARGET_TEMP) not in dps:
                raise UnicoCommunicationError("Unexpected UNICO DPS response")
        except UnicoCommunicationError as err:
            _LOGGER.debug("UNICO config validation failed: %s", err)
            return "cannot_connect"
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Unexpected error while validating UNICO connection")
            return "unknown"
        return None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Set up a new UNICO."""
        errors: dict[str, str] = {}

        if user_input is not None:
            data = {
                CONF_HOST: str(user_input[CONF_HOST]).strip(),
                CONF_DEVICE_ID: str(user_input[CONF_DEVICE_ID]).strip(),
                CONF_LOCAL_KEY: str(user_input[CONF_LOCAL_KEY]).strip(),
            }
            error = await self._async_validate(
                data[CONF_HOST],
                data[CONF_DEVICE_ID],
                data[CONF_LOCAL_KEY],
            )
            if error is not None:
                errors["base"] = error
            else:
                await self.async_set_unique_id(device_fingerprint(data[CONF_DEVICE_ID]))
                self._abort_if_unique_id_configured(
                    updates={
                        CONF_HOST: data[CONF_HOST],
                        CONF_LOCAL_KEY: data[CONF_LOCAL_KEY],
                    }
                )
                return self.async_create_entry(
                    title="UNICO EVO",
                    data=data,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                ),
                vol.Required(CONF_DEVICE_ID): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                ),
                vol.Required(CONF_LOCAL_KEY): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Allow the user to update the host or Local Key."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            host = str(user_input[CONF_HOST]).strip()
            submitted_key = str(user_input.get(CONF_LOCAL_KEY, "")).strip()
            local_key = submitted_key or entry.data[CONF_LOCAL_KEY]
            device_id = entry.data[CONF_DEVICE_ID]

            error = await self._async_validate(host, device_id, local_key)
            if error is not None:
                errors["base"] = error
            else:
                await self.async_set_unique_id(device_fingerprint(device_id))
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_HOST: host,
                        CONF_LOCAL_KEY: local_key,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_HOST,
                    description={"suggested_value": entry.data[CONF_HOST]},
                ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
                vol.Optional(CONF_LOCAL_KEY): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
            }
        )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=schema,
            errors=errors,
        )
