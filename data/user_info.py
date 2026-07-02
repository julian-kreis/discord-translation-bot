import aiosqlite
from datetime import datetime, timezone

DB_FILE = "user_info.db"


# ----------------------------
# INIT
# ----------------------------
async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("PRAGMA journal_mode=WAL;")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id INTEGER PRIMARY KEY,
                preferred_language TEXT,
                preferred_language_send TEXT,
                num_translations_today INTEGER NOT NULL DEFAULT 0,
                subscription_tier INTEGER NOT NULL DEFAULT 0,
                last_translation_reset TEXT NOT NULL DEFAULT ''
            )
        """)

        await db.commit()


# ----------------------------
# HELPERS
# ----------------------------
def get_utc_today() -> str:
    """Return current UTC date as YYYY-MM-DD."""
    return datetime.now(timezone.utc).date().isoformat()


async def ensure_user_exists(user_id: int):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            INSERT OR IGNORE INTO user_preferences (
                user_id,
                preferred_language,
                preferred_language_send,
                num_translations_today,
                subscription_tier,
                last_translation_reset
            )
            VALUES (?, NULL, NULL, 0, 0, '')
        """, (user_id,))
        await db.commit()


async def _reset_user_if_new_day(db, user_id: int):
    """Reset user counter if UTC day changed."""
    today = get_utc_today()

    await db.execute("""
        UPDATE user_preferences
        SET num_translations_today = 0,
            last_translation_reset = ?
        WHERE user_id = ?
          AND last_translation_reset != ?
    """, (today, user_id, today))


# ----------------------------
# GETTERS
# ----------------------------
async def get_num_translations_today(user_id: int) -> int:
    await ensure_user_exists(user_id)

    async with aiosqlite.connect(DB_FILE) as db:
        await _reset_user_if_new_day(db, user_id)

        async with db.execute("""
            SELECT num_translations_today
            FROM user_preferences
            WHERE user_id = ?
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def get_preferred_language(user_id: int) -> str | None:
    await ensure_user_exists(user_id)

    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("""
            SELECT preferred_language
            FROM user_preferences
            WHERE user_id = ?
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0]


async def get_preferred_language_send(user_id: int) -> str | None:
    await ensure_user_exists(user_id)

    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("""
            SELECT preferred_language_send
            FROM user_preferences
            WHERE user_id = ?
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0]
        
async def get_num_translations_today(user_id: int) -> int:
    """Get the user's translation count for the current UTC day."""
    await ensure_user_exists(user_id)

    async with aiosqlite.connect(DB_FILE) as db:
        # ensure it's up to date for today (lazy reset)
        await _reset_user_if_new_day(db, user_id)

        async with db.execute("""
            SELECT num_translations_today
            FROM user_preferences
            WHERE user_id = ?
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


# ----------------------------
# SETTERS
# ----------------------------
async def set_preferred_language(user_id: int, language: str):
    await ensure_user_exists(user_id)

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            UPDATE user_preferences
            SET preferred_language = ?
            WHERE user_id = ?
        """, (language, user_id))
        await db.commit()


async def set_preferred_language_send(user_id: int, language: str):
    await ensure_user_exists(user_id)

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            UPDATE user_preferences
            SET preferred_language_send = ?
            WHERE user_id = ?
        """, (language, user_id))
        await db.commit()


# ----------------------------
# TRANSLATION COUNTER
# ----------------------------
async def increment_num_translations_today(user_id: int):
    await ensure_user_exists(user_id)

    today = get_utc_today()

    async with aiosqlite.connect(DB_FILE) as db:
        await _reset_user_if_new_day(db, user_id)

        await db.execute("""
            UPDATE user_preferences
            SET num_translations_today = num_translations_today + 1,
                last_translation_reset = ?
            WHERE user_id = ?
        """, (today, user_id))

        await db.commit()