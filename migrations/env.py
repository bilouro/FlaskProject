from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from config import BaseConfig

config = context.config

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from books.models import Base  # noqa: E402

# ---------------------------------------------------------------------------
# URL do banco: SEMPRE usar DATABASE_URL (vindo do ambiente).
# Se não estiver definida, podemos usar BaseConfig como fallback opcional.
# ---------------------------------------------------------------------------

db_url = os.environ.get("DATABASE_URL")
if not db_url:
    # fallback opcional para uso local (ex.: alembic upgrade head rodando na sua máquina)
    db_url = BaseConfig.SQLALCHEMY_DATABASE_URI

# Sobrescreve a sqlalchemy.url do alembic.ini
config.set_main_option("sqlalchemy.url", db_url)

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()