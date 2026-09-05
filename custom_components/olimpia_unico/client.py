"""Blocking TinyTuya client wrapper for Olimpia Splendid UNICO."""

from __future__ import annotations

import logging
import time
from threading import Lock
from typing import Any, Callable

import tinytuya

from .const import (
    RECONNECT_BACKOFF,
    SOCKET_RETRY_DELAY,
    SOCKET_RETRY_LIMIT,
    SOCKET_TIMEOUT,
    TUYA_VERSION,
)

_LOGGER = logging.getLogger(__name__)


class UnicoCommunicationError(Exception):
    """Raised when communication with the UNICO fails."""


class UnicoReconnectBackoffError(UnicoCommunicationError):
    """Raised when an operation is intentionally skipped during reconnect backoff."""


def validate_connection(host: str, device_id: str, local_key: str) -> dict[str, Any]:
    """Validate credentials with a short-lived, non-persistent Tuya session."""
    device = tinytuya.Device(device_id, host, local_key, version=TUYA_VERSION, persist=False)
    device.set_socketPersistent(False)
    device.set_socketTimeout(SOCKET_TIMEOUT)
    device.set_socketRetryLimit(SOCKET_RETRY_LIMIT)
    device.set_socketRetryDelay(SOCKET_RETRY_DELAY)
    try:
        data = device.status()
        if not isinstance(data, dict):
            raise UnicoCommunicationError(f"Unexpected response: {data!r}")
        if "Error" in data or "Err" in data:
            raise UnicoCommunicationError(f"TinyTuya error {data.get('Err')}: {data.get('Error')}")
        dps = data.get("dps")
        if not isinstance(dps, dict):
            raise UnicoCommunicationError(f"No DPS in response: {data!r}")
        return {str(key): value for key, value in dps.items()}
    except UnicoCommunicationError:
        raise
    except Exception as err:  # noqa: BLE001
        raise UnicoCommunicationError(str(err)) from err
    finally:
        try:
            device.close()
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("UNICO validation socket close raised %r", err)


class UnicoClient:
    """Local client for an Olimpia Splendid UNICO using Tuya LAN protocol."""

    def __init__(self, host: str, device_id: str, local_key: str) -> None:
        self.host = host
        self.device_id = device_id
        self.local_key = local_key
        self._lock = Lock()
        self._backoff_index = 0
        self._retry_after = 0.0
        self._consecutive_failures = 0
        self._total_requests = 0
        self._total_failures = 0
        self._last_success_monotonic: float | None = None
        self._last_response_ms: int | None = None
        self._planned_rotations = 0
        self._last_planned_rotation_monotonic: float | None = None
        self._device: tinytuya.Device | None = None
        self._session_created_at = 0.0
        self._replace_device("initial setup")

    def _new_device(self) -> tinytuya.Device:
        device = tinytuya.Device(self.device_id, self.host, self.local_key, version=TUYA_VERSION, persist=True)
        device.set_socketPersistent(True)
        device.set_socketTimeout(SOCKET_TIMEOUT)
        device.set_socketRetryLimit(SOCKET_RETRY_LIMIT)
        device.set_socketRetryDelay(SOCKET_RETRY_DELAY)
        return device

    def _close_device(self) -> None:
        if self._device is None:
            return
        try:
            self._device.close()
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("UNICO socket close raised %r", err)

    def _replace_device(self, reason: str) -> None:
        self._close_device()
        self._device = self._new_device()
        self._session_created_at = time.monotonic()
        _LOGGER.debug("UNICO created fresh Tuya 3.4 session/client (%s)", reason)

    def planned_rotate(self, reason: str = "scheduled daily maintenance") -> None:
        with self._lock:
            self._replace_device(reason)
            self._planned_rotations += 1
            self._last_planned_rotation_monotonic = time.monotonic()

    @staticmethod
    def _check_response(data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise UnicoCommunicationError(f"Unexpected response: {data!r}")
        if "Error" in data or "Err" in data:
            raise UnicoCommunicationError(f"TinyTuya error {data.get('Err')}: {data.get('Error')}")
        return data

    def _check_backoff(self) -> None:
        remaining = self._retry_after - time.monotonic()
        if remaining > 0:
            raise UnicoReconnectBackoffError(f"Reconnect backoff active ({int(remaining) + 1}s remaining)")

    def _record_success(self, elapsed_ms: int, operation_name: str) -> None:
        self._backoff_index = 0
        self._retry_after = 0.0
        self._consecutive_failures = 0
        self._last_success_monotonic = time.monotonic()
        self._last_response_ms = elapsed_ms
        _LOGGER.debug("UNICO %s succeeded in %d ms; session age %.1f min", operation_name, elapsed_ms, (time.monotonic() - self._session_created_at) / 60)

    def _record_failure(self, err: Exception, operation_name: str) -> None:
        self._total_failures += 1
        self._consecutive_failures += 1
        delay = RECONNECT_BACKOFF[min(self._backoff_index, len(RECONNECT_BACKOFF) - 1)]
        self._backoff_index = min(self._backoff_index + 1, len(RECONNECT_BACKOFF) - 1)
        self._retry_after = time.monotonic() + delay
        _LOGGER.debug("UNICO %s failed (%s); consecutive failures=%d; fresh client will be used after %ds backoff", operation_name, err, self._consecutive_failures, delay)
        self._replace_device("communication failure")

    def _run(self, operation_name: str, operation: Callable[[], Any]) -> dict[str, Any]:
        self._check_backoff()
        self._total_requests += 1
        started = time.monotonic()
        try:
            data = self._check_response(operation())
        except Exception as err:  # noqa: BLE001
            wrapped = err if isinstance(err, UnicoCommunicationError) else UnicoCommunicationError(str(err))
            self._record_failure(wrapped, operation_name)
            raise wrapped
        elapsed_ms = round((time.monotonic() - started) * 1000)
        self._record_success(elapsed_ms, operation_name)
        return data

    def status(self) -> dict[str, Any]:
        with self._lock:
            if self._device is None:
                self._replace_device("missing client")
            data = self._run("status", self._device.status)
            dps = data.get("dps")
            if not isinstance(dps, dict):
                err = UnicoCommunicationError(f"No DPS in response: {data!r}")
                self._record_failure(err, "status")
                raise err
            return {str(key): value for key, value in dps.items()}

    def set_value(self, dp: int, value: Any) -> None:
        with self._lock:
            if self._device is None:
                self._replace_device("missing client")
            self._run(f"set DP {dp}", lambda: self._device.set_value(dp, value))

    def set_values(self, values: dict[int, Any]) -> None:
        with self._lock:
            if self._device is None:
                self._replace_device("missing client")
            dps = ",".join(str(dp) for dp in sorted(values))
            self._run(f"set DPs {dps}", lambda: self._device.set_multiple_values(values))

    def close(self) -> None:
        with self._lock:
            self._close_device()
            self._device = None
            self._retry_after = 0.0
            _LOGGER.debug("UNICO local Tuya client closed")

    @property
    def diagnostics(self) -> dict[str, Any]:
        now = time.monotonic()
        return {
            "session_age_seconds": max(0, int(now - self._session_created_at)),
            "seconds_since_last_success": None if self._last_success_monotonic is None else max(0, int(now - self._last_success_monotonic)),
            "last_response_ms": self._last_response_ms,
            "consecutive_failures": self._consecutive_failures,
            "total_requests": self._total_requests,
            "total_failures": self._total_failures,
            "backoff_remaining_seconds": max(0, int(self._retry_after - now)),
            "planned_rotations": self._planned_rotations,
            "seconds_since_planned_rotation": None if self._last_planned_rotation_monotonic is None else max(0, int(now - self._last_planned_rotation_monotonic)),
        }
