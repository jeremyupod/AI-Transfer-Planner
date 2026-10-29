from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.major import Major
    from app.models.student_profile import StudentProfile, StudentProfileTarget


class Institution(Base):
    __tablename__ = "institutions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    institution_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)

    majors: Mapped[list["Major"]] = relationship(back_populates="institution")
    current_student_profiles: Mapped[list["StudentProfile"]] = relationship(
        back_populates="current_college",
        foreign_keys="StudentProfile.current_college_id",
    )
    profile_targets: Mapped[list["StudentProfileTarget"]] = relationship(
        back_populates="target_campus"
    )
