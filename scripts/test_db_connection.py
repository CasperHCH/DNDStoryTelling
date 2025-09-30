import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_db_connection():
    db_url = "postgresql+asyncpg://user:password@localhost/dndstory"
    engine = create_async_engine(db_url, echo=True)
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        print("Database connection successful.")
    except Exception as e:
        print(f"Database connection failed: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_db_connection())