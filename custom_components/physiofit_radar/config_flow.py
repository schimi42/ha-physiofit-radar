"""Config flow for PhysioFIT Auslastungsradar."""
from homeassistant import config_entries

class PhysioFITConfigFlow(config_entries.ConfigFlow, domain="physiofit_radar"):
    """Handle a config flow for PhysioFIT Auslastungsradar."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(step_id="user")

        return self.async_create_entry(
            title="PhysioFIT Auslastungsradar",
            data={}
        ) 