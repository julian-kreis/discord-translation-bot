import asyncio
import discord
from translation import translate_message

MAX_CONCURRENT_REQS = 5
MAX_MESSAGE_LENGTH = 1900
MAX_CHUNKS = 3

# Caps simultaneous Translation API and typing requests globally across all importing modules
TRANSLATION_SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_REQS)

def chunk_text(text: str) -> list[str]:
    """Breaks text into chunks based on max length and chunk count limits."""
    chunks = []
    while text and len(chunks) < MAX_CHUNKS:
        if len(text) <= MAX_MESSAGE_LENGTH:
            chunks.append(text)
            break
        
        # Try to find a clean break (newline or space) within the limit
        split_at = text.rfind('\n', 0, MAX_MESSAGE_LENGTH)
        if split_at == -1:
            split_at = text.rfind(' ', 0, MAX_MESSAGE_LENGTH)
        if split_at == -1:
            split_at = MAX_MESSAGE_LENGTH # Hard cut if no spaces exist
            
        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()
        
    return chunks

async def process_and_send_translation(message, channel, language) -> list[int]:
    """
    Handles typing states, semaphore locking, fetching the translation, 
    chunking the message, and sending the replies.
    """
    async with TRANSLATION_SEMAPHORE:
        stop_typing = asyncio.Event()

        async def keep_typing():
            try:
                while not stop_typing.is_set():
                    async with channel.typing():
                        await asyncio.sleep(8)
            except asyncio.CancelledError:
                pass

        typing_task = asyncio.create_task(keep_typing())

        try:
            translated = await translate_message(message, channel, language)
            chunks = chunk_text(translated)
            
            reply_ids = []
            for chunk in chunks:
                reply = await message.reply(chunk, mention_author=False)
                reply_ids.append(reply.id)
                
            return reply_ids

        except Exception as e:
            print(f"Translation Error: {e}")
            await message.reply("Translation API failure.", mention_author=False)
            raise  # Re-raise so the caller knows the generation failed
        finally:
            stop_typing.set()
            typing_task.cancel()
            try:
                await typing_task
            except asyncio.CancelledError:
                pass

async def refresh_duplicate_translation(message, channel, language, old_reply_ids: list[int]) -> list[int]:
    """
    Handles copying old translation replies to the bottom of the chat,
    deleting the old ones, or regenerating them if deleted externally.
    """
    try:
        new_reply_ids = []
        for old_id in old_reply_ids:
            old_reply = await channel.fetch_message(old_id)

            # copy old message content
            new_reply = await message.reply(
                old_reply.content,
                mention_author=False,
            )
            new_reply_ids.append(new_reply.id)

            # delete old reply
            await old_reply.delete()
            
        return new_reply_ids

    except discord.NotFound:
        print("Cached translation messages were deleted externally. Regenerating...")
        # if any chunk was deleted externally, just regenerate the whole thing
        return await process_and_send_translation(message, channel, language)

    except Exception as e:
        print(f"Duplicate translation error: {e}")
        await message.reply(
            "Translation refresh failed.",
            mention_author=False,
        )
        raise