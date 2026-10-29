from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.institution import Institution
from app.models.major import Major
from app.models.student_profile import StudentProfile, StudentProfileTarget
from app.schemas.profile import StudentProfileCreate


def create_profile(db: Session, data: StudentProfileCreate) -> StudentProfile:
    college = db.get(Institution, data.current_college_id)
    if not college or college.institution_type != "community_college":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid community college")

    profile = StudentProfile(
        current_college_id=data.current_college_id,
        anticipated_transfer_term=data.anticipated_transfer_term,
    )
    for target in data.targets:
        campus = db.get(Institution, target.target_campus_id)
        major = db.get(Major, target.intended_major_id)
        if not campus or campus.institution_type != "university":
            raise HTTPException(status_code=400, detail="Invalid target campus")
        if not major or major.institution_id != campus.id:
            raise HTTPException(status_code=400, detail="Major is not associated with target campus")
        profile.targets.append(
            StudentProfileTarget(
                target_campus_id=campus.id,
                intended_major_id=major.id,
            )
        )

    db.add(profile)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Profile conflicts with current catalog data. Reload the catalog and try again.") from None
    return get_profile(db, profile.id)


def get_profile(db: Session, profile_id: int) -> StudentProfile:
    profile = db.scalar(
        select(StudentProfile)
        .where(StudentProfile.id == profile_id)
        .options(
            selectinload(StudentProfile.current_college),
            selectinload(StudentProfile.targets).selectinload(StudentProfileTarget.target_campus),
            selectinload(StudentProfile.targets).selectinload(StudentProfileTarget.intended_major),
        )
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return profile
