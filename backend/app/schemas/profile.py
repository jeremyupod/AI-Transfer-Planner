from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator
import re

from app.schemas.catalog import InstitutionRead, MajorRead


class ProfileTargetCreate(BaseModel):
    target_campus_id: int = Field(gt=0, strict=True)
    intended_major_id: int = Field(gt=0, strict=True)


class StudentProfileCreate(BaseModel):
    current_college_id: int = Field(gt=0, strict=True)
    anticipated_transfer_term: str = Field(min_length=1, max_length=40)
    targets: list[ProfileTargetCreate] = Field(min_length=1, max_length=10)

    @field_validator("anticipated_transfer_term")
    @classmethod
    def validate_term(cls, value: str) -> str:
        value = " ".join(value.split()).title()
        if not re.fullmatch(r"(Fall|Winter|Spring|Summer) (20|21)\d{2}", value):
            raise ValueError("Use a season and four-digit year from 2000–2199, for example Fall 2027")
        return value

    @field_validator("targets")
    @classmethod
    def unique_targets(cls, targets: list[ProfileTargetCreate]) -> list[ProfileTargetCreate]:
        pairs = {(target.target_campus_id, target.intended_major_id) for target in targets}
        if len(pairs) != len(targets):
            raise ValueError("Each campus and major combination must be unique")
        return targets


class ProfileTargetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    target_campus: InstitutionRead
    intended_major: MajorRead


class StudentProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    current_college: InstitutionRead
    anticipated_transfer_term: str
    created_at: datetime
    targets: list[ProfileTargetRead]
