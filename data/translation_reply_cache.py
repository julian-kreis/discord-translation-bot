import aiosqlite

DB_FILE = "translation_reply_cache.db"
TARGET_CACHED_MESSAGES = 100000
TRIGGER_THRESHOLD = int(TARGET_CACHED_MESSAGES * 1.1)

async def init_db():
    """Initializes the database and creates the translations table."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        # Using a composite primary key. SQLite provides a hidden 'rowid' 
        # for this table that automatically increments on every insert.
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cached_translations (
                message_id INTEGER,
                language TEXT,
                reply_id INTEGER,
                PRIMARY KEY (message_id, language)
            )
        """)
        await db.commit()

async def get_translation(message_id: int, language: str) -> int | None:
    """Retrieves a cached reply_id for a given message and language."""
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute(
            "SELECT reply_id FROM cached_translations WHERE message_id = ? AND language = ?",
            (message_id, language)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def set_translation(message_id: int, language: str, reply_id: int):
    """Inserts or updates a translation, batch-evicting old entries if the overshoot threshold is met."""
    async with aiosqlite.connect(DB_FILE) as db:
        # INSERT OR REPLACE keeps things clean, but note that REPLACE deletes the old row
        # and inserts a new one, which helpfully bumps its 'rowid' to the end of the line!
        await db.execute("""
            INSERT OR REPLACE INTO cached_translations (message_id, language, reply_id)
            VALUES (?, ?, ?)
        """, (message_id, language, reply_id))
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