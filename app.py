import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from data import translation_reply_cache

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True
intents.guild_reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)


async def main():
    await translation_reply_cache.init_db()

    async with bot:
        await bot.load_extension("reaction")
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())