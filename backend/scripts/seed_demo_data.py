from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.db.session import SessionLocal
from app.models.institution import Institution
from app.models.major import Major


DEMO_INSTITUTIONS = [
    ("Santa Monica College", "community_college"),
    ("Pasadena City College", "community_college"),
    ("University of California, Los Angeles", "university"),
    ("California State University, Long Beach", "university"),
]
DEMO_MAJORS = ["Computer Science", "Business Administration", "Psychology"]


def seed(session_factory=None) -> None:
    """Insert demonstration options; uniqueness also protects concurrent invocations."""
    with (session_factory or SessionLocal)() as db:
        insert = pg_insert if db.get_bind().dialect.name == "postgresql" else sqlite_insert
        institutions = {}
        for name, institution_type in DEMO_INSTITUTIONS:
            db.execute(insert(Institution).values(name=name, institution_type=institution_type)
                       .on_conflict_do_nothing(index_elements=["name"]))
            institution = db.scalar(select(Institution).where(Institution.name == name))
            institutions[name] = institution

        for university_name in [name for name, kind in DEMO_INSTITUTIONS if kind == "university"]:
            university = institutions[university_name]
            for major_name in DEMO_MAJORS:
                db.execute(
                    insert(Major).values(name=major_name, institution_id=university.id)
                    .on_conflict_do_nothing(index_elements=["institution_id", "name"])
                )
        db.commit()
        print("Demo catalog data is ready.")


if __name__ == "__main__":
    seed()
