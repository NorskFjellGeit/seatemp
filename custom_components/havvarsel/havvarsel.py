from urllib.parse import urlencode
from requests import get
from datetime import datetime, timezone


class HavvarselDataResult(object):
    temp: float
    salt: int
    time: datetime

    def __init__(
        self, temp: float = 0.0, salt: int = 0, time: datetime = datetime.utcnow()
    ) -> None:
        self.temp = temp
        self.salt = salt
        self.time = time

    def __repr__(self) -> str:
        return repr(self.__dict__)


class HavvarselData:

    HAVVARSEL_URL = "https://api.havvarsel.no/apps/havvarsel/v1/get_projection"

    after: datetime = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    before: datetime = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    lat: float = 60.39323
    lon: float = 5.3245

    def __init__(
        self,
        after=None,
        before=None,
        lat=None,
        lon=None,
        variable=None,
    ) -> None:
        if after:
            self.after = after
        if before:
            self.before = before
        if lat:
            self.lat = lat
        if lon:
            self.lon = lon

    def _params(self) -> dict:
        return {
            "after": self.after,
            "before": self.before,
            "lat": self.lat,
            "lon": self.lon,
            "variable": "temperature,salinity",
        }

    def get_data(self):
        headers = {
            "User-Agent": "Home Assistant Integration",
        }
        try:
            req = get(self.HAVVARSEL_URL, params=self._params(), headers=headers)
            req.raise_for_status()
            jsondata = req.json()
            return HavvarselDataResult(
                temp=round(jsondata["variables"][0]["datapoints"][0]["value"], 1),
                salt=round(jsondata["variables"][1]["datapoints"][0]["value"]),
                time=datetime.fromtimestamp(
                    int(jsondata["variables"][0]["datapoints"][0]["raw_time"]) / 1000,
                    tz=timezone.utc,
                ),
            )
        except Exception as e:
            return HavvarselDataResult()


if __name__ == "__main__":
    hv = HavvarselData()
    print(hv.get_data())