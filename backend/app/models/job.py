from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="pending")
    parameters = Column(Text, nullable=True)
    tos_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    video = relationship("Video", backref="jobs")
    owner = relationship("User", backref="jobs")
