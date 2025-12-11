from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
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
    notes = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False, nullable=False, comment="是否公开")
    visible_to_user_ids = Column(Text, nullable=True, comment="管理员指定的可见用户ID列表，JSON格式")
    run_id = Column(String, nullable=True, comment="上游工作流 runId")
    created_at = Column(DateTime, default=datetime.utcnow)

    video = relationship("Video", backref="jobs")
    owner = relationship("User", backref="jobs")
