"""Load local configuration without logging connection strings or passwords."""

import os
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError

ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


def get_database_url() -> URL:
    # Shell variables take precedence; reading .env does not mutate the process.
    value = os.environ.get("DATABASE_URL")
    if value is None:
        value = dotenv_values(ENV_FILE).get("DATABASE_URL")
    if not value or not value.strip():
        raise RuntimeError("DATABASE_URL is required. Configure it in the root .env or environment.")
    try:
        url = make_url(value)
    except ArgumentError:
        raise RuntimeError("DATABASE_URL must be a valid PostgreSQL connection URL.") from None
    if url.drivername != "postgresql+psycopg" or not all(
        (url.username, url.password, url.host, url.database)
    ):
        raise RuntimeError("DATABASE_URL requires postgresql+psycopg, a user, password, host, and database.")
    return url
