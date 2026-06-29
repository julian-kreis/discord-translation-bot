import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from google import genai

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True
intents.guild_reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

# message_id -> {language: reply_message_id}
translations = {}

REGIONAL_BASE = 0x1F1E6

COUNTRY_LANGUAGE = {
    # English
    "US": "English", "GB": "English", "AU": "English",
    "CA": "English", "NZ": "English", "IE": "English",

    # French
    "FR": "French", "BE": "French", "CH": "French",

    # Spanish
    "ES": "Spanish", "MX": "Spanish", "AR": "Spanish",
    "CL": "Spanish", "CO": "Spanish", "PE": "Spanish",

    # Portuguese
    "PT": "Portuguese", "BR": "Portuguese",

    # German
    "DE": "German", "AT": "German",

    # Chinese
    "CN": "Simplified Chinese",
    "SG": "Simplified Chinese",
    "TW": "Traditional Chinese",
    "HK": "Traditional Chinese",

    "JP": "Japanese",
    "KR": "Korean",
    "IT": "Italian",
    "NL": "Dutch",
    "SE": "Swedish",
    "NO": "Norwegian",
    "DK": "Danish",
    "FI": "Finnish",
    "PL": "Polish",
    "CZ": "Czech",
    "SK": "Slovak",
    "HU": "Hungarian",
    "RO": "Romanian",
    "BG": "Bulgarian",
    "GR": "Greek",
    "TR": "Turkish",
    "RU": "Russian",
    "UA": "Ukrainian",
    "IL": "Hebrew",
    "SA": "Arabic",
    "AE": "Arabic",
    "EG": "Arabic",
    "TH": "Thai",
    "VN": "Vietnamese",
    "IN": "Hindi",
}


def flag_to_country(flag):
    if len(flag) != 2:
        return None

    chars = []

    for c in flag:
        code = ord(c)
        if not (0x1F1E6 <= code <= 0x1F1FF):
            return None
        chars.append(chr(ord("A") + code - REGIONAL_BASE))

    return "".join(chars)


def language_from_flag(flag):
    country = flag_to_country(flag)
    if country is None:
        return None
    return COUNTRY_LANGUAGE.get(country)


async def language_still_reacted(message, language):
    for reaction in message.reactions:
        emoji = str(reaction.emoji)

        if language_from_flag(emoji) != language:
            continue

        users = [u async for u in reaction.users()]

        if any(not u.bot for u in users):
            return True

    return False


@bot.event
async def on_ready():
    print(bot.user)


@bot.event
async def on_raw_reaction_add(payload):

    if payload.user_id == bot.user.id:
        return

    channel = bot.get_channel(payload.channel_id) or await bot.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    language = language_from_flag(str(payload.emoji))

    if language is None:
        return

    translations.setdefault(message.id, {})

    if language in translations[message.id]:
        return

    prompt = f"""
Translate into {language}.

Return ONLY the translated text.

{message.content}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    reply = await message.reply(
        f"**{language}**\n{response.text}",
        mention_author=False
    )

    translations[message.id][language] = reply.id


@bot.event
async def on_raw_reaction_remove(payload):

    channel = bot.get_channel(payload.channel_id) or await bot.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    language = language_from_flag(str(payload.emoji))

    if language is None:
        return

    if message.id not in translations:
        return

    if language not in translations[message.id]:
        return

    if await language_still_reacted(message, language):
        return

    try:
        reply = await channel.fetch_message(translations[message.id][language])
        await reply.delete()
    except discord.NotFound:
        pass

    del translations[message.id][language]

    if not translations[message.id]:
        del translations[message.id]


bot.run(TOKEN)