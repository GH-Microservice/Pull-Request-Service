from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime
from database.pull_request_database import PullRequestBASE
from datetime import datetime


class PullRequestModel(PullRequestBASE):
    __tablename__ = "pull_requests"

    id: Mapped[int] = mapped_column(Integer, index=True, primary_key=True)
    repository_id: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow())
    status: Mapped[str] = mapped_column(String, default="Not known")
    letter: Mapped[str] = mapped_column(String, nullable=True)
