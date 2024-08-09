
from shared.lib.routes.fast import FastRoute
from shared.lib.routes.crud import CrudRoutes

import os
import importlib
import inspect
import logging

logger = logging.getLogger(__name__)


def register_route_class(app):
    app.router.route_class = FastRoute


def register_routes(app):
    route_files = [
        ".".join(root.split(os.sep) + [filename]).strip().removesuffix(".py")
        for root, subdirs, files in os.walk("home/api")
        for filename in files
        if (len(filename) > 3 and filename[-3:] == ".py" and filename != "__init__.py")
    ]
    route_files += [
        ".".join(root.split(os.sep) + [filename]).strip().removesuffix(".py")
        for root, subdirs, files in os.walk("shared/api")
        for filename in files
        if (len(filename) > 3 and filename[-3:] == ".py" and filename != "__init__.py")
    ]

    for route_file in route_files:
        try:
            module = importlib.import_module(route_file)
        except ModuleNotFoundError:
            logger.exception(f"Failed to import route file '{route_file}'")
            continue

        route_classes = []
        for attr in dir(module):
            attribute = getattr(module, attr)
            if (
                inspect.isclass(attribute)
                and attribute != FastRoute
                and attribute != CrudRoutes
                and issubclass(attribute, FastRoute)
            ):
                route_classes.append(attribute)

        for route_class in route_classes:
            route_class.register(app)
