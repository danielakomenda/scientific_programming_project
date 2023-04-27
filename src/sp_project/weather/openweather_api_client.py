import datetime

import httpx


class OpenWeatherClient:
    """Handles the OpenWeather-Request"""

    def __init__(self, api_key: str, api_url: str="https://api.openweathermap.org/data/3.0"):
        """Instantiate the class; it takes the parameters api_url and api_key"""

        # Instantiate a new httpx-AsyncClient and tells server to send JSON-File back
        self._client = httpx.AsyncClient(
            headers={"Accept": "application/json"},
            base_url=api_url,
            params=dict(appid = api_key),
        )


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
    def station_at(self, lon, lat):
        return WeatherStation(self, lon=lon, lat=lat)



class WeatherStation:
    """Handels a specific location defined by latitude and longitude"""

    def __init__(self, client: OpenWeatherClient, lon: float, lat: float):
        """Constructor"""
        self._client = client
        self.lon = lon
        self.lat = lat


    async def historic(self, ts: datetime.datetime, lang: str = "en"):
        assert ts.tzinfo is not None, "Naive timestamps are not supported"
        dt = int(round(ts.timestamp())) #ts.timestamp gives the UNIX-Timestamp corresponding to ts
        ret = await self._client._client.get(
            "onecall/timemachine", 
            params=dict(
                dt=dt, 
                lang=lang, 
                units="standard",
                lon=self.lon,
                lat=self.lat,
            ),
        )
        ret.raise_for_status() # turns http-Errors into exceptions
        ret = ret.json() # if there is no Error, the response is a json-document

        # For all the Datapoints a matching Unit is attached
        for d in ret["data"]: # d is the complete 'data'-list-dictionary
            # for Sunrise and Sunset we convert the ISO-String to a Datetime object
            for k in "dt sunrise sunset".split():
                v = d.get(k)
                if v is None:
                    continue
                d[k] = datetime.datetime.utcfromtimestamp(v).replace(tzinfo=datetime.timezone.utc)
        return ret
