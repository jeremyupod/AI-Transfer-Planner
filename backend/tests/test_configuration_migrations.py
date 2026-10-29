from io import StringIO
from pathlib import Path
import shutil

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text

from app.db import config as settings

ROOT = Path(__file__).resolve().parents[2]


def migration_config():
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "backend/alembic"))
    return config


def test_missing_database_url_fails_without_fallback(monkeypatch, tmp_path):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(settings, "ENV_FILE", tmp_path / "missing.env")
    with pytest.raises(RuntimeError, match="DATABASE_URL is required"):
        settings.get_database_url()


def test_empty_environment_does_not_fall_back_to_file(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")
    with pytest.raises(RuntimeError, match="DATABASE_URL is required"):
        settings.get_database_url()


def test_encoded_password_migration_url(monkeypatch):
    # Synthetic URL: offline SQL generation never connects to a database.
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://example:sample%40value%25@localhost/example")
    assert settings.get_database_url().password == "sample@value%"
    config = migration_config()
    config.output_buffer = StringIO()
    command.upgrade(config, "0001_initial", sql=True)
    assert "CREATE TABLE student_profiles" in config.output_buffer.getvalue()


def test_generated_revision_is_loadable(tmp_path):
    (tmp_path / "versions").mkdir()
    shutil.copy(ROOT / "backend/alembic/script.py.mako", tmp_path / "script.py.mako")
    config = Config()
    config.set_main_option("script_location", str(tmp_path))
    script = command.revision(config, message="regression probe", rev_id="probe")
    loaded = ScriptDirectory.from_config(config).get_revision("probe").module
    assert loaded.revision == "probe"
    assert loaded.down_revision is None
    assert callable(loaded.upgrade) and callable(loaded.downgrade)
    assert script is not None


def test_full_migration_chain_matches_models():
    engine = create_engine("sqlite://")
    try:
        with engine.begin() as connection:
            config = migration_config()
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
            command.check(config)
            assert any(item["name"] == "uq_major_institution_name" for item in inspect(connection).get_unique_constraints("majors"))
            command.downgrade(config, "base")
            assert "student_profiles" not in inspect(connection).get_table_names()
    finally:
        engine.dispose()


def test_migration_refuses_duplicates_without_removing_records():
    engine = create_engine("sqlite://")
    try:
        with engine.begin() as connection:
            config = migration_config()
            config.attributes["connection"] = connection
            command.upgrade(config, "0001_initial")
            connection.execute(text("INSERT INTO institutions (id, name, institution_type) VALUES (1, 'Demo', 'university')"))
            connection.execute(text("INSERT INTO majors (name, institution_id) VALUES ('Demo Major', 1), ('Demo Major', 1)"))
            with pytest.raises(RuntimeError, match="Duplicate records in majors"):
                command.upgrade(config, "head")
            assert connection.scalar(text("SELECT count(*) FROM majors")) == 2
    finally:
        engine.dispose()
