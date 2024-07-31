import enum

from sqlalchemy.orm import Mapped, mapped_column

from config.orm     import db


class UserRoleEnum(enum.Enum):
    Audience = "audience"
    Uploader = "uploader"


class User(db.Model):
    id:           Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    oauth_sub:    Mapped[str] = mapped_column(nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(nullable=False)
    email:        Mapped[str] = mapped_column(default="")
    user_role:    Mapped[str] = mapped_column(nullable=False, default=UserRoleEnum.Audience.value)

