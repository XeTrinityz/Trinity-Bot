import discord
import validators

class ThumbnailModal(discord.ui.Modal):

    def __init__(self, *args, initial_thumbnail_url: str, tutorial_embed=None, **kwargs):

        self.tutorial_embed: discord.Embed | None = tutorial_embed
        super().__init__(
            discord.ui.InputText(label="Embed Thumbnail",
                placeholder="The thumbnail URL...",
                style=discord.InputTextStyle.long, max_length=4000, value=initial_thumbnail_url, required=False), *args, **kwargs)

    async def callback(self, interaction: discord.Interaction) -> None:

        if not validators.url(self.children[0].value):
            await interaction.response.send_message("Invalid Link", ephemeral=True)
            return
        
        user_embed: discord.Embed = interaction.message.embeds[0]
        user_embed.set_thumbnail(url=self.children[0].value)

        await interaction.response.edit_message(embed=user_embed)


class ImageModal(discord.ui.Modal):

    def __init__(self, *args, initial_image_url: str, tutorial_embed=None, **kwargs):

        self.tutorial_embed: discord.Embed | None = tutorial_embed
        super().__init__(
            discord.ui.InputText(
                label="Embed Image",
                placeholder="The image URL...",
                style=discord.InputTextStyle.long,
                max_length=4000,
                value=initial_image_url,
                required=False
            ),
            *args,
            **kwargs
        )

    async def callback(self, interaction: discord.Interaction) -> None:

        if not validators.url(self.children[0].value):
            await interaction.response.send_message("Invalid Link", ephemeral=True)
            return
        
        user_embed: discord.Embed = interaction.message.embeds[0]
        user_embed.set_image(url=self.children[0].value)

        await interaction.response.edit_message(embed=user_embed)


class FooterImageModal(discord.ui.Modal):

    def __init__(self, *args, initial_footer_image_url: str, tutorial_embed=None, **kwargs):

        self.tutorial_embed: discord.Embed | None = tutorial_embed
        super().__init__(
            discord.ui.InputText(
                label="Embed Footer Image",
                placeholder="Footer icon URL...",
                style=discord.InputTextStyle.long,
                max_length=4000,
                value=initial_footer_image_url,
                required=False
            ),
            *args,
            **kwargs
        )

    async def callback(self, interaction: discord.Interaction) -> None:

        if not validators.url(self.children[0].value):
            await interaction.response.send_message("Invalid Link", ephemeral=True)
            return
        
        user_embed: discord.Embed = interaction.message.embeds[0]
        try:
            user_embed.footer.icon_url = self.children[0].value
        except:
            pass
        
        footer_text = user_embed.footer
        if footer_text is None:
            footer_text = "ﾠ"
        user_embed.set_footer(text=footer_text, icon_url=self.children[0].value)

        await interaction.response.edit_message(embed=user_embed)
