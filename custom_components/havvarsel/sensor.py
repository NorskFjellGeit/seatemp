"""Support for Met.no weather service."""
from __future__ import annotations

import logging
from types import MappingProxyType
from typing import Any

import voluptuous as vol

from homeassistant.components.sensor import (
    SensorEntity,
    PLATFORM_SCHEMA,
)
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
    TEMP_CELSIUS,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    T,
)

from .const import (
    CONF_TRACK_HOME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

ATTRIBUTION = "Sea data from havvarsel.no"
DEFAULT_NAME = "Havvarsel.no"


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Inclusive(
            CONF_LATITUDE, "coordinates", "Latitude and longitude must exist together"
        ): cv.latitude,
        vol.Inclusive(
            CONF_LONGITUDE, "coordinates", "Latitude and longitude must exist together"
        ): cv.longitude,
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Met.no weather platform."""
    _LOGGER.warning("Loading Met.no via platform config is deprecated")

    # Add defaults.

    if config.get(CONF_LATITUDE) is None:
        config[CONF_TRACK_HOME] = True

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=config
        )
    )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add a weather entity from a config_entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        [
            HavvarselSensorTemperature(coordinator, config_entry.data),
            HavvarselSensorSalinity(coordinator, config_entry.data),
        ]
    )


class HavvarselSensorTemperature(CoordinatorEntity, SensorEntity):
    """Implementation of a Havvarsel.no data."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[T],
        config: MappingProxyType[str, Any],
    ) -> None:
        """Initialise the platform with a data instance and site."""
        super().__init__(coordinator)
        self._config = config

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return "home"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        name = self._config.get(CONF_NAME)
        if name is not None:
            return f"{name} Sea Temperature"

        if self.track_home:
            return f"{self.hass.config.location_name} Sea Temperature"

        return f"{DEFAULT_NAME} Sea Temperature"

    @property
    def should_poll(self):
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def state(self) -> float | None:
        """Return the temperature."""
        return self.coordinator.data.current_data.get("temperature")

    @property
    def icon(self) -> str:
        return "mdi:coolant-temperature"

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement this sensor expresses itself in."""
        return TEMP_CELSIUS

    @property
    def state_class(self) -> str | None:
        return "measurement"


class HavvarselSensorSalinity(CoordinatorEntity, SensorEntity):
    """Implementation of a Havvarsel.no data."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[T],
        config: MappingProxyType[str, Any],
    ) -> None:
        """Initialise the platform with a data instance and site."""
        super().__init__(coordinator)
        self._config = config

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return "home_salinity"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        name = self._config.get(CONF_NAME)
        if name is not None:
            return f"{name} Sea Salinity"

        if self.track_home:
            return f"{self.hass.config.location_name} Sea Salinity"

        return f"{DEFAULT_NAME} Sea Salinity"

    @property
    def should_poll(self):
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def state(self) -> float | None:
        """Return the Salinity."""
        return self.coordinator.data.current_data.get("salinity")

    @property
    def icon(self) -> str:
        return "mdi:water-percent"

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement this sensor expresses itself in."""
        return "‰"

    @property
    def state_class(self) -> str | None:
        return "measurement"
