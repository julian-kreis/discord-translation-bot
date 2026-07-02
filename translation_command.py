import discord
from discord import app_commands
from discord.ext import commands

from languages import LANGUAGES_DICT
from translation import translate_text
from translation_utils import chunk_text


class TranslationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_as_user(self, interaction: discord.Interaction, content: str):
        """Send a message through a webhook using the user's name and avatar."""
        channel = interaction.channel

        webhooks = await channel.webhooks()
        webhook = next((w for w in webhooks if w.name == "TranslatorWebhook"), None)

        if webhook is None:
            webhook = await channel.create_webhook(name="TranslatorWebhook")

        await webhook.send(
            content=content,
            username=interaction.user.display_name,
            avatar_url=interaction.user.display_avatar.url,
        )

    @app_commands.command(
        name="send-translated-message",
        description="Translate text and send the translation."
    )
    @app_commands.describe(
        language="The target language",
        text="The text to translate"
    )
    async def send_translated_message(
        self,
        interaction: discord.Interaction,
        language: str,
        text: str,
    ):
        await interaction.response.defer()
    
        translated_text = await translate_text(text, language)

        try:
            if interaction.guild and interaction.app_permissions.manage_webhooks:
                for chunk in chunk_text(translated_text):
                    await self.send_as_user(interaction, chunk)
                await interaction.delete_original_response()
            else:
                for chunk in chunk_text(translated_text):
                    await interaction.followup.send(chunk)
                    
        except Exception:
            await interaction.followup.send("Translation API Error", ephemeral=True)

    @app_commands.command(
        name="translate",
        description="Translate text to a different language."
    )
    @app_commands.describe(
        language="The target language",
        text="The text to translate"
    )
    async def translate(
        self,
        interaction: discord.Interaction,
        language: str,
        text: str,
    ):
        await interaction.response.defer()

        try:
            translated_text = await translate_text(text, language)

            native_name = LANGUAGES_DICT.get(language, language)
            output = f"**Original:** {text}\n**{native_name}:** {translated_text}"

            chunks = chunk_text(output)

            for chunk in chunks:
                await interaction.followup.send(chunk)

        except Exception:
            await interaction.followup.send("Translation API Error")

    @send_translated_message.autocomplete("language")
    @translate.autocomplete("language")
    async def language_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ):
        results = []

        for eng_name, native_name in LANGUAGES_DICT.items():
            value = eng_name
            display = f"{eng_name} ({native_name})"

            if (
                current.lower() in eng_name.lower()
                or current.lower() in native_name.lower()
            ):
                results.append(
                    app_commands.Choice(
                        name=display,
                        value=value,
                    )
                )

        return results[:25]


async def setup(bot):
    await bot.add_cog(TranslationCog(bot))