from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.profile import StudentProfileCreate, StudentProfileRead
from app.services.profile_service import create_profile, get_profile

router = APIRouter(prefix="/api/v1/student-profiles", tags=["student profiles"])


@router.post("", response_model=StudentProfileRead, status_code=status.HTTP_201_CREATED)
def create_student_profile(
    data: StudentProfileCreate,
    db: Annotated[Session, Depends(get_db)],
) -> StudentProfileRead:
    return create_profile(db, data)


@router.get("/{profile_id}", response_model=StudentProfileRead)
def read_student_profile(
    profile_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
) -> StudentProfileRead:
    return get_profile(db, profile_id)
