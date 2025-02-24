"""Config flow for PhysioFIT Auslastungsradar."""
from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.const import CONF_NAME

from . import DOMAIN

DAYS = {
    "monday": "Montag",
    "tuesday": "Dienstag",
    "wednesday": "Mittwoch",
    "thursday": "Donnerstag",
    "friday": "Freitag",
    "saturday": "Samstag",
    "sunday": "Sonntag"
}

def time_string_to_dict(time_str: str) -> dict:
    """Convert HH:MM time string to dict."""
    if not time_str:
        return {"hour": 0, "minute": 0}
    try:
        hour, minute = time_str.split(":")
        return {"hour": int(hour), "minute": int(minute)}
    except ValueError:
        return {"hour": 0, "minute": 0}

for day in DAYS:
    STEP_USER_DATA_SCHEMA = vol.Schema(
        {
            vol.Optional(f"{day}_enabled", default=True): bool,
            vol.Optional(f"{day}_open", default="08:00"): str,
            vol.Optional(f"{day}_close", default="22:00"): str,
        }
    )

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PhysioFIT Auslastungsradar."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._data = {}
        self._current_step = 0

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        # Check if already configured
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                description_placeholders={"day": DAYS[list(DAYS.keys())[self._current_step]]}
            )

        errors = {}

        # Validate time format
        for day in DAYS:
            if user_input.get(f"{day}_enabled"):
                try:
                    time_string_to_dict(user_input[f"{day}_open"])
                    time_string_to_dict(user_input[f"{day}_close"])
                except ValueError:
                    errors[f"{day}_open"] = "time_format"
                    errors[f"{day}_close"] = "time_format"

        if errors:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors=errors,
                description_placeholders={"day": DAYS[list(DAYS.keys())[self._current_step]]}
            )

        return self.async_create_entry(
            title="PhysioFIT Auslastungsradar",
            data=user_input
        ) 