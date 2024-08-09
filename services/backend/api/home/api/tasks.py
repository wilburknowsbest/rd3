
from shared.lib.routes.crud import CrudRoutes
from shared.tables.task import Task


class TaskRoutes(CrudRoutes):
    PATH = "/tasks"
    DB_MODEL = Task