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

@bot.event
async def on_ready():
    await bot.tree.sync()

    await bot.change_presence(
        activity=discord.Game(name="/help me understand")
    )

    print(f"Logged in as {bot.user} and commands synced!")

async def main():
    await translation_reply_cache.init_db()

    async with bot:
        # Load your cogs
        await bot.load_extension("reaction")
        await bot.load_extension("app_translate_message")
        await bot.load_extension("translation_command")
        await bot.load_extension("help_command")
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())