from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from app.models import Base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///../data/db/ttlab.db")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # SQLite create_all does not add columns to an existing database.
        columns = await conn.execute(text("PRAGMA table_info(matches)"))
        existing = {row[1] for row in columns.fetchall()}
        if "progress" not in existing:
            await conn.execute(text("ALTER TABLE matches ADD COLUMN progress FLOAT NOT NULL DEFAULT 0"))
        if "progress_message" not in existing:
            await conn.execute(text("ALTER TABLE matches ADD COLUMN progress_message VARCHAR"))
        for column, sql_type in {
            "match_date": "DATETIME",
            "player_name": "VARCHAR",
            "opponent_name": "VARCHAR",
            "result": "VARCHAR",
            "score": "VARCHAR",
            "notes": "TEXT",
            "table_points": "TEXT",
            "custom_title": "VARCHAR",
        }.items():
            if column not in existing:
                await conn.execute(text(f"ALTER TABLE matches ADD COLUMN {column} {sql_type}"))

        rally_columns = await conn.execute(text("PRAGMA table_info(rallies)"))
        existing_rally = {row[1] for row in rally_columns.fetchall()}
        for column, sql_type in {
            "validation_status": "VARCHAR DEFAULT 'accepted'",
            "confidence": "FLOAT DEFAULT 0",
            "impact_count": "INTEGER DEFAULT 0",
            "user_marked_highlight": "BOOLEAN DEFAULT FALSE",
            "notes": "TEXT",
        }.items():
            if column not in existing_rally:
                await conn.execute(text(f"ALTER TABLE rallies ADD COLUMN {column} {sql_type}"))

        # Rallies created before V0.3 have no validation status. They were
        # already visible and should remain accepted after the migration.
        await conn.execute(
            text("UPDATE rallies SET validation_status = 'accepted' "
                 "WHERE validation_status IS NULL OR validation_status = ''")
        )
        await conn.execute(
            text("UPDATE rallies SET user_marked_highlight = 0 "
                 "WHERE user_marked_highlight IS NULL")
        )


async def get_db():
    async with async_session_maker() as session:
        yield session
