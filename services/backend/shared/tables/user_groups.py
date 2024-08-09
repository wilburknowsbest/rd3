from __future__ import annotations

import secrets
import typing as t
from datetime import datetime, timedelta

from piccolo.columns import Integer, Serial, Timestamp, Varchar
from piccolo.columns.column_types import UUID, Text, Timestamptz
from piccolo.columns.defaults.timestamptz import TimestamptzNow
from piccolo.columns.defaults.uuid import UUID4
from piccolo.table import Table


class UserGroup(Table, tablename="user_groups"):
    id = UUID(default=UUID4)
    name = Text(null=False)
    created_at = Timestamptz(default=TimestamptzNow)
    updated_at = Timestamptz(default=TimestamptzNow)

