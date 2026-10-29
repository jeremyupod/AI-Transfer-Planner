from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    current_college_id: Mapped[int] = mapped_column(ForeignKey("institutions.id"), nullable=False)
    anticipated_transfer_term: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    current_college = relationship(
        "Institution",
        back_populates="current_student_profiles",
        foreign_keys=[current_college_id],
    )
    targets = relationship(
        "StudentProfileTarget",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="StudentProfileTarget.id",
    )


class StudentProfileTarget(Base):
    __tablename__ = "student_profile_targets"
    __table_args__ = (
        UniqueConstraint("profile_id", "target_campus_id", "intended_major_id", name="uq_profile_campus_major"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id"), nullable=False)
    target_campus_id: Mapped[int] = mapped_column(ForeignKey("institutions.id"), nullable=False)
    intended_major_id: Mapped[int] = mapped_column(ForeignKey("majors.id"), nullable=False)

    profile = relationship("StudentProfile", back_populates="targets")
    target_campus = relationship("Institution", back_populates="profile_targets")
    intended_major = relationship("Major", back_populates="profile_targets")
