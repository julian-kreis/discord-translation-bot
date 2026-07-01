import discord
from discord import app_commands
from discord.ext import commands

from languages import LANGUAGES_DICT 
from translation import translate_text
from translation_utils import chunk_text

class TranslationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="translate", description="Translate text to a target language")
    @app_commands.describe(
        language="The target language",
        text="The text you want to translate"
    )
    async def translate(self, interaction: discord.Interaction, language: str, text: str):
        await interaction.response.defer(ephemeral=False)

        try:
            # 1. Get the translation
            translated_text = await translate_text(text, language)
            
            # 2. Format the entire block
            full_output = f"{interaction.user.display_name}: {text}\n{language}: {translated_text}"
            
            # 3. Chunk the full formatted string
            chunks = chunk_text(full_output)
            
            # 4. Send the chunks
            for chunk in chunks:
                await interaction.followup.send(chunk)

        except Exception as e:
            await interaction.followup.send(f"Translation API error.", ephemeral=True)

    @translate.autocomplete('language')
    async def language_autocomplete(self, interaction: discord.Interaction, current: str):
        results = []
        for eng_name, native_name in LANGUAGES_DICT.items():
            display_name = f"{eng_name} ({native_name})"
            if current.lower() in eng_name.lower() or current.lower() in native_name.lower():
                results.append(app_commands.Choice(name=display_name, value=eng_name))
        return results[:25]

async def setup(bot):
    await bot.add_cog(TranslationCog(bot))