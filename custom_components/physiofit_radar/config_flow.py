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

def get_schema_for_day(day: str) -> vol.Schema:
    """Get schema for a specific day."""
    return vol.Schema({
        vol.Required(f"{day}_enabled", default=True): bool,
        vol.Optional(f"{day}_open", default="08:00"): str,
        vol.Optional(f"{day}_close", default="22:00"): str,
    })

def time_string_to_dict(time_str: str) -> dict:
    """Convert HH:MM time string to dict."""
    if not time_str:
        return {"hour": 0, "minute": 0}
    try:
        hour, minute = time_str.split(":")
        hour_int = int(hour)
        minute_int = int(minute)
        if not (0 <= hour_int <= 23 and 0 <= minute_int <= 59):
            raise ValueError
        return {"hour": hour_int, "minute": minute_int}
    except ValueError:
        raise ValueError("Invalid time format")

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PhysioFIT Auslastungsradar."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._data = {}
        self._current_day_index = 0

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        # Check if already configured
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        return await self.async_step_day()

    async def async_step_day(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle day configuration."""
        errors = {}
        
        if self._current_day_index >= len(DAYS):
            # All days configured, create the entry
            return self.async_create_entry(
                title="PhysioFIT Auslastungsradar",
                data=self._data
            )

        current_day = list(DAYS.keys())[self._current_day_index]
        
        if user_input is not None:
            try:
                if user_input[f"{current_day}_enabled"]:
                    # Validate time format
                    time_string_to_dict(user_input[f"{current_day}_open"])
                    time_string_to_dict(user_input[f"{current_day}_close"])
                
                # Store the data
                self._data.update(user_input)
                
                # Move to next day
                self._current_day_index += 1
                
                # If we have more days, show the next form
                if self._current_day_index < len(DAYS):
                    return await self.async_step_day()
                
                # All days configured, create the entry
                return self.async_create_entry(
                    title="PhysioFIT Auslastungsradar",
                    data=self._data
                )
                
            except ValueError:
                errors["base"] = "time_format"

        return self.async_show_form(
            step_id="day",
            data_schema=get_schema_for_day(current_day),
            errors=errors,
            description_placeholders={
                "day": DAYS[current_day],
                "current_step": str(self._current_day_index + 1),
                "total_steps": str(len(DAYS))
            }
        ) 