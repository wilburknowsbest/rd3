
from home.settings import settings
from shared.lib.exceptions import (
    BaseException,
    ValidationException,
)

from fastapi import FastAPI, Request, Response, Depends, APIRouter
from fastapi.routing import APIRoute
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse

from typing import (
    Any,
    Callable,
    Literal,
    Optional,
)

import datetime
import uuid
import time
import json
import logging

logger = logging.getLogger(__name__)


class FastRoute(APIRoute):
    PATH: str
    METHOD: Literal["GET", "PUT", "POST", "DELETE"]
    SUMMARY: Optional[str] = None
    DESCRIPTION: Optional[str] = None
    RESPONSE_MODEL: Any = None

    @classmethod
    def register(cls, app: FastAPI) -> None:
        # Assemble token dependencies
        dependencies = []
        # if not cls.PUBLIC:
        #     dependencies.append(Depends(api_token_header))
        #     if settings.env != 'local':
        #         dependencies.append(Depends(csrf_token_header))

        try:
            # Making a router per route seems crazy,
            # but it allows us to have a different route class for each
            router = APIRouter(
                route_class=cls,
                prefix=f"/{settings.service_name}/v1"
            )
            router.add_api_route(
                path=cls.PATH,
                endpoint=cls.endpoint,
                methods=[cls.METHOD],
                dependencies=dependencies,
                summary=cls.SUMMARY,
                description=cls.DESCRIPTION,
                response_model=cls.RESPONSE_MODEL,
            )
            app.include_router(router)
        except Exception:
            logger.error(f"Failed to add route {cls.PATH}")
            raise

    @classmethod
    async def endpoint(cls, *args, **kwargs) -> dict:
        raise NotImplementedError("endpoint not implemented")

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                await self._before_request(request)

                # if not self.PUBLIC:
                #     await self._route_auth(request)

                response = await original_route_handler(request)

            except json.decoder.JSONDecodeError:
                error = ValidationException("Invalid JSON")
                logger.exception(error)
                response = JSONResponse(
                    status_code=error.STATUS_CODE, content=error.content()
                )

            except RequestValidationError as exc:
                error = ValidationException()
                error.from_request_validation_errors(exc.errors())
                logger.exception(error)
                response = JSONResponse(
                    status_code=error.STATUS_CODE, content=error.content()
                )

            except HTTPException as exc:
                logger.exception(exc)
                response = JSONResponse(
                    status_code=exc.STATUS_CODE, content=exc.content()
                )

            except Exception as exc:
                logger.exception(exc)
                error = BaseException()
                response = JSONResponse(
                    status_code=error.STATUS_CODE, content=error.content()
                )

            finally:
                return await self._after_request(request, response)

        return custom_route_handler

    async def _before_request(self, request: Request):
        """
        Save anything necessary before the request on the state
        """

        request.state.request_id = str(uuid.uuid4())
        request.state.request_start_time = datetime.datetime.now()

    async def _after_request(self, request: Request, response: Response):
        """
        Log the Request/Response
        """

        if isinstance(response, RedirectResponse):
            return response

        content_type = response.headers["content-type"]
        if (
            "text/csv" in content_type
            or "text/xml" in content_type
            or "image" in content_type
            or self._skip_request_logging(request)
        ):
            return response

        # Get response body
        if isinstance(response, JSONResponse):
            response_body = response.body
        else:
            # Load the streaming response into memory hmmm
            response_body = [chunk async for chunk in response.body_iterator][0]

        try:
            if isinstance(response_body, bytes):
                response_body = response_body.decode()
            response_body = json.loads(response_body)
        except Exception:
            pass

        # Total elapsed response time
        response_total_ms = int(
            (
                datetime.datetime.now() - request.state.request_start_time
            ).total_seconds()
            * 1000
        )

        # Get request body
        request_body = await request.body()
        request_form = await request.form()
        if request_body:
            request_data = str(request_body)
        elif request_form:
            request_data = str(dict(request_form))
        else:
            request_data = ""

        # TODO: fix logging and set this up
        print(
            {
                "route": request.url.path,
                "method": request.method,
                "service": settings.service_name,
                "request_id": request.state.request_id,
                "timestamp": time.strftime("%Y-%b-%d %H:%M:%S"),
                "from": request.client.host,
                "request_headers": dict(request.headers),
                "request_body": request_data,
                "response_headers": dict(response.headers),
                "response_status": response.status_code,
                "response_total_ms": response_total_ms,
                "response_body": response_body,
            }
        )

        return response

    def _skip_request_logging(self, request):
        return any(
            (
                x in request.url.path
                for x in [
                    "/docs",
                    "/redoc",
                    "/openapi.json",
                    "/status",
                ]
            )
        )