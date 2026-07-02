import aiosqlite

DB_FILE = "user_preferences.db"


async def init_db():
    """Initializes the database and creates the user_preferences table."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("PRAGMA journal_mode=WAL;")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id INTEGER PRIMARY KEY,
                preferred_language TEXT,
                preferred_language_send TEXT
            )
        """)

        await db.commit()


async def get_preferred_language(user_id: int) -> str | None:
    """Get the user's preferred target language (translation output)."""
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute(
            "SELECT preferred_language FROM user_preferences WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def get_preferred_language_send(user_id: int) -> str | None:
    """Get the user's preferred input/source language (language they send in)."""
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute(
            "SELECT preferred_language_send FROM user_preferences WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def set_preferred_language(user_id: int, language: str):
    """Set or update the user's preferred target language."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            INSERT INTO user_preferences (user_id, preferred_language, preferred_language_send)
            VALUES (?, ?, COALESCE((SELECT preferred_language_send FROM user_preferences WHERE user_id = ?), NULL))
            ON CONFLICT(user_id) DO UPDATE SET
                preferred_language = excluded.preferred_language
        """, (user_id, language, user_id))
        await db.commit()


async def set_preferred_language_send(user_id: int, language: str):
    """Set or update the user's preferred source/input language."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            INSERT INTO user_preferences (user_id, preferred_language, preferred_language_send)
            VALUES (
                ?, 
                COALESCE((SELECT preferred_language FROM user_preferences WHERE user_id = ?), NULL),
                ?
            )
            ON CONFLICT(user_id) DO UPDATE SET
                preferred_language_send = excluded.preferred_language_send
        """, (user_id, user_id, language))
        await db.commit()