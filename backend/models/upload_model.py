import enum
from   uuid         import uuid4, UUID

from sqlalchemy.orm import Mapped, mapped_column

from config.orm     import db


class MediaStatusEnum(enum.Enum):
    Queued     = "queued"
    Processing = "processing"
    Ready      = "ready"
    Failed     = "failed"

class MediaTypeEnum(enum.Enum):
    Audio = "audio"
    Video = "video"

class Media(db.Model):
    id:                Mapped[int]  = mapped_column(primary_key=True, autoincrement=True)
    uuid:              Mapped[UUID] = mapped_column(nullable=False, default=uuid4)
    ownedby_oauth_sub: Mapped[str]  = mapped_column(nullable=False, unique=True)
    media_type:        Mapped[str]  = mapped_column(nullable=False)
    title:             Mapped[str]  = mapped_column(nullable=False)

