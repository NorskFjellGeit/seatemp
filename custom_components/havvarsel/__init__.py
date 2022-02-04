"""The Havvarsel.no integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from random import randrange
from collections.abc import Callable
from typing import Any
from types import MappingProxyType
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    EVENT_CORE_CONFIG_UPDATE,
    LENGTH_FEET,
    LENGTH_METERS,
    Platform,
)
from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.util.dt as dt_util

from .const import (
    DOMAIN,
    CONF_TRACK_HOME,
    DEFAULT_HOME_LATITUDE,
    DEFAULT_HOME_LONGITUDE,
    API_URL,
)

from . import havvarsel

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up Havvarsel as config entry."""
    # Don't setup if tracking home location and latitude or longitude isn't set.
    # Also, filters out our onboarding default location.
    if config_entry.data.get(CONF_TRACK_HOME, False) and (
        (not hass.config.latitude and not hass.config.longitude)
        or (
            hass.config.latitude == DEFAULT_HOME_LATITUDE
            and hass.config.longitude == DEFAULT_HOME_LONGITUDE
        )
    ):
        _LOGGER.warning(
            "Skip setting up havvarsel.no integration; No Home location has been set"
        )
        return False

    coordinator = HavvarselDataUpdateCoordinator(hass, config_entry)
    await coordinator.async_config_entry_first_refresh()

    if config_entry.data.get(CONF_TRACK_HOME, False):
        coordinator.track_home()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = coordinator

    hass.config_entries.async_setup_platforms(config_entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )

    hass.data[DOMAIN][config_entry.entry_id].untrack_home()
    hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


class HavvarselDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Met data."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize global Met data updater."""
        self._unsub_track_home: Callable | None = None
        self.weather = HavvarselData(
            hass, config_entry.data, hass.config.units.is_metric
        )
        self.weather.set_coordinates()

        update_interval = timedelta(minutes=randrange(55, 65))

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

    async def _async_update_data(self) -> HavvarselData:
        """Fetch data from Met."""
        try:
            return await self.weather.fetch_data()
        except Exception as err:
            raise UpdateFailed(f"Update failed: {err}") from err

    def track_home(self) -> None:
        """Start tracking changes to HA home setting."""
        if self._unsub_track_home:
            return

        async def _async_update_weather_data(_event: Event | None = None) -> None:
            """Update weather data."""
            if self.weather.set_coordinates():
                await self.async_refresh()

        self._unsub_track_home = self.hass.bus.async_listen(
            EVENT_CORE_CONFIG_UPDATE, _async_update_weather_data
        )

    def untrack_home(self) -> None:
        """Stop tracking changes to HA home setting."""
        if self._unsub_track_home:
            self._unsub_track_home()
            self._unsub_track_home = None


class HavvarselData:
    """Keep data for Havvarsel entities."""

    def __init__(
        self, hass: HomeAssistant, config: MappingProxyType[str, Any], is_metric: bool
    ) -> None:
        """Initialise the weather entity data."""
        self.hass = hass
        self._config = config
        self._sea_data: havvarsel.HavvarselData
        self.current_data: dict = {}
        self._coordinates: dict[str, str] | None = None

    def set_coordinates(self) -> bool:
        """Weather data inialization - set the coordinates."""
        if self._config.get(CONF_TRACK_HOME, False):
            latitude = self.hass.config.latitude
            longitude = self.hass.config.longitude
        else:
            latitude = self._config[CONF_LATITUDE]
            longitude = self._config[CONF_LONGITUDE]

        coordinates = {
            "lat": str(latitude),
            "lon": str(longitude),
        }
        if coordinates == self._coordinates:
            return False
        self._coordinates = coordinates

        self._sea_data = havvarsel.HavvarselData(
            coordinates, async_get_clientsession(self.hass), api_url=API_URL
        )
        return True

    async def fetch_data(self) -> HavvarselData:
        """Fetch data from API - (current weather and forecast)."""
        await self._sea_data.fetching_data()
        self.current_data = self._sea_data.get_current_seadata()
        _LOGGER.info(self.current_data)
        return self
