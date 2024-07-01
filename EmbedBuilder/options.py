import discord
import json
from utils.lists import *
from utils.database import Database

db = Database()

class FooterTextModal(discord.ui.Modal):

    def __init__(self, *args, initial_footer: str, tutorial_embed=None, **kwargs):

        self.tutorial_embed: discord.Embed | None = tutorial_embed
        super().__init__(
            discord.ui.InputText(
                label="Embed Footer:",
                placeholder="The embed footer...",
                style=discord.InputTextStyle.long,
                max_length=2048,
                value=initial_footer,
                required=False
            ),
            *args,
            **kwargs
        )

    async def callback(self, interaction: discord.Interaction) -> None:

        user_embed: discord.Embed = interaction.message.embeds[0]
        try:
            icon_url = user_embed.footer.icon_url
        except:
            icon_url = ""
        user_embed.set_footer(text=self.children[0].value, icon_url=icon_url)

        if self.tutorial_embed:
            await interaction.response.edit_message(embeds=[user_embed, self.tutorial_embed])
            return
        await interaction.response.edit_message(embed=user_embed)


class SaveTemplate(discord.ui.Modal):

    def __init__(self, *args, **kwargs):

        
        super().__init__(
            discord.ui.InputText(
                label="Embed Title",
                placeholder="My Embed",
                style=discord.InputTextStyle.singleline,
                max_length=100,
                required=True), *args, **kwargs)

    async def callback(self, interaction: discord.Interaction) -> None:

        await interaction.response.defer()
        user_embed: discord.Embed = interaction.message.embeds[0]
        embed_dict = discord.Embed.to_dict(user_embed)
        await db.update_value_in_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "TEMPLATES", str(self.children[0].value), embed_dict)

        await interaction.followup.send(embed=discord.Embed(title=f"{success_emoji} Template Saved", description="The current embed has been saved successfully.", color=discord.Color.green(), timestamp=discord.utils.utcnow()), ephemeral=True)


class LoadTemplateView(discord.ui.View):

    def __init__(self, *args, ctx: discord.ApplicationContext, user_embed: discord.Embed, options: list[discord.SelectOption], **kwargs):

        self.ctx: discord.ApplicationContext = ctx
        self.user_embed: discord.Embed = user_embed
        super().__init__(*args, **kwargs)
        self.load_template.options = options

    @discord.ui.string_select(placeholder="The template to load...")
    async def load_template(self, select: discord.ui.Select, interaction: discord.Interaction) -> None:
        selected_template = select.values[0]
        await interaction.response.defer()

        if selected_template:
            all_embeds = await db.get_value_from_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "TEMPLATES")
            if all_embeds:
                all_embeds = json.loads(all_embeds)
                template_data = all_embeds.get(selected_template)

                if template_data:
                    embed = discord.Embed.from_dict(template_data)
                    await self.ctx.edit(embed=embed)

        await interaction.delete_original_response()
       

class RemoveTemplateView(discord.ui.View):

    def __init__(self, *args, ctx: discord.ApplicationContext, user_embed: discord.Embed, options: list[discord.SelectOption], **kwargs):

        self.ctx: discord.ApplicationContext = ctx
        self.user_embed: discord.Embed = user_embed
        super().__init__(*args, **kwargs)
        self.remove_template.options = options

    @discord.ui.string_select(placeholder="The template to remove...")
    async def remove_template(self, select: discord.ui.Select, interaction: discord.Interaction) -> None:
        selected_template = select.values[0]
        await interaction.response.defer()

        if selected_template:
            all_embeds = await db.get_value_from_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "TEMPLATES")
            if all_embeds:
                all_embeds = json.loads(all_embeds)
                template_data = all_embeds.get(selected_template)

                if template_data:
                    await db.remove_value_from_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "TEMPLATES", selected_template)
                    await interaction.followup.send(embed=discord.Embed(title=f"{success_emoji} Template Removed", description=f"The {selected_template} template was removed.", color=discord.Color.green(), timestamp=discord.utils.utcnow()), ephemeral=True)

        await interaction.delete_original_response()
        await self.ctx.edit(embed=self.user_embed)