import json
import aiosqlite

DB_FILE = "translation_reply_cache.db"
TARGET_CACHED_MESSAGES = 100000
TRIGGER_THRESHOLD = int(TARGET_CACHED_MESSAGES * 1.1)

async def init_db():
    """Initializes the database and creates the translations table."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        # Changed reply_id to reply_ids (TEXT) to hold a JSON array
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cached_translations (
                message_id INTEGER,
                language TEXT,
                reply_ids TEXT,
                PRIMARY KEY (message_id, language)
            )
        """)
        await db.commit()

async def get_translation(message_id: int, language: str) -> list[int] | None:
    """Retrieves a cached list of reply_ids for a given message and language."""
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute(
            "SELECT reply_ids FROM cached_translations WHERE message_id = ? AND language = ?",
            (message_id, language)
        ) as cursor:
            row = await cursor.fetchone()
            if row and row[0]:
                return json.loads(row[0])
            return None

async def set_translation(message_id: int, language: str, reply_ids: list[int]):
    """Inserts or updates a translation, batch-evicting old entries if the overshoot threshold is met."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            INSERT OR REPLACE INTO cached_translations (message_id, language, reply_ids)
            VALUES (?, ?, ?)
        """, (message_id, language, json.dumps(reply_ids)))
        await db.commit()
        
        # --- Batch Eviction Logic using rowid ---
        async with db.execute("SELECT COUNT(DISTINCT message_id) FROM cached_translations") as cursor:
            row = await cursor.fetchone()
            distinct_messages = row[0] if row else 0

        # Only clean up if we exceed the 10% overshoot threshold
        if distinct_messages >= TRIGGER_THRESHOLD:
            # Clear out the excess down to your original target limit in one batch
            purge_count = distinct_messages - TARGET_CACHED_MESSAGES
            
            # Find the oldest distinct message_ids based on their smallest rowid
            async with db.execute("""
                SELECT message_id FROM cached_translations 
                GROUP BY message_id 
                ORDER BY MIN(rowid) ASC 
                LIMIT ?
            """, (purge_count,)) as cursor:
                oldest_messages = await cursor.fetchall()
                oldest_ids = [r[0] for r in oldest_messages]

            if oldest_ids:
                placeholder = ",".join("?" for _ in oldest_ids)
                # Wipe out all language tracks associated with those specific message IDs
                await db.execute(
                    f"DELETE FROM cached_translations WHERE message_id IN ({placeholder})",
                    oldest_ids
                )
                await db.commit()