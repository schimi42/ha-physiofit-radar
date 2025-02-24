"""PhysioFIT Auslastungsradar sensor implementation."""
from datetime import timedelta
import logging
import async_timeout
import aiohttp
from bs4 import BeautifulSoup

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import PERCENTAGE

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=5)
URL = "https://portal.aidoo-online.de/workload?mandant=201000113_physiofit_peine&stud_nr=1"

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info=None,
) -> None:
    """Set up the PhysioFIT sensor."""
    async_add_entities([PhysioFITSensor()], True)

class PhysioFITSensor(SensorEntity):
    """Representation of a PhysioFIT utilization sensor."""

    def __init__(self):
        """Initialize the sensor."""
        self._attr_name = "PhysioFIT Auslastung"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_unique_id = "physiofit_peine_utilization"
        self._attr_native_value = None

    async def async_update(self):
        """Fetch new state data for the sensor."""
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
                            
                            # Find the specific div with id="studioChart1"
                            chart_div = soup.find('div', id='studioChart1')
                            if chart_div and chart_div.has_attr('percentage'):
                                # Get the percentage attribute and clean it up
                                percent_value = chart_div['percentage'].replace(',', '.').replace('%', '').strip()
                                try:
                                    self._attr_native_value = float(percent_value)
                                    _LOGGER.debug("Found utilization: %s%%", self._attr_native_value)
                                except ValueError:
                                    _LOGGER.error("Could not parse percentage value: %s", percent_value)
                            else:
                                _LOGGER.error("Percentage div not found on page")
                        else:
                            _LOGGER.error("Failed to fetch data: %s", response.status)
        except Exception as err:
            _LOGGER.error("Error updating PhysioFIT sensor: %s", err) 