import discord
from discord.ext import commands
from utils.lists import *


class TitleModal(discord.ui.Modal):

    def __init__(self, *args, initial_title: str, **kwargs):

        super().__init__(
            discord.ui.InputText(label="Embed Title",
                placeholder="The embed title...",
                style=discord.InputTextStyle.paragraph, max_length=256, value=initial_title, required=False), *args, **kwargs)

    async def callback(self, interaction: discord.Interaction) -> None:

        user_embed: discord.Embed = interaction.message.embeds[0]
        user_embed.title = self.children[0].value

        await interaction.response.edit_message(embed=user_embed)


class DescriptionModal(discord.ui.Modal):

    def __init__(self, *args, initial_description: str, tutorial_embed=None, **kwargs):

        self.tutorial_embed: discord.Embed | None = tutorial_embed
        super().__init__(
            discord.ui.InputText(label="Embed Description",
                placeholder="The embed description...",
                style=discord.InputTextStyle.paragraph, max_length=4000, value=initial_description, required=False), *args, **kwargs)

    async def callback(self, interaction: discord.Interaction) -> None:

        user_embed: discord.Embed = interaction.message.embeds[0]
        user_embed.description = self.children[0].value

        await interaction.response.edit_message(embed=user_embed)


class ContentModal(discord.ui.Modal):

    def __init__(self, *args, initial_content: str, message: discord.Message, **kwargs):
        self.message = message

        super().__init__(
            discord.ui.InputText(label="Embed Content",
                placeholder="The message content...",
                style=discord.InputTextStyle.paragraph, max_length=4000, value=initial_content, required=False), *args, **kwargs)

    async def callback(self, interaction: discord.Interaction) -> None:
        
        content = self.children[0].value
        if not self.message:
            user_embed: discord.Embed = interaction.message.embeds[0]
            await interaction.response.edit_message(content=content, embed=user_embed)
        else:
            await self.message.edit(content=content)
            await interaction.response.defer()


class ColorModal(discord.ui.Modal):

    def __init__(self, *args, initial_color: str, tutorial_embed=None, **kwargs):

        self.tutorial_embed: discord.Embed | None = tutorial_embed
        super().__init__(
            discord.ui.InputText(label="Embed Color",
                placeholder="#FFFFFF",
                style=discord.InputTextStyle.short, max_length=7, value=initial_color, required=False), *args, **kwargs)

    async def callback(self, interaction: discord.Interaction) -> None:

        user_embed: discord.Embed = interaction.message.embeds[0]
        color_string = self.children[0].value
        color = await commands.ColorConverter().convert(interaction, color_string)
        user_embed.colour = color

        await interaction.response.edit_message(embed=user_embed)

    async def on_error(self, error: Exception, interaction: discord.Interaction) -> None:

        if isinstance(error, commands.BadArgument):
            await interaction.response.send_message(embed=discord.Embed(title=f"{error_emoji} Request Failed", description="Invalid color format.", color=discord.Color.red(), timestamp=discord.utils.utcnow()), ephemeral=True)
            return
        
        raise error
    
    
class AddMentionView(discord.ui.View):

    def __init__(self, *args, ctx: discord.ApplicationContext, user_embed: discord.Embed, content: str, **kwargs):

        self.ctx: discord.ApplicationContext = ctx
        self.content: str = content
        self.user_embed: discord.Embed = user_embed
        super().__init__(*args, **kwargs)

    @discord.ui.mentionable_select(placeholder="The member or role to mention...")
    async def mention_role(self, select: discord.ui.Select, interaction: discord.Interaction) -> None:

        await interaction.response.defer()
        role = select.values[0]
        content = self.content
        await self.ctx.edit(content=f"{content} " + role.mention, embed=self.user_embed)
        await interaction.delete_original_response()
