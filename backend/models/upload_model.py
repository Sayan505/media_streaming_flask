import enum

from sqlalchemy.orm import Mapped, mapped_column

from config.orm     import db


class MediaStatusEnum(enum.Enum):
    NotQueued  = "notqueued"
    Queued     = "queued"
    Processing = "processing"
    Ready      = "ready"

class MediaTypeEnum(enum.Enum):
    Audio      = "audio"
    Video      = "video"


class Media(db.Model):
    id:                Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid:              Mapped[str] = mapped_column(nullable=False, unique=True)
    ownedby_oauth_sub: Mapped[str] = mapped_column(nullable=False)
    media_type:        Mapped[str] = mapped_column(nullable=False)
    title:             Mapped[str] = mapped_column(nullable=False)


class Pending(db.Model):
    id:                Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid:              Mapped[str] = mapped_column(nullable=False, unique=True)
    ownedby_oauth_sub: Mapped[str] = mapped_column(nullable=False)
    media_type:        Mapped[str] = mapped_column(nullable=False)
    title:             Mapped[str] = mapped_column(nullable=False)
    media_status:      Mapped[str] = mapped_column(nullable=False)

