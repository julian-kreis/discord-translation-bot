import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from languages import LANGUAGES_DICT
from translation import translate_text
from translation_utils import chunk_text

class TranslationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_as_user(self, interaction: discord.Interaction, content: str):
        """Helper to send a message via webhook as the user."""
        channel = interaction.channel
        
        # Look for existing webhook or create one
        webhooks = await channel.webhooks()
        webhook = next((w for w in webhooks if w.name == "TranslatorWebhook"), None)
        
        if not webhook:
            webhook = await channel.create_webhook(name="TranslatorWebhook")

        await webhook.send(
            content=content,
            username=interaction.user.display_name,
            avatar_url=interaction.user.display_avatar.url
        )

    @app_commands.command(name="translate", description="Translate text to a target language")
    @app_commands.describe(
        language="The target language",
        text="The text you want to translate",
        include_original="Include the original message?"
    )
    @app_commands.choices(include_original=[
        app_commands.Choice(name="Yes", value="yes"),
        app_commands.Choice(name="No", value="no")
    ])
    async def translate(
        self, 
        interaction: discord.Interaction, 
        language: str, 
        text: str, 
        include_original: Optional[app_commands.Choice[str]] = None
    ):
        # Defer silently so the command isn't hanging, but don't show "Thinking..." to everyone
        await interaction.response.defer(ephemeral=True)
        
        option = include_original.value if include_original else "no"
        username = interaction.user.display_name
        
        try:
            translated_text = await translate_text(text, language)
            
            if option == "yes":
                full_output = f"{text}\n{translated_text}"
            else:
                full_output = f"{translated_text}"
            
            chunks = chunk_text(full_output)
            
            # Send chunks via the webhook impersonation helper
            for chunk in chunks:
                await self.send_as_user(interaction, chunk)
            
            # Final silent confirmation to the user
            await interaction.followup.send("Translation sent!", ephemeral=True)
                
        except Exception as e:
            await interaction.followup.send(f"Translation API Error", ephemeral=True)

    @translate.autocomplete('language')
    async def language_autocomplete(self, interaction: discord.Interaction, current: str):
        results = []
        for eng_name, native_name in LANGUAGES_DICT.items():
            val = eng_name.split('(')[0].strip()
            display_name = f"{eng_name} ({native_name})"
            if current.lower() in eng_name.lower() or current.lower() in native_name.lower():
                results.append(app_commands.Choice(name=display_name, value=val))
        return results[:25]

async def setup(bot):
    await bot.add_cog(TranslationCog(bot))