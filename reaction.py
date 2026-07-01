import asyncio
import discord
from discord.ext import commands

from languages import language_from_flag
from translation import translate_message
from data.translation_reply_cache import get_translation, set_translation

MAX_CONCURRENT_REQS = 5

class ReactionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Caps simultaneous Translation API and typing requests globally across all servers
        self.translation_semaphore = asyncio.Semaphore(5)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in as {self.bot.user}!")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return

        channel = (
            self.bot.get_channel(payload.channel_id)
            or await self.bot.fetch_channel(payload.channel_id)
        )

        message = await channel.fetch_message(payload.message_id)

        language = language_from_flag(str(payload.emoji))
        if language is None:
            return

        # -------------------------
        # Check database for existing translation
        # -------------------------
        old_reply_id = await get_translation(message.id, language)

        if old_reply_id is not None:
            # -------------------------
            # Duplicate reaction logic
            # -------------------------
            try:
                old_reply = await channel.fetch_message(old_reply_id)

                # copy old message content
                new_reply = await message.reply(
                    old_reply.content,
                    mention_author=False,
                )

                # delete old reply
                await old_reply.delete()

                # update database cache
                await set_translation(message.id, language, new_reply.id)

            except discord.NotFound:
                # if deleted externally, just regenerate
                translated = await translate_message(
                    message,
                    channel,
                    language,
                )

                new_reply = await message.reply(
                    translated,
                    mention_author=False,
                )

                await set_translation(message.id, language, new_reply.id)

            except Exception as e:
                print(f"Duplicate translation error: {e}")
                await message.reply(
                    "Translation refresh failed.",
                    mention_author=False,
                )

            return

        # -------------------------
        # First-time translation (Protected by Semaphore)
        # -------------------------
        async with self.translation_semaphore:
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
                translated = await translate_message(
                    message,
                    channel,
                    language,
                )

                reply = await message.reply(
                    translated,
                    mention_author=False,
                )

                # Save the new translation to the database
                await set_translation(message.id, language, reply.id)

            except Exception as e:
                print(f"Translation Error: {e}")

                await message.reply(
                    "Translation API failure.",
                    mention_author=False,
                )

            finally:
                stop_typing.set()
                typing_task.cancel()

                try:
                    await typing_task
                except asyncio.CancelledError:
                    pass


async def setup(bot):
    await bot.add_cog(ReactionCog(bot))