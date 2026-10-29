"""create initial student profile schema

Revision ID: 0001_initial
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "institutions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False, unique=True),
        sa.Column("institution_type", sa.String(length=40), nullable=False),
    )
    op.create_index("ix_institutions_institution_type", "institutions", ["institution_type"])
    op.create_table(
        "majors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("institution_id", sa.Integer(), sa.ForeignKey("institutions.id"), nullable=False),
    )
    op.create_table(
        "student_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("current_college_id", sa.Integer(), sa.ForeignKey("institutions.id"), nullable=False),
        sa.Column("anticipated_transfer_term", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "student_profile_targets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("student_profiles.id"), nullable=False),
        sa.Column("target_campus_id", sa.Integer(), sa.ForeignKey("institutions.id"), nullable=False),
        sa.Column("intended_major_id", sa.Integer(), sa.ForeignKey("majors.id"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("student_profile_targets")
    op.drop_table("student_profiles")
    op.drop_table("majors")
    op.drop_index("ix_institutions_institution_type", table_name="institutions")
    op.drop_table("institutions")
