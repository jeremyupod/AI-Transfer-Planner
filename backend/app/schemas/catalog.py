from pydantic import BaseModel, ConfigDict


class InstitutionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    institution_type: str


class MajorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    institution_id: int
