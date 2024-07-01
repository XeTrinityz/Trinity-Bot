import discord
from utils.lists import *

class AddFieldModal(discord.ui.Modal):

    def __init__(self, *args, **kwargs):

        super().__init__(
            discord.ui.InputText(
                label="Field Title",
                placeholder="The field title...",
                style=discord.InputTextStyle.long,
                max_length=256,
                required=False),

            discord.ui.InputText(
                label="Field Value",
                placeholder="The field value...",
                style=discord.InputTextStyle.long,
                max_length=1024,
                required=False),

            discord.ui.InputText(
                label="Inline?",
                placeholder="True/False",
                style=discord.InputTextStyle.short,
                max_length=5,
                required=True), *args, **kwargs)

    async def callback(self, interaction: discord.Interaction) -> None:

        user_embed: discord.Embed = interaction.message.embeds[0]
        title = self.children[0].value
        value = self.children[1].value
        inline_str = self.children[2].value.lower()
        if inline_str in ["true", "1"]:
            inline = True
        
        elif inline_str in ["false", "0"]:
            inline = False
        
        else:
            await interaction.response.send_message(embed=discord.Embed(title=f"{error_emoji} Request Failed",
                description="Supported values are True/False", color=discord.Color.red(), timestamp=discord.utils.utcnow()), ephemeral=True)
            return
        user_embed.add_field(name=title, value=value, inline=inline)

        await interaction.response.edit_message(embed=user_embed)


class RemoveFieldView(discord.ui.View):

    def __init__(self, *args, ctx: discord.ApplicationContext, user_embed: discord.Embed, tutorial_embed=None,
                 options: list[discord.SelectOption], **kwargs):

        self.ctx: discord.ApplicationContext = ctx
        self.user_embed: discord.Embed = user_embed
        self.tutorial_embed: discord.Embed | None = tutorial_embed
        super().__init__(*args, **kwargs)
        self.remove_field.options = options

    @discord.ui.string_select(placeholder="The field to remove...")
    async def remove_field(self, select: discord.ui.Select, interaction: discord.Interaction) -> None:

        await interaction.response.defer()
        field_index: int = int(select.values[0])
        self.user_embed.remove_field(field_index)
        
        await self.ctx.edit(embed=self.user_embed)
        await interaction.delete_original_response()


class EditFieldView(discord.ui.View):

    def __init__(self, *args, ctx: discord.ApplicationContext, user_embed: discord.Embed, tutorial_embed=None, options: list[discord.SelectOption], **kwargs):

        self.ctx: discord.ApplicationContext = ctx
        self.user_embed: discord.Embed = user_embed
        self.tutorial_embed: discord.Embed | None = tutorial_embed
        super().__init__(*args, **kwargs)
        self.edit_field.options = options

    @discord.ui.string_select(placeholder="The field to edit...")
    async def edit_field(self, select: discord.ui.Select, interaction: discord.Interaction) -> None:

        field_index: int = int(select.values[0])
        await interaction.response.send_modal(EditFieldModal(ctx=self.ctx, title="Edit Field", user_embed=self.user_embed, tutorial_embed=self.tutorial_embed, field_index=field_index))
        await interaction.delete_original_response()


class EditFieldModal(discord.ui.Modal):

    def __init__(self, *args, ctx: discord.ApplicationContext, user_embed: discord.Embed, tutorial_embed=None,
                 field_index: int, **kwargs):

        self.ctx: discord.ApplicationContext = ctx
        self.user_embed: discord.Embed = user_embed
        self.tutorial_embed: discord.Embed | None = tutorial_embed
        self.field_index: int = field_index
        
        super().__init__(
            discord.ui.InputText(
                label="Field Title",
                placeholder="Field title...",
                style=discord.InputTextStyle.long,
                max_length=256,
                value=self.user_embed.fields[self.field_index].name,
                required=False),

            discord.ui.InputText(
                label="Field Value",
                placeholder="Field value...",
                style=discord.InputTextStyle.long,
                max_length=1024,
                value=self.user_embed.fields[self.field_index].value,
                required=False),

            discord.ui.InputText(
                label="Inline?",
                placeholder="True/False",
                style=discord.InputTextStyle.short,
                max_length=5,
                value=str(self.user_embed.fields[self.field_index].inline), required=True), *args, **kwargs)

    async def callback(self, interaction: discord.Interaction) -> None:

        await interaction.response.defer()
        title = self.children[0].value
        value = self.children[1].value
        inline_str = self.children[2].value.lower()
        
        if inline_str in ["true", "1"]:
            inline = True
        
        elif inline_str in ["false", "0"]:
            inline = False
        
        else:
            await interaction.response.send_message(embed=discord.Embed(title=f"{error_emoji} Request Failed", description="Supported inputs are True/False.", color=discord.Color.red(), timestamp=discord.utils.utcnow()), ephemeral=True)
            return
        
        self.user_embed.set_field_at(index=self.field_index, name=title, value=value, inline=inline)
        
        await self.ctx.edit(embed=self.user_embed)
