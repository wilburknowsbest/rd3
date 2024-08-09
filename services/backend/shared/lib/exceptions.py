import http.client

from fastapi.exceptions import HTTPException


class ErrorCategories(object):
    GENERAL = "GENERAL"
    VALIDATION = "VALIDATION"
    SECURITY = "SECURITY"


class BaseException(HTTPException):
    """
    A Generic Exception Class
    """

    STATUS_CODE = http.client.INTERNAL_SERVER_ERROR
    CATEGORY = ErrorCategories.GENERAL
    DEFAULT_MESSAGE = (
        "An internal server error has occurred.  Our technical team has been notified."
    )

    def __init__(self, message=None):
        if not isinstance(message, str):
            message = str(self.DEFAULT_MESSAGE)

        super().__init__(status_code=int(self.STATUS_CODE), detail=message)

    def __str__(self):
        return self.detail

    def content(self):
        return {"errors": {self.CATEGORY: self.detail}}


class ValidationException(BaseException):
    """
    Error describing when a request is not valid
    """

    STATUS_CODE = http.client.UNPROCESSABLE_ENTITY
    CATEGORY = ErrorCategories.VALIDATION
    DEFAULT_MESSAGE = "Invalid Request."

    def from_request_validation_errors(self, error_list):
        self.detail = ""
        for i in range(len(error_list)):
            error = error_list[i]
            if i != 0:
                self.detail += " "

            if error["type"] == "missing":
                self.detail += f"'{error['loc'][-1]}' is Required."
            else:
                self.detail += f"{error['msg']}: {error['loc'][-1]}"


class NotFoundException(BaseException):
    """
    Error describing when a request is not valid (403)
    """

    STATUS_CODE = http.client.NOT_FOUND
    CATEGORY = ErrorCategories.VALIDATION
    DEFAULT_MESSAGE = "Resource Not Found"


class ForbiddenException(BaseException):
    """
    Error describing when a request is not valid (403)
    """

    STATUS_CODE = http.client.FORBIDDEN
    CATEGORY = ErrorCategories.SECURITY
    DEFAULT_MESSAGE = "Forbidden Request."


class UnauthorizedException(BaseException):
    """
    Error describing when a request is not authorized
    """

    STATUS_CODE = http.client.UNAUTHORIZED
    CATEGORY = ErrorCategories.SECURITY
    DEFAULT_MESSAGE = "Request Unauthorized."


class ExternalCommunicationFailure(BaseException):
    """
    Error describing when we have failed to communicate with an external source
    """

    STATUS_CODE = http.client.SERVICE_UNAVAILABLE
    CATEGORY = ErrorCategories.GENERAL
    DEFAULT_MESSAGE = "FAILED TO COMMUNICATE WITH AN EXTERNAL RESOURCE"
