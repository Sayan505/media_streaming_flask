import enum

from sqlalchemy.orm import Mapped, mapped_column

from config.orm     import db


class UserRoleEnum(enum.Enum):
    Banned   = "banned"
    Listener = "listener"
    Artist   = "artist"
    Admin    = "admin"

class User(db.Model):
    __tablename__ = "users"

    id:          Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    oauth_sub:   Mapped[str] = mapped_column(nullable=False, unique=True)
    displayname: Mapped[str] = mapped_column(nullable=False)
    user_role:   Mapped[str] = mapped_column(nullable=False, default=UserRoleEnum.Listener.value)

