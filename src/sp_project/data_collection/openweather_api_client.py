import datetime

import anyio
import httpx


class OpenWeatherClient:
    """Handles the OpenWeather-Request"""

    def __init__(self, api_key: str, api_url: str = "https://api.openweathermap.org/data/3.0"):
        """Instantiate the class; it takes the parameters api_url and api_key.
        api_url has already a default-value, so it only needs the api_key."""

        # Instantiate a new httpx-AsyncClient and tells server to send JSON-File back
        self._client = httpx.AsyncClient(
            headers={"Accept": "application/json"},
            base_url=api_url,
            params=dict(appid=api_key),
        )
        self._call_history = []

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

    async def _rate_limit(self):
        max_requests = 60
        max_request_time = 60
        while len(self._call_history) >= max_requests:
            deadline = anyio.current_time() - max_request_time
            if self._call_history[0] > deadline:
                await anyio.sleep_until(self._call_history[0]+max_request_time)
            # cleanup call-history; discard old entries
            del self._call_history[0]
        self._call_history.append(anyio.current_time())

    # Defines the weatherstation with the coordinates as parameters
    def station_at(self, lon, lat):
        return WeatherStation(self, lon=lon, lat=lat)


class WeatherStation:
    """Handels a specific location defined by latitude and longitude"""

    def __init__(self, client: OpenWeatherClient, *, lon: float, lat: float):
        """Constructor"""
        self._client = client
        self.lon = lon
        self.lat = lat

    async def historic(self, ts: datetime.datetime, lang: str = "en"):
        assert ts.tzinfo is not None, "Naive timestamps are not supported"
        dt = int(round(ts.timestamp()))  # ts.timestamp gives the UNIX-Timestamp corresponding to ts
        await self._client._rate_limit()
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
        ret.raise_for_status()  # turns http-Errors into exceptions
        ret = ret.json()  # if there is no Error, the response is a json-document

        # For all the Datapoints a matching Unit is attached
        for d in ret["data"]:  # d is the complete 'data'-list-dictionary

            # We convert the UNIX-Timestamp(seconds since 1970-01-01) to a Datetime object
            for k in "dt sunrise sunset".split():
                v = d.get(k)
                if v is None:
                    continue
                d[k] = datetime.datetime.utcfromtimestamp(v).replace(tzinfo=datetime.timezone.utc)
        return ret

    async def prediction(self, lang: str = "en"):
        await self._client._rate_limit()
        ret = await self._client._client.get(
            "onecall", 
            params=dict(
                exclude=["alert"],
                lang=lang, 
                units="standard",
                lon=self.lon,
                lat=self.lat,
            ),
        )
        ret.raise_for_status()  # turns http-Errors into exceptions
        ret = ret.json()  # if there is no Error, the response is a json-document

        def convert_timestamps(d: dict, keys: list[str]):
            """We convert the UNIX-Timestamp(seconds since 1970-01-01) to a Datetime object"""

            for k in keys:
                v = d.get(k)
                if v is None:
                    continue
                d[k] = datetime.datetime.utcfromtimestamp(v).replace(tzinfo=datetime.timezone.utc)

        # For all the Datapoints a matching Unit is attached
        for d in ret["daily"]:  # d is the complete 'data'-list-dictionary
            convert_timestamps(d, "dt sunrise sunset moonrise moonset".split())
            # split() splits the string and converts it to a list.

        for d in ret["minutely"]:  # d is the complete 'data'-list-dictionary
            convert_timestamps(d, ["dt"])

        for d in ret["hourly"]:  # d is the complete 'data'-list-dictionary
            convert_timestamps(d, ["dt"])
        
        convert_timestamps(ret["current"], "dt sunrise sunset".split())
        
        return ret
