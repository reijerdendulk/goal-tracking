"""Initial schema with all tables and indexes

Revision ID: 001
Revises:
Create Date: 2024-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create extension
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # Create enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE activity_type AS ENUM ('run', 'hangout', 'work');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE run_workout_type AS ENUM ('easy','tempo','intervals','long','race','recovery');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE work_status AS ENUM ('idea','todo','in_progress','blocked','done');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$
    """)

    # Create activity table
    op.create_table(
        "activity",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "type",
            postgresql.ENUM("run", "hangout", "work", name="activity_type", create_type=False),
            nullable=False,
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "start_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "end_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column("duration_min", sa.Integer(), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_activity_type_start_at", "activity", ["type", "start_at"])
    op.create_index("idx_activity_start_at", "activity", ["start_at"])

    # Create run_detail table
    op.create_table(
        "run_detail",
        sa.Column(
            "activity_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("distance_meters", sa.Integer(), nullable=False),
        sa.Column("moving_time_sec", sa.Integer(), nullable=True),
        sa.Column("avg_pace_sec_per_km", sa.Integer(), nullable=True),
        sa.Column("elevation_gain_m", sa.Integer(), nullable=True),
        sa.Column("rpe", sa.Integer(), nullable=True),
        sa.Column(
            "workout_type",
            postgresql.ENUM(
                "easy", "tempo", "intervals", "long", "race", "recovery",
                name="run_workout_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("surface", sa.Text(), nullable=True),
        sa.Column("shoe", sa.Text(), nullable=True),
        sa.Column("splits", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["activity_id"],
            ["activity.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("activity_id"),
        sa.CheckConstraint("distance_meters > 0", name="check_distance_positive"),
        sa.CheckConstraint("rpe BETWEEN 1 AND 10", name="check_rpe_range"),
    )
    op.create_index("idx_run_detail_workout_type", "run_detail", ["workout_type"])
    op.create_index("idx_run_detail_distance_meters", "run_detail", ["distance_meters"])

    # Create hangout_detail table
    op.create_table(
        "hangout_detail",
        sa.Column(
            "activity_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("location_name", sa.Text(), nullable=True),
        sa.Column("location_type", sa.Text(), nullable=True),
        sa.Column("cost_estimate", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("mood", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["activity_id"],
            ["activity.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("activity_id"),
        sa.CheckConstraint("mood BETWEEN 1 AND 5", name="check_mood_range"),
    )

    # Create person table
    op.create_table(
        "person",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("handle", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create activity_participant table
    op.create_table(
        "activity_participant",
        sa.Column(
            "activity_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "person_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("role", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["activity_id"],
            ["activity.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["person.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("activity_id", "person_id"),
    )
    op.create_index(
        "idx_activity_participant_person_activity",
        "activity_participant",
        ["person_id", "activity_id"],
    )

    # Create work_detail table
    op.create_table(
        "work_detail",
        sa.Column(
            "activity_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("project", sa.Text(), nullable=False),
        sa.Column("area", sa.Text(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "idea", "todo", "in_progress", "blocked", "done",
                name="work_status",
                create_type=False,
            ),
            server_default=sa.text("'in_progress'"),
            nullable=False,
        ),
        sa.Column("artifact_link", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["activity_id"],
            ["activity.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("activity_id"),
    )
    op.create_index("idx_work_detail_project", "work_detail", ["project"])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("work_detail")
    op.drop_table("activity_participant")
    op.drop_table("person")
    op.drop_table("hangout_detail")
    op.drop_table("run_detail")
    op.drop_table("activity")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS work_status")
    op.execute("DROP TYPE IF EXISTS run_workout_type")
    op.execute("DROP TYPE IF EXISTS activity_type")
