import discord
from discord import app_commands
from discord.ext import commands


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="help",
        description="Show information about the available bot functionality."
    )
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="ePolyglot Help",
            description="Information about available bot functionality",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="/translate",
            value=(
                "Translate input text to a target language and reply with both the original text and the "
                "translated version."
            ),
            inline=False
        )

        embed.add_field(
            name="/send-translated-message",
            value=(
                "Translate input text to a target language and send the translated message as you."
                "Requires Manage Webhooks permission."
            ),
            inline=False
        )

        embed.add_field(
            name="Flag Reactions",
            value=(
                "React to any message with a supported country flag to translate "
                "that message into the corresponding language."
            ),
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(HelpCog(bot))