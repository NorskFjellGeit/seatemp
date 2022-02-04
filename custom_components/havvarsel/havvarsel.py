import asyncio
import datetime
import logging


import aiohttp
import async_timeout
import pytz

TIMEOUT = 30

_LOGGER = logging.getLogger(__name__)

DEFAULT_API_URL = "https://api.havvarsel.no/apps/havvarsel/v1/get_projection"


class HavvarselData:
    """Representation of Havvarsel data."""

    def __init__(self, urlparams, websession=None, api_url=DEFAULT_API_URL):
        """Initialize the Havvarsel object."""
        urlparams = {
            "lat": str(round(float(urlparams["lat"]), 4)),
            "lon": str(round(float(urlparams["lon"]), 4)),
            "variable": "temperature,salinity",
        }
        self._urlparams = urlparams
        self._api_url = api_url
        if websession is None:

            async def _create_session():
                return aiohttp.ClientSession()

            loop = asyncio.get_event_loop()
            self._websession = loop.run_until_complete(_create_session())
        else:
            self._websession = websession
        self.data = None

    async def fetching_data(self, *_):
        """Get the latest data from met.no."""
        try:
            async with async_timeout.timeout(TIMEOUT):
                resp = await self._websession.get(self._api_url, params=self._urlparams)
            if resp.status >= 400:
                _LOGGER.error("%s returned %s", self._api_url, resp.status)
                return False
            self.data = await resp.json()
        except (asyncio.TimeoutError, aiohttp.ClientError) as err:
            _LOGGER.error(
                "Access to %s returned error '%s'", self._api_url, type(err).__name__
            )
            return False
        except ValueError:
            _LOGGER.exception("Unable to parse json response from %s", self._api_url)
            return False
        return True

    def get_current_seadata(self):
        """Get the current havvarsel data."""
        if self.data is None:
            return {}

        return {
            "temperature": round(
                self.data["variables"][0]["datapoints"][0]["value"], 1
            ),
            "salinity": round(self.data["variables"][1]["datapoints"][0]["value"]),
            "time": datetime.datetime.fromtimestamp(
                int(self.data["variables"][0]["datapoints"][0]["raw_time"]) / 1000,
                tz=datetime.timezone.utc,
            ),
        }
