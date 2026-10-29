from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.institution import Institution
from app.models.major import Major
from app.schemas.catalog import InstitutionRead, MajorRead

router = APIRouter(prefix="/api/v1", tags=["catalog"])


@router.get("/institutions", response_model=list[InstitutionRead])
def list_institutions(
    db: Annotated[Session, Depends(get_db)],
    institution_type: Literal["community_college", "university"] = Query("community_college"),
) -> list[Institution]:
    return list(db.scalars(select(Institution).where(Institution.institution_type == institution_type).order_by(Institution.name)))


@router.get("/campuses", response_model=list[InstitutionRead])
def list_campuses(db: Annotated[Session, Depends(get_db)]) -> list[Institution]:
    return list(db.scalars(select(Institution).where(Institution.institution_type == "university").order_by(Institution.name)))


@router.get("/majors", response_model=list[MajorRead])
def list_majors(
    db: Annotated[Session, Depends(get_db)],
    institution_id: Annotated[int | None, Query(gt=0)] = None,
) -> list[Major]:
    query = select(Major).order_by(Major.name)
    if institution_id is not None:
        query = query.where(Major.institution_id == institution_id)
    return list(db.scalars(query))
