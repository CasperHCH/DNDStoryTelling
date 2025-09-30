from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from app.models.database import Base
from app.config import get_settings
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
import asyncio

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    return get_settings().DATABASE_URL

def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = create_async_engine(
        configuration["sqlalchemy.url"],
        poolclass=pool.NullPool,
    )

    async def do_run_migrations():
        async with connectable.connect() as connection:
            await connection.run_sync(
                lambda conn: context.configure(
                    connection=conn, target_metadata=target_metadata
                )
            )
            await connection.run_sync(lambda conn: context.run_migrations())

    asyncio.run(do_run_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()