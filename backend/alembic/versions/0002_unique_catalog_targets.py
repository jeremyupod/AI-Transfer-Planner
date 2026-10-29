"""Add uniqueness constraints without modifying existing records."""
from alembic import op
import sqlalchemy as sa

revision = "0002_unique_catalog_targets"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    # Refuse ambiguous existing data; never silently delete or merge student records.
    for name, columns in (
        ("majors", ("institution_id", "name")),
        ("student_profile_targets", ("profile_id", "target_campus_id", "intended_major_id")),
    ):
        table = sa.table(name, *(sa.column(column) for column in columns))
        duplicate = connection.execute(
            sa.select(sa.func.count()).select_from(table)
            .group_by(*(table.c[column] for column in columns))
            .having(sa.func.count() > 1).limit(1)
        ).first()
        if duplicate:
            raise RuntimeError(f"Duplicate records in {name}; review and resolve them before migrating. No records were removed.")
    with op.batch_alter_table("majors") as batch:
        batch.create_unique_constraint("uq_major_institution_name", ["institution_id", "name"])
    with op.batch_alter_table("student_profile_targets") as batch:
        batch.create_unique_constraint("uq_profile_campus_major", ["profile_id", "target_campus_id", "intended_major_id"])


def downgrade() -> None:
    with op.batch_alter_table("student_profile_targets") as batch:
        batch.drop_constraint("uq_profile_campus_major", type_="unique")
    with op.batch_alter_table("majors") as batch:
        batch.drop_constraint("uq_major_institution_name", type_="unique")
