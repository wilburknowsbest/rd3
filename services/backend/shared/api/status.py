from shared.lib.routes.fast import FastRoute


class GetStatus(FastRoute):
    PATH = "/status"
    METHOD = "GET"
    SUMMARY = "Get Status Endpoint"

    @classmethod
    async def endpoint(cls):
        return {"status": "ok"}
