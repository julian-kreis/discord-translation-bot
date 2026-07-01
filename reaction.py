import asyncio
import discord
from collections import OrderedDict
from discord.ext import commands

from languages import language_from_flag
from translation import translate_message

MAX_CACHED_MESSAGES = 1000
MAX_TRANSLATIONS_PER_LANG = 50

translations = OrderedDict()
reaction_stack = OrderedDict()


class ReactionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

        # Cache management
        if message.id not in translations:
            if len(translations) >= MAX_CACHED_MESSAGES:
                oldest_message_id, _ = translations.popitem(last=False)

                # Remove any cached reactions for the evicted message
                for key in list(reaction_stack):
                    if key[0] == oldest_message_id:
                        reaction_stack.pop(key, None)

            translations[message.id] = {}

        reaction_key = (
            message.id,
            payload.user_id,
            str(payload.emoji),
        )

        if reaction_key in reaction_stack:
            return

        if language not in translations[message.id]:
            translations[message.id][language] = []

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

            reaction_stack[reaction_key] = language

            if len(reaction_stack) > MAX_CACHED_MESSAGES:
                reaction_stack.popitem(last=False)

            translations[message.id][language].append(
                (reaction_key, reply.id)
            )

            if (
                len(translations[message.id][language])
                > MAX_TRANSLATIONS_PER_LANG
            ):
                translations[message.id][language].pop(0)

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

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        channel = (
            self.bot.get_channel(payload.channel_id)
            or await self.bot.fetch_channel(payload.channel_id)
        )

        message = await channel.fetch_message(payload.message_id)

        language = language_from_flag(str(payload.emoji))
        if language is None:
            return

        reaction_key = (
            message.id,
            payload.user_id,
            str(payload.emoji),
        )

        reaction_stack.pop(reaction_key, None)

        if message.id not in translations:
            return

        if language not in translations[message.id]:
            return

        stack = translations[message.id][language]

        for i in range(len(stack) - 1, -1, -1):
            if stack[i][0] == reaction_key:
                _, reply_id = stack.pop(i)

                try:
                    reply = await channel.fetch_message(reply_id)
                    await reply.delete()
                except discord.NotFound:
                    pass

                break

        if not translations[message.id][language]:
            del translations[message.id][language]

        if not translations[message.id]:
            del translations[message.id]


async def setup(bot):
    await bot.add_cog(ReactionCog(bot))