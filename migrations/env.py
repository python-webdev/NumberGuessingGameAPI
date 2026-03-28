# pyright: reportAttributeAccessIssue=false
# mypy: disable-error-code=attr-defined
# ruff: noqa: I001

from importlib import import_module
from logging.config import fileConfig

from alembic.config import Config
from alembic import context as alembic_context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.database import Base

# Import all models so Alembic can detect metadata from mapped classes.
for module in ("app.models.player", "app.models.game", "app.models.guess"):
    import_module(module)

config: Config = getattr(alembic_context, "config")

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Pull DB URL from settings — not hardcoded
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    getattr(alembic_context, "configure")(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with getattr(alembic_context, "begin_transaction")():
        getattr(alembic_context, "run_migrations")()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        getattr(alembic_context, "configure")(
            connection=connection,
            target_metadata=target_metadata,
        )
        with getattr(alembic_context, "begin_transaction")():
            getattr(alembic_context, "run_migrations")()


if getattr(alembic_context, "is_offline_mode")():
    run_migrations_offline()
else:
    run_migrations_online()
