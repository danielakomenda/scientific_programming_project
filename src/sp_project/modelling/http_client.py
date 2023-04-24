import abc


class RequestWrapper(abc.ABC):

    # All Child-Classes must implement the Method standard_request
    @abc.abstractmethod
    async def standard_request(self, method, url, *args, **kw):
        pass

    # Method to get a request; all Child-Classes can use this Method
    async def get(self, *args, **kw):
        return await self.standard_request("get", *args, **kw)

    # Method to send a request; all Child-Classes can use this Method
    async def post(self, *args, **kw):
        return await self.standard_request("post", *args, **kw)
