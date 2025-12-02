from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Background(Base):
    __tablename__ = "backgrounds"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    camera_count = Column(Integer, nullable=False, comment="相机数")
    tos_path = Column(String, nullable=False, comment="tos路径")
    notes = Column(Text, nullable=True, comment="备注")
    status = Column(String, nullable=False, default="uploading", comment="状态: uploading/ready/failed")
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", backref="backgrounds")

