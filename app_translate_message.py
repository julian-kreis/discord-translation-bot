import discord
from discord import ui, app_commands
from discord.ext import commands

from languages import LANGUAGES_DICT
from translation import translate_message
from translation_utils import chunk_text


PAGE_SIZE = 25


# ---------------------------
# Helper: format + sort languages
# ---------------------------
def get_sorted_languages():
    # LANGUAGES_DICT = {"English": "English", "French": "Français", ...}

    sorted_items = sorted(LANGUAGES_DICT.items(), key=lambda x: x[0].lower())

    # Return tuples: ("English (English)", "English")
    return [
        (f"{english} ({native})", english)
        for english, native in sorted_items
    ]


# ---------------------------
# Select Menu
# ---------------------------
class LanguageSelect(ui.Select):
    def __init__(self, message: discord.Message, languages, page: int, total_pages: int):
        self.message = message
        self.page = page
        self.total_pages = total_pages

        self.languages = languages  # list of (display, value)

        options = [
            discord.SelectOption(label=display, value=value)
            for display, value in languages
        ]

        super().__init__(
            placeholder=f"Page {page + 1}/{total_pages} — Choose language...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        language = self.values[0]

        await interaction.response.defer(ephemeral=True)

        try:
            translated_text = await translate_message(
                self.message,
                interaction.channel,
                language
            )

            for chunk in chunk_text(translated_text):
                await interaction.followup.send(
                    f"**Original:** {self.message.content}\n"
                    f"**{language}:** {chunk}",
                    ephemeral=True
                )

        except Exception:
            await interaction.followup.send(
                "Translation failed.",
                ephemeral=True
            )


# ---------------------------
# Pagination View
# ---------------------------
class PaginationView(ui.View):
    def __init__(self, message: discord.Message, languages, page: int = 0):
        super().__init__(timeout=60)

        self.message_obj = message
        self.languages = languages
        self.page = page

        self.total_pages = (len(languages) + PAGE_SIZE - 1) // PAGE_SIZE

        self.update_view()

    def get_page_slice(self):
        start = self.page * PAGE_SIZE
        end = start + PAGE_SIZE
        return self.languages[start:end]

    def update_view(self):
        self.clear_items()

        page_items = self.get_page_slice()

        self.add_item(
            LanguageSelect(
                self.message_obj,
                page_items,
                self.page,
                self.total_pages
            )
        )

        self.add_item(self.PreviousButton())
        self.add_item(self.NextButton())

    # ---------------------------
    # Buttons
    # ---------------------------
    class PreviousButton(ui.Button):
        def __init__(self):
            super().__init__(label="⬅️ Prev", style=discord.ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            view: "PaginationView" = self.view

            if view.page > 0:
                view.page -= 1
                view.update_view()

            await interaction.response.edit_message(view=view)

    class NextButton(ui.Button):
        def __init__(self):
            super().__init__(label="Next ➡️", style=discord.ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            view: "PaginationView" = self.view

            if view.page < view.total_pages - 1:
                view.page += 1
                view.update_view()

            await interaction.response.edit_message(view=view)


# ---------------------------
# Cog
# ---------------------------
class AppTranslateCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.translate_context_menu = app_commands.ContextMenu(
            name="Translate",
            callback=self.translate_callback
        )

        self.bot.tree.add_command(self.translate_context_menu)

    async def translate_callback(
        self,
        interaction: discord.Interaction,
        message: discord.Message
    ):
        languages = get_sorted_languages()

        await interaction.response.send_message(
            "Select a language:",
            view=PaginationView(message, languages),
            ephemeral=True
        )

    def cog_unload(self):
        self.bot.tree.remove_command(
            self.translate_context_menu.name,
            type=self.translate_context_menu.type
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(AppTranslateCog(bot))