"""
A User model, used for authentication.
"""

from __future__ import annotations

import datetime
import hashlib
import logging
import secrets
import typing as t

from piccolo.columns import Boolean, Secret, Timestamp, Varchar
from piccolo.columns.column_types import UUID, Text, Timestamptz
from piccolo.columns.defaults.timestamptz import TimestamptzNow
from piccolo.columns.defaults.uuid import UUID4
from piccolo.table import Table

logger = logging.getLogger(__name__)


class User(Table, tablename="users"):
    """
    Provides a basic user, with authentication support.
    """

    id = UUID(default=UUID4)
    active = Boolean(default=True)
    email = Varchar(length=255, unique=True)
    password = Secret(length=255)
    first_name = Text(null=True)
    last_name = Text(null=True)
    last_login = Timestamp(
        null=True,
        default=None,
        required=False,
        help_text="When this user last logged in.",
    )
    created_at = Timestamptz(default=TimestamptzNow)
    updated_at = Timestamptz(default=TimestamptzNow)

    _min_password_length = 6
    _max_password_length = 128
    # The number of hash iterations recommended by OWASP:
    # https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html#pbkdf2
    _pbkdf2_iteration_count = 600_000

    def __init__(self, **kwargs):
        # Generating passwords upfront is expensive, so might need reworking.
        password = kwargs.get("password", None)
        if password:
            if not password.startswith("pbkdf2_sha256"):
                kwargs["password"] = self.__class__.hash_password(password)
        super().__init__(**kwargs)

    @classmethod
    def get_salt(cls):
        return secrets.token_hex(16)

    ###########################################################################

    @classmethod
    def _validate_password(cls, password: str):
        """
        Validate the raw password. Used by :meth:`update_password` and
        :meth:`create_user`.

        :param password:
            The raw password e.g. ``'hello123'``.
        :raises ValueError:
            If the password fails any of the criteria.

        """
        if not password:
            raise ValueError("A password must be provided.")

        if len(password) < cls._min_password_length:
            raise ValueError(
                f"The password is too short. (min {cls._min_password_length})"
            )

        if len(password) > cls._max_password_length:
            raise ValueError(
                f"The password is too long. (max {cls._max_password_length})"
            )

        if password.startswith("pbkdf2_sha256"):
            logger.warning(
                "Tried to create a user with an already hashed password."
            )
            raise ValueError("Do not pass a hashed password.")

    ###########################################################################

    @classmethod
    async def update_password(cls, user_id: str, password: str):
        """
        The password is the raw password string e.g. ``'password123'``.
        The user ID
        """
        cls._validate_password(password=password)

        password = cls.hash_password(password)
        await cls.update({cls.password: password}).where(cls.id == user_id).run()

    ###########################################################################

    @classmethod
    def hash_password(
        cls, password: str, salt: str = "", iterations: t.Optional[int] = None
    ) -> str:
        """
        Hashes the password, ready for storage, and for comparing during
        login.

        :raises ValueError:
            If an excessively long password is provided.

        """
        if len(password) > cls._max_password_length:
            logger.warning("Excessively long password provided.")
            raise ValueError("The password is too long.")

        if not salt:
            salt = cls.get_salt()

        if iterations is None:
            iterations = cls._pbkdf2_iteration_count

        hashed = hashlib.pbkdf2_hmac(
            "sha256",
            bytes(password, encoding="utf-8"),
            bytes(salt, encoding="utf-8"),
            iterations,
        ).hex()
        return f"pbkdf2_sha256${iterations}${salt}${hashed}"

    def __setattr__(self, name: str, value: t.Any):
        """
        Make sure that if the password is set, it's stored in a hashed form.
        """
        if name == "password" and not value.startswith("pbkdf2_sha256"):
            value = self.__class__.hash_password(value)

        super().__setattr__(name, value)

    @classmethod
    def split_stored_password(cls, password: str) -> t.List[str]:
        elements = password.split("$")
        if len(elements) != 4:
            raise ValueError("Unable to split hashed password")
        return elements

    ###########################################################################

    @classmethod
    async def login(cls, email: str, password: str) -> t.Optional[int]:
        """
        Make sure the user exists and the password is valid. If so, the
        ``last_login`` value is updated in the database.

        :returns:
            The id of the user if a match is found, otherwise ``None``.

        """
        if len(email) > cls.email.length:
            logger.warning("Excessively long email provided.")
            return None

        if len(password) > cls._max_password_length:
            logger.warning("Excessively long password provided.")
            return None

        response = (
            await cls.select(cls._meta.primary_key, cls.password)
            .where(cls.email == email)
            .first()
            .run()
        )
        if not response:
            # No match found. We still call hash_password
            # here to mitigate the ability to enumerate
            # users via response timings
            # TODO: could alos just SLEEP
            cls.hash_password(password)
            return None

        if not response["active"]:
            logger.warning("User is not active")
            return None

        stored_password = response["password"]

        algorithm, iterations_, salt, hashed = cls.split_stored_password(
            stored_password
        )
        iterations = int(iterations_)

        if cls.hash_password(password, salt, iterations) == stored_password:
            # If the password was hashed in an earlier Piccolo version, update
            # it so it's hashed with the currently recommended number of
            # iterations:
            if iterations != cls._pbkdf2_iteration_count:
                await cls.update_password(response["id"], password)

            await cls.update({cls.last_login: datetime.datetime.now()}).where(
                cls.email == email
            )
            return response["id"]
        else:
            return None

    ###########################################################################

    @classmethod
    async def create_user(
        cls, email: str, password: str, **extra_params
    ) -> User:
        """
        Creates a new user, and saves it in the database. It is recommended to
        use this rather than instantiating and saving ``User`` directly, as
        we add extra validation.

        :raises ValueError:
            If the email or password is invalid.
        :returns:
            The created ``User`` instance.

        """
        if not email:
            raise ValueError("A email must be provided.")

        cls._validate_password(password=password)

        user = cls(email=email, password=password, **extra_params)
        await user.save()
        return user