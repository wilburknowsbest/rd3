
from shared.lib.routes.crud import CrudRoutes
from shared.tables.users import User


class UserRoutes(CrudRoutes):
    PATH = "/users"
    DB_MODEL = User