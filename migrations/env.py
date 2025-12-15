from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from config import BaseConfig

# ---------------------------------------------------------------------------
# Garante que o diretório do projeto esteja no sys.path
# (para o import "books.models" funcionar mesmo quando o Alembic
#  for executado a partir de outros diretórios).
# ---------------------------------------------------------------------------

config = context.config

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from books.models import Base  # noqa: E402  (importa após ajustar sys.path)

# ---------------------------------------------------------------------------
# Alembic Config object
# ---------------------------------------------------------------------------

config = context.config

app_url = BaseConfig.SQLALCHEMY_DATABASE_URI
db_url = os.environ.get("DATABASE_URL")
if not db_url:
    #localhost
    config.set_main_option("sqlalchemy.url", app_url)
else:
    #docker
    config.set_main_option("sqlalchemy.url", db_url)

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# METADATA DOS MODELOS - usado pelo autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
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
    """Run migrations in 'online' mode."""
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