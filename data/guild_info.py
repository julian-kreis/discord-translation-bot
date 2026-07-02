import aiosqlite
from datetime import datetime, timezone

DB_FILE = "guild_info.db"


# ----------------------------
# DB INIT
# ----------------------------
async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("PRAGMA journal_mode=WAL;")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS guild_info (
                guild_id INTEGER PRIMARY KEY,
                subscription_tier INTEGER NOT NULL DEFAULT 0,
                messages_today INTEGER NOT NULL DEFAULT 0,
                last_message_reset TEXT NOT NULL DEFAULT ''
            )
        """)

        await db.commit()


# ----------------------------
# HELPERS
# ----------------------------
def get_utc_today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


async def ensure_guild_exists(guild_id: int):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            INSERT OR IGNORE INTO guild_info (
                guild_id,
                subscription_tier,
                messages_today,
                last_message_reset
            )
            VALUES (?, 0, 0, '')
        """, (guild_id,))
        await db.commit()


async def _reset_guild_if_new_day(db, guild_id: int):
    """Lazy UTC-day reset for guild message counter."""
    today = get_utc_today()

    await db.execute("""
        UPDATE guild_info
        SET messages_today = 0,
            last_message_reset = ?
        WHERE guild_id = ?
          AND last_message_reset != ?
    """, (today, guild_id, today))


# ----------------------------
# GETTERS
# ----------------------------
async def get_subscription_tier(guild_id: int) -> int:
    await ensure_guild_exists(guild_id)

    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("""
            SELECT subscription_tier
            FROM guild_info
            WHERE guild_id = ?
        """, (guild_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def get_messages_today(guild_id: int) -> int:
    await ensure_guild_exists(guild_id)

    async with aiosqlite.connect(DB_FILE) as db:
        await _reset_guild_if_new_day(db, guild_id)

        async with db.execute("""
            SELECT messages_today
            FROM guild_info
            WHERE guild_id = ?
        """, (guild_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


# ----------------------------
# SETTERS
# ----------------------------
async def set_subscription_tier(guild_id: int, tier: int):
    await ensure_guild_exists(guild_id)

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            UPDATE guild_info
            SET subscription_tier = ?
            WHERE guild_id = ?
        """, (tier, guild_id))
        await db.commit()


# ----------------------------
# MESSAGE TRACKING
# ----------------------------
async def increment_messages_today(guild_id: int):
    await ensure_guild_exists(guild_id)

    today = get_utc_today()

    async with aiosqlite.connect(DB_FILE) as db:
        await _reset_guild_if_new_day(db, guild_id)

        await db.execute("""
            UPDATE guild_info
            SET messages_today = messages_today + 1,
                last_message_reset = ?
            WHERE guild_id = ?
        """, (today, guild_id))

        await db.commit()