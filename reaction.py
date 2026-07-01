from discord.ext import commands

from languages import language_from_flag
from data.translation_reply_cache import get_translation, set_translation
from translation_utils import process_and_send_translation, refresh_duplicate_translation

class ReactionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user} reaction.py ready!")

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
        old_reply_ids = await get_translation(message.id, language)

        try:
            if old_reply_ids is not None:
                # -------------------------
                # Duplicate/Refresh logic
                # -------------------------
                new_reply_ids = await refresh_duplicate_translation(message, channel, language, old_reply_ids)
                await set_translation(message.id, language, new_reply_ids)
            else:
                # -------------------------
                # First-time translation
                # -------------------------
                new_reply_ids = await process_and_send_translation(message, channel, language)
                await set_translation(message.id, language, new_reply_ids)
        except Exception:
            # Exceptions are handled, logged, and user-notified inside the utils functions.
            # We catch here so the listener doesn't throw unhandled errors to the console.
            pass

async def setup(bot):
    await bot.add_cog(ReactionCog(bot))