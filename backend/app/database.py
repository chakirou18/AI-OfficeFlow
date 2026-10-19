"""Explicit PostgreSQL configuration; no SQLite or embedded password fallback."""

import os

from sqlalchemy import URL, Engine, create_engine


def database_url() -> URL:
    password = os.environ.get("POSTGRES_PASSWORD", "")
    if not password or password == "REPLACE_WITH_A_GENERATED_LOCAL_PASSWORD":
        raise RuntimeError("Configure a local PostgreSQL password before startup.")
    return URL.create(
        "postgresql+psycopg",
        username=os.environ.get("POSTGRES_USER", "officeflow"),
        password=password,
        host=os.environ.get("POSTGRES_HOST", "db"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        database=os.environ.get("POSTGRES_DB", "officeflow"),
    )


def build_engine() -> Engine:
    return create_engine(
        database_url(),
        pool_pre_ping=True,
        pool_timeout=3,
        connect_args={"connect_timeout": 3},
        hide_parameters=True,
    )
