"""Climate platform for Olimpia Splendid UNICO."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import FAN_AUTO, FAN_HIGH, FAN_LOW, FAN_MEDIUM, SWING_OFF, SWING_ON, ClimateEntityFeature, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DP_CURRENT_TEMP, DP_ECO, DP_FAN, DP_MODE, DP_POWER, DP_SILENT, DP_SWING, DP_TARGET_TEMP, MAX_TEMP, MIN_TEMP, PRESET_ECO, PRESET_ECO_SILENT, PRESET_NORMAL, PRESET_SILENT
from .coordinator import UnicoCoordinator
from .entity import UnicoEntity

PARALLEL_UPDATES = 1

TUYA_TO_HVAC = {"auto": HVACMode.AUTO, "cool": HVACMode.COOL, "heat": HVACMode.HEAT, "dehum": HVACMode.DRY, "fan": HVACMode.FAN_ONLY}
HVAC_TO_TUYA = {value: key for key, value in TUYA_TO_HVAC.items()}
TUYA_TO_FAN = {"auto": FAN_AUTO, "low": FAN_LOW, "middle": FAN_MEDIUM, "high": FAN_HIGH}
FAN_TO_TUYA = {value: key for key, value in TUYA_TO_FAN.items()}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: UnicoCoordinator = entry.runtime_data
    async_add_entities([UnicoClimate(coordinator, entry)])


class UnicoClimate(UnicoEntity, ClimateEntity):
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP
    _attr_target_temperature_step = 1.0
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.AUTO, HVACMode.COOL, HVACMode.HEAT, HVACMode.DRY, HVACMode.FAN_ONLY]
    _attr_fan_modes = [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH]
    _attr_swing_modes = [SWING_OFF, SWING_ON]
    _attr_preset_modes = [PRESET_NORMAL, PRESET_ECO, PRESET_SILENT, PRESET_ECO_SILENT]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE | ClimateEntityFeature.SWING_MODE | ClimateEntityFeature.PRESET_MODE | ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF

    def __init__(self, coordinator: UnicoCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._device_identifier}_climate"

    def _dp(self, dp: int, default: Any = None) -> Any:
        return (self.coordinator.data or {}).get(str(dp), default)

    @property
    def current_temperature(self) -> float | None:
        value = self._dp(DP_CURRENT_TEMP)
        return float(value) if isinstance(value, (int, float)) else None

    @property
    def target_temperature(self) -> float | None:
        value = self._dp(DP_TARGET_TEMP)
        return float(value) if isinstance(value, (int, float)) else None

    @property
    def hvac_mode(self) -> HVACMode:
        if not bool(self._dp(DP_POWER, False)):
            return HVACMode.OFF
        return TUYA_TO_HVAC.get(str(self._dp(DP_MODE)), HVACMode.AUTO)

    @property
    def fan_mode(self) -> str:
        return TUYA_TO_FAN.get(str(self._dp(DP_FAN)), FAN_AUTO)

    @property
    def swing_mode(self) -> str:
        return SWING_ON if str(self._dp(DP_SWING, "OFF")).upper() == "ON" else SWING_OFF

    @property
    def preset_mode(self) -> str:
        eco = bool(self._dp(DP_ECO, False))
        silent = bool(self._dp(DP_SILENT, False))
        if eco and silent:
            return PRESET_ECO_SILENT
        if silent:
            return PRESET_SILENT
        if eco:
            return PRESET_ECO
        return PRESET_NORMAL

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is not None:
            await self.coordinator.async_set_value(DP_TARGET_TEMP, int(round(temperature)))

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.async_set_value(DP_POWER, False)
            return
        tuya_mode = HVAC_TO_TUYA.get(hvac_mode)
        if tuya_mode is not None:
            await self.coordinator.async_set_values({DP_POWER: True, DP_MODE: tuya_mode})

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        tuya_fan = FAN_TO_TUYA.get(fan_mode)
        if tuya_fan is not None:
            await self.coordinator.async_set_value(DP_FAN, tuya_fan)

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        if swing_mode in self._attr_swing_modes:
            await self.coordinator.async_set_value(DP_SWING, "ON" if swing_mode == SWING_ON else "OFF")

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode == PRESET_NORMAL:
            values = {DP_ECO: False, DP_SILENT: False}
        elif preset_mode == PRESET_ECO:
            values = {DP_ECO: True}
        elif preset_mode == PRESET_SILENT:
            values = {DP_SILENT: True}
        elif preset_mode == PRESET_ECO_SILENT:
            values = {DP_ECO: True, DP_SILENT: True}
        else:
            return
        await self.coordinator.async_set_values(values)

    async def async_turn_on(self) -> None:
        await self.coordinator.async_set_value(DP_POWER, True)

    async def async_turn_off(self) -> None:
        await self.coordinator.async_set_value(DP_POWER, False)
