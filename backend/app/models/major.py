from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Major(Base):
    __tablename__ = "majors"
    __table_args__ = (UniqueConstraint("institution_id", "name", name="uq_major_institution_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institutions.id"), nullable=False)

    institution = relationship("Institution", back_populates="majors")
    profile_targets = relationship("StudentProfileTarget", back_populates="intended_major")
