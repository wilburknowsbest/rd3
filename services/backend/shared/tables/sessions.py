from __future__ import annotations

import secrets
import typing as t
from datetime import datetime, timedelta

from piccolo.columns import Integer, Serial, Timestamp, Varchar
from piccolo.columns.defaults.timestamp import TimestampOffset
from piccolo.columns.column_types import UUID, Text, Timestamptz
from piccolo.columns.defaults.timestamptz import TimestamptzNow
from piccolo.columns.defaults.uuid import UUID4

from piccolo.table import Table
from piccolo.utils.sync import run_sync

from shared.tables.users import User


class Session(Table, tablename="sessions"):
    """
    Use this table, or inherit from it, to create a session store.
    """

    id = UUID(default=UUID4)

    #: Stores the user ID.
    user_id: UUID = ForeignKey(User, null=False)

    #: Stores the expiry date for this session.
    expiry_date: Timestamp = Timestamp(
        default=TimestampOffset(hours=1), null=False
    )

    #: We set a hard limit on the expiry date - it can keep on getting extended
    #: up until this value, after which it's best to invalidate it, and either
    #: require login again, or just create a new session token.
    max_expiry_date: Timestamp = Timestamp(
        default=TimestampOffset(days=7), null=False
    )
    created_at = Timestamptz(default=TimestamptzNow)
    updated_at = Timestamptz(default=TimestamptzNow)

    @classmethod
    async def create_session(
        cls,
        user_id: UUID,
        expiry_date: t.Optional[datetime] = None,
        max_expiry_date: t.Optional[datetime] = None,
    ) -> SessionsBase:
        """
        Creates a session in the database.
        """
        while True:
            token = secrets.token_urlsafe(nbytes=32)
            if not await cls.exists().where(cls.token == token).run():
                break

        session = cls(id=token, user_id=user_id)
        if expiry_date:
            session.expiry_date = expiry_date
        if max_expiry_date:
            session.max_expiry_date = max_expiry_date

        await session.save().run()

        return session

    @classmethod
    async def get_user_id(
        cls, token: str, increase_expiry: t.Optional[timedelta] = None
    ) -> t.Optional[int]:
        """
        Returns the ``user_id`` if the given token is valid, otherwise
        ``None``.

        :param increase_expiry:
            If set, the ``expiry_date`` will be increased by the given amount
            if it's close to expiring. If it has already expired, nothing
            happens. The ``max_expiry_date`` remains the same, so there's a
            hard limit on how long a session can be used for.
        """
        session = await cls.objects().where(cls.id == token).first().run()

        if not session:
            return None

        now = datetime.now()
        if (session.expiry_date > now) and (session.max_expiry_date > now):
            if increase_expiry and (
                t.cast(datetime, session.expiry_date) - now < increase_expiry
            ):
                session.expiry_date = (
                    t.cast(datetime, session.expiry_date) + increase_expiry
                )
                await session.save().run()

            return t.cast(t.Optional[int], session.user_id)
        else:
            return None

    @classmethod
    async def remove_session(cls, token: str):
        """
        Deletes a matching session from the database.
        """
        await cls.delete().where(cls.id == token).run()
