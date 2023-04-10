import datetime

import pint
import httpx

from sp_project.lib.http_client import RequestWrapper


u = pint.get_application_registry()


class OpenWeatherClient(RequestWrapper):
    """Handles the OpenWeather - Request"""

    def __init__(self, api_key: str, api_url: str = "https://api.openweathermap.org/data/3.0"):
        """Instantiate the class; it takes the parameters api_url and api_key"""

        # Instantiate a new httpx-AsyncClient and tells server to send JSON-File back
        self._client = httpx.AsyncClient(headers={"Accept": "application/json"})

        # Must-Have-Parameters
        self._api_url = api_url
        self._api_key = api_key

    async def __aenter__(self):
        await self._client.__aenter__()
        return self

    # When an exception happens inside the `with`-Block
    # `__aexit__` will receive Information about the exception in its arguments.
    # The httpx-AsyncClient's `__aexit__`-Methode will be invoked and will decide if the exception is to propagete
    # (It always decides to propagate)
    # `__aexit__' closes the connection
    async def __aexit__(self, exc_type, exc_value, exc_tb):
        return await self._client.__aexit__(exc_type, exc_value, exc_tb)


    async def standard_request(self, method, url, *args, **kw):
        """handels the usual type of request with api_key and standard response"""

        params = kw.pop("params", {}) #
        assert params.setdefault("appid", self._api_key) == self._api_key # raises exception if the api_key isn't correct
        full_url = f"{self._api_url}/{url}"
        response = await self._client.request(method, full_url, *args, params=params, **kw) # httpx.request()-Methode

        response.raise_for_status() # if not http 200 -> raise an exception
        ret = response.json() # if response-code is 200, we want to know everything in form of a json-document
        return ret

    # Defines the weatherstation with the coordinates as parameters
    def station_at(self, lat, lon):
        return WeatherStation(self, lat, lon)


# Handles a specific weatherstation

class WeatherStation(RequestWrapper):
    def __init__(self, client: OpenWeatherClient, lat: float, lon: float):
        self._client = client
        self.lat = lat
        self.lon = lon

    async def standard_request(self, method, url, *args, **kw):
        lat = self.lat
        lon = self.lon
        params = kw.pop("params", {})
        assert params.setdefault("lat", lat) == lat
        assert params.setdefault("lon", lon) == lon
        return await self._client.standard_request(method, url, *args, params=params, **kw)

    # Adds the Units
    _data_units = dict(
        temp=u.K,
        feels_like=u.K,
        pressure=u.hPa,
        #        humidity = u.percent,
        #        clouds = u.percent,
        dew_point=u.K,
        visibility=u.km,
        wind_speed=u.m / u.s,
        wind_gust=u.m / u.s,
        wind_deg=u.degree,
        rain=u.mm / u.hr,
        snow=u.mm / u.hr,
    )

    async def historic(self, ts: datetime.datetime, lang: str = "en"):
        assert ts.tzinfo is not None, "Naive timestamps are not supported"
        dt = int(round(ts.timestamp())) #ts.timestamp gives the UNIX-Timestamp corresponding to ts
        ret = await self.get("onecall/timemachine", params=dict(dt=dt, lang=lang, units="standard"))
        #ret["timezone_offset"] = datetime.timedelta(seconds=ret["timezone_offset"])

        # For all the Datapoints a matching Unit is attached
        for d in ret["data"]: # d is the complete 'data'-list-dictionary
            if False:
                for k, units in self._data_units.items(): #e.g. k is "temp" and units is 'u.K'
                    v = d.get(k) # goes in the dictionary "d" to the key "k" and gives back the value
                    if v is None:
                        continue
                    d[k] = u.Quantity(v, units)

            # for Sunrise and Sunset, instead of Unit is a Datetime object
            for k in "dt sunrise sunset".split():
                v = d.get(k)
                if v is None:
                    continue
                d[k] = datetime.datetime.utcfromtimestamp(v).replace(tzinfo=datetime.timezone.utc)
        return ret
