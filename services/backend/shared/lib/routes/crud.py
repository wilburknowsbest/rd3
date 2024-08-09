
from home.settings import settings

from fastapi import FastAPI, Request, Response, Depends, APIRouter
from fastapi.routing import APIRoute
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse



import datetime
import uuid
import time
import json


import logging

logger = logging.getLogger(__name__)

from shared.lib.routes.fast import FastRoute
from piccolo.table import Table
import typing as t
from piccolo_api.crud.serializers import create_pydantic_model
from shared.lib.exceptions import NotFoundException



class CrudRoutes(FastRoute):
    PATH: str
    METHODS: t.List[t.Literal["INDEX", "GET", "PUT", "POST", "DELETE"]] = ["INDEX", "GET", "PUT", "POST", "DELETE"]
    DB_MODEL: Table

    @classmethod
    def register(cls, app: FastAPI) -> None:
        # Assemble token dependencies
        dependencies = []
        # if not cls.PUBLIC:
        #     dependencies.append(Depends(api_token_header))
        #     if settings.env != 'local':
        #         dependencies.append(Depends(csrf_token_header))

        response_model = create_pydantic_model(
            table=cls.DB_MODEL,
            include_default_columns=True,
            model_name="ResponseModel",
        )

        router = APIRouter(
            route_class=cls,
            prefix=f"/{settings.service_name}/v1"
        )
        for method in cls.METHODS:
            http_method = str(method)
            resp_model = response_model
            path = str(cls.PATH.rstrip("/"))

            if method == "INDEX":
                http_method = "GET"
                resp_model = t.List[resp_model]
            elif method in ["GET", "PUT", "DELETE"]:
                path += "/{pk}"

            try:
                router.add_api_route(
                    path=path,
                    endpoint=cls._get_crud(method),
                    methods=[http_method],
                    dependencies=dependencies,
                    summary=cls.SUMMARY,
                    description=cls.DESCRIPTION,
                    response_model=resp_model,
                )
            except Exception:
                logger.error(f"Failed to add route {method} -> {path}")
                raise

        app.include_router(router)

    @classmethod
    def _get_crud(cls, method: str) -> callable:
        if method == "INDEX":
            async def _index():
                return await cls.DB_MODEL.select().order_by(cls.DB_MODEL.id)

            return _index
        
        elif method == "POST":
            request_model = create_pydantic_model(
                table=cls.DB_MODEL,
                model_name="RequestModel",
            )

            async def _create(model: request_model):
                obj = cls.DB_MODEL(**model.dict())
                await obj.save()
                return obj.to_dict()

            return _create

        elif method == "GET":
            async def _get_by_id(pk: str):
                obj = await cls.DB_MODEL.objects().get(cls.DB_MODEL._meta.primary_key == pk)
                if not obj:
                    raise NotFoundException()

                return obj.to_dict()

            return _get_by_id
        
        elif method == "PUT":
            request_model = create_pydantic_model(
                table=cls.DB_MODEL,
                model_name="RequestModel",
            )

            async def _update_by_id(pk: str, model: request_model):
                obj = await cls.DB_MODEL.objects().get(cls.DB_MODEL._meta.primary_key == pk)
                if not obj:
                    raise NotFoundException()

                for key, value in model.dict().items():
                    setattr(obj, key, value)

                await obj.save()
                return obj.to_dict()

            return _update_by_id

        elif method == "DELETE":
            async def _delete_by_id(pk: str):
                obj = await cls.DB_MODEL.objects().get(cls.DB_MODEL._meta.primary_key == pk)
                if not obj:
                    raise NotFoundException()

                await obj.remove()

                return obj.to_dict()

            return _delete_by_id

        raise Exception(f"Method {method} Unsupported")
