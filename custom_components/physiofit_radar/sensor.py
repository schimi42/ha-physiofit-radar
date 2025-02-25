"""PhysioFIT Auslastungsradar sensor implementation."""
from datetime import timedelta, datetime
import logging
import async_timeout
import aiohttp
from bs4 import BeautifulSoup
import os

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import PERCENTAGE

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=5)
URL = "https://portal.aidoo-online.de/workload?mandant=201000113_physiofit_peine&stud_nr=1"

WEEKDAYS = {
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
    4: "friday",
    5: "saturday",
    6: "sunday"
}

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the PhysioFIT sensor from config entry."""
    async_add_entities([PhysioFITSensor(config_entry)], True)

class PhysioFITSensor(SensorEntity):
    """Representation of a PhysioFIT utilization sensor."""

    def __init__(self, config_entry: ConfigEntry):
        """Initialize the sensor."""
        self._config_entry = config_entry
        self._attr_name = "PhysioFIT Auslastung"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}"
        self._attr_native_value = 0  # Initialize with 0
        self._attr_available = True   # Always available
        
        # Use the icon from the brand directory
        self._attr_icon = "mdi:dumbbell"  # Fallback icon
        current_dir = os.path.dirname(os.path.realpath(__file__))
        icon_path = os.path.join(current_dir, "brand", "icon.jpg")
        if os.path.exists(icon_path):
            self._attr_entity_picture = f"/local/custom_components/{DOMAIN}/brand/icon.jpg"

    def _is_open(self) -> bool:
        """Check if the gym is currently open."""
        now = datetime.now()
        weekday = WEEKDAYS[now.weekday()]
        
        # Check if day is enabled
        if not self._config_entry.data.get(f"{weekday}_enabled", True):
            return False

        # Get opening hours for current day
        open_time = self._config_entry.data.get(f"{weekday}_open", "08:00")
        close_time = self._config_entry.data.get(f"{weekday}_close", "22:00")

        # Convert times to datetime objects
        open_hour, open_minute = map(int, open_time.split(":"))
        close_hour, close_minute = map(int, close_time.split(":"))
        
        opening = now.replace(hour=open_hour, minute=open_minute)
        closing = now.replace(hour=close_hour, minute=close_minute)

        return opening <= now <= closing

    async def async_update(self):
        """Fetch new state data for the sensor."""
        if not self._is_open():
            self._attr_native_value = 0
            _LOGGER.debug("Gym is currently closed, setting utilization to 0%")
            return

        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    }
                    async with session.get(URL, headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            chart_div = soup.find('div', id='studioChart1')
                            if chart_div and chart_div.has_attr('percentage'):
                                percent_value = chart_div['percentage'].replace(',', '.').replace('%', '').strip()
                                try:
                                    self._attr_native_value = float(percent_value)
                                    _LOGGER.debug("Found utilization: %s%%", self._attr_native_value)
                                except ValueError:
                                    self._attr_native_value = 0
                                    _LOGGER.error("Could not parse percentage value: %s", percent_value)
                            else:
                                self._attr_native_value = 0
                                _LOGGER.error("Percentage div not found on page")
                        else:
                            self._attr_native_value = 0
                            _LOGGER.error("Failed to fetch data: %s", response.status)
        except Exception as err:
            self._attr_native_value = 0
            _LOGGER.error("Error updating PhysioFIT sensor: %s", err) 