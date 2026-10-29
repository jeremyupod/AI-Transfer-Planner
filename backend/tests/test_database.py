import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.models import Institution, Major, StudentProfile, StudentProfileTarget
from scripts.seed_demo_data import seed


def test_seed_is_repeatable_and_keeps_existing_ids(db_factory):
    seed(db_factory)
    with db_factory() as db:
        original = list(db.execute(select(Major.id, Major.name, Major.institution_id)))
    seed(db_factory)
    seed(db_factory)
    with db_factory() as db:
        assert db.scalar(select(func.count()).select_from(Institution)) == 4
        assert db.scalar(select(func.count()).select_from(Major)) == 6
        assert list(db.execute(select(Major.id, Major.name, Major.institution_id))) == original


def test_foreign_keys_are_enforced(db_factory):
    with db_factory() as db:
        db.add(Major(name="Invalid", institution_id=999))
        with pytest.raises(IntegrityError):
            db.commit()


def test_major_uniqueness(db_factory):
    seed(db_factory)
    with db_factory() as db:
        major = db.scalar(select(Major))
        db.add(Major(name=major.name, institution_id=major.institution_id))
        with pytest.raises(IntegrityError):
            db.commit()


def test_target_uniqueness(db_factory):
    seed(db_factory)
    with db_factory() as db:
        major = db.scalar(select(Major))
        college = db.scalar(select(Institution).where(Institution.institution_type == "community_college"))
        profile = StudentProfile(current_college_id=college.id, anticipated_transfer_term="Fall 2027")
        db.add(profile)
        db.flush()
        for _ in range(2):
            db.add(StudentProfileTarget(profile_id=profile.id, target_campus_id=major.institution_id, intended_major_id=major.id))
        with pytest.raises(IntegrityError):
            db.commit()
