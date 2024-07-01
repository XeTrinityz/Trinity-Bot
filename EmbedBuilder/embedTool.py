# Standard Library Imports
import aiohttp
import json

# Third-Party Library Imports
from discord_webhook import DiscordWebhook
import discord

# Local Module Imports
from .fields import AddFieldModal, RemoveFieldView, EditFieldView
from .general import TitleModal, DescriptionModal, ColorModal, ContentModal, AddMentionView
from .images import ThumbnailModal, ImageModal, FooterImageModal
from .options import FooterTextModal, SaveTemplate, LoadTemplateView, RemoveTemplateView
from utils.database import Database
from utils.lists import *
from Bot import client

db = Database()

class EmbedToolView(discord.ui.View):

    def __init__(self, *args, channel_or_message: discord.abc.GuildChannel | discord.Message, is_new_embed: bool, ctx: discord.ApplicationContext, view = discord.ui.View, custom: str, **kwargs):

        super().__init__(*args, timeout=300, **kwargs)
        self.is_new_embed: bool = is_new_embed
        if self.is_new_embed:
            self.channel: discord.abc.GuildChannel = channel_or_message
        else:
            self.message_edit = channel_or_message
            self.channel = self.message_edit.channel
        self.ctx: discord.ApplicationContext = ctx
        self.author_hidden: bool = True
        self.view = view
        self.timestamp_hidden: bool = True
        self.canceled_before: bool = False
        self.custom = custom

    async def on_timeout(self):
        try:
            self.disable_all_items()
            await self.message.edit(view=self)
        except:
            pass

    @discord.ui.button(label="Title", style=discord.ButtonStyle.gray)
    async def set_title(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:

        try:
            initial_title = interaction.message.embeds[0].title
        except:
            initial_title = None

        await interaction.response.send_modal(TitleModal(title="Embed Title", initial_title=initial_title))

    @discord.ui.button(label="Description", style=discord.ButtonStyle.gray)
    async def set_description(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:

        try:
            initial_description = interaction.message.embeds[0].description
        except:
            initial_description = None

        await interaction.response.send_modal(DescriptionModal(title="Embed Description", initial_description=initial_description))

    @discord.ui.button(label="Color", style=discord.ButtonStyle.gray)
    async def set_color(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:

        initial_color = str(interaction.message.embeds[0].color)
        await interaction.response.send_modal(ColorModal(title="Embed Color", initial_color=initial_color))

    @discord.ui.button(label="Thumbnail", style=discord.ButtonStyle.gray)
    async def set_thumbnail(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        
        try:
            initial_thumbnail_url = interaction.message.embeds[0].thumbnail.url
        except:
            initial_thumbnail_url = None

        await interaction.response.send_modal(ThumbnailModal(title="Thumbnail", initial_thumbnail_url=initial_thumbnail_url))

    @discord.ui.button(label="Image", style=discord.ButtonStyle.gray)
    async def set_image(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:

        try:
            initial_image_url = interaction.message.embeds[0].image.url
        except:
            initial_image_url = None

        await interaction.response.send_modal(ImageModal(title="Image", initial_image_url=initial_image_url))

    @discord.ui.button(label="Footer Icon", style=discord.ButtonStyle.gray)
    async def set_footer_image(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:

        try:
            initial_footer_icon_url = interaction.message.embeds[0].footer.icon_url
        except:
            initial_footer_icon_url = None

        await interaction.response.send_modal(FooterImageModal(title="Footer Icon", initial_footer_image_url=initial_footer_icon_url))

    @discord.ui.button(label="Author", style=discord.ButtonStyle.gray)
    async def set_author(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:

        user_embed = interaction.message.embeds[0]
        if self.author_hidden:
            self.author_hidden = False
            user_embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        else:
            self.author_hidden = True
            user_embed.remove_author()

        await interaction.response.edit_message(embed=user_embed)

    @discord.ui.button(label="Footer", style=discord.ButtonStyle.gray)
    async def set_footer_text(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        
        try:
            initial_footer = interaction.message.embeds[0].footer.text
        except:
            initial_footer = None

        await interaction.response.send_modal(FooterTextModal(title="Embed Description", initial_footer=initial_footer))

    @discord.ui.button(label="Timestamp", style=discord.ButtonStyle.gray)
    async def set_timestamp(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:

        user_embed = interaction.message.embeds[0]
        if self.timestamp_hidden:
            self.timestamp_hidden = False
            user_embed.timestamp = discord.utils.utcnow()
        else:
            self.timestamp_hidden = True
            user_embed.timestamp = None

        await interaction.response.edit_message(embed=user_embed)

    @discord.ui.button(label="Content", style=discord.ButtonStyle.gray)
    async def content_embed(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:

        try:
            initial_content = interaction.message.content
        except:
            initial_content = None
        await interaction.response.send_modal(ContentModal(title="Content", initial_content=initial_content, message=None))

    @discord.ui.button(label="Send", style=discord.ButtonStyle.green)
    async def send_embed(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:

        user_embed = interaction.message.embeds[0]
        content = interaction.message.content
        await interaction.response.defer()

        if self.is_new_embed:
            if self.view is not None:
                message = await self.channel.send(content=content, embed=user_embed, view=self.view)

                if "ticket_category" in self.view.children[0].custom_id:
                    existing_data = await db.get_value_from_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

                    if existing_data:
                        existing_data = json.loads(existing_data)
                        ticket_data = existing_data.get("ticket_data")
                        ticket_data["ticket_panel"] = {"Channel ID": message.channel.id, "Message ID": message.id}
                        await db.update_value_in_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS", "ticket_data", ticket_data)
                        
            elif self.custom is not None:
                if self.custom == "sticky":
                    message = await self.channel.send(content=content, embed=user_embed)
                    data = {"Channel ID": message.channel.id, "Message ID": message.id}
                    await db.update_value_in_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "STICKY", str(message.channel.id), data)

                elif self.custom == "admin_announcement":
                    for servers in client.guilds:
                        owner = servers.owner
                        try:
                            await owner.send(embed=user_embed)
                        except:
                            pass
                    
                    await interaction.followup.send(embed=discord.Embed(title=f"{success_emoji} Embed Sent", description=f"Your custom embed was sent to all server owners.", color=discord.Color.green(), timestamp=discord.utils.utcnow()), ephemeral=True)
                    return await interaction.delete_original_response()

                elif "webhook" in self.custom:
                    splithook = self.custom.split("|")
                    username = splithook[1]
                    webhook = splithook[2]
                    embed_dict = user_embed.to_dict()

                    if "edit" not in self.custom:
                        async with aiohttp.ClientSession() as cs:
                            webhook = DiscordWebhook(url=webhook, content=content, username=username)
                            webhook.add_embed(embed_dict)
                            response = webhook.execute()
                            response_data = response.json()
                    
                        if response.status_code == 200:
                            await interaction.followup.send(embed=discord.Embed(title=f"{success_emoji} Embed Sent", description=f"Your custom embed was sent to <#{response_data['channel_id']}>.", color=discord.Color.green(), timestamp=discord.utils.utcnow()), ephemeral=True)
                        elif response.status_code == 404 or response.status_code == 401:
                            await interaction.followup.send(embed=discord.Embed(title=f"{error_emoji} Request Failed", description="The webhook provided was invalid or no longer existing.", color=discord.Color.green(), timestamp=discord.utils.utcnow()), ephemeral=True)
                        return await interaction.delete_original_response()
                    else:
                        message_id = splithook[3]
                        async with aiohttp.ClientSession() as session:
                            json_data = {
                                "embeds": [embed_dict],
                                "content": content
                            }
                            response = await session.patch(f"{webhook}/messages/{message_id}", json=json_data, headers={'Content-Type': 'application/json'})        
                            response_data = await response.json()

                        if response.status == 200:
                            await interaction.followup.send(embed=discord.Embed(title=f"{success_emoji} Embed Edited", description=f"Your custom embed was edited in <#{response_data['channel_id']}>.", color=discord.Color.green(), timestamp=discord.utils.utcnow()), ephemeral=True)
                        elif response.status == 404 or response.status == 401:
                            await interaction.followup.send(embed=discord.Embed(title=f"{error_emoji} Request Failed", description="The webhook provided was invalid or no longer existing.", color=discord.Color.green(), timestamp=discord.utils.utcnow()), ephemeral=True)
                        return await interaction.delete_original_response()
                    
                elif "trigger" in self.custom:
                    trigger = self.custom.split("_")[1]
                    embed_dict = discord.Embed.to_dict(user_embed)
                    embed_dict["type"] = "Embed"

                    await db.update_value_in_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "TRIGGERS", trigger, embed_dict)
                    return await interaction.delete_original_response()
            else:
                await self.channel.send(content=content, embed=user_embed)
            await interaction.followup.send(embed=discord.Embed(title=f"{success_emoji} Embed Sent", description=f"Your custom embed was sent to {self.channel.mention}.", color=discord.Color.green(), timestamp=discord.utils.utcnow()), ephemeral=True)
        else:
            
            await self.message_edit.edit(content=content, embed=user_embed)
            await interaction.followup.send(embed=discord.Embed(title=f"{success_emoji} Embed Edited", description=f"The embed was updated with your changes.", color=discord.Color.green(), timestamp=discord.utils.utcnow()), ephemeral=True)
        
        await interaction.delete_original_response()

    @discord.ui.button(label="Save Template", style=discord.ButtonStyle.grey)
    async def save_template(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:

        templates = await db.get_value_from_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "TEMPLATES")
        if templates:
            templates = json.loads(templates)

            options = []
            for embed_name, embed_data in templates.items():
                options.append(discord.SelectOption(label=embed_name, value=embed_name))

            if len(options) >= 25:
                await interaction.response.send_message(embed=discord.Embed(title=f"{error_emoji} Request Failed", description="You can not save any more templates.", color=discord.Color.red(), timestamp=discord.utils.utcnow()), ephemeral=True)
                return                   

        await interaction.response.send_modal(SaveTemplate(title="Save Template"))

    @discord.ui.button(label="Load Template", style=discord.ButtonStyle.grey)
    async def load_template(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:

        templates = await db.get_value_from_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "TEMPLATES")
        if templates:
            templates = json.loads(templates)

            options = []
            for embed_name, embed_data in templates.items():
                options.append(discord.SelectOption(label=embed_name, value=embed_name))

            if len(options) == 0:
                await interaction.response.send_message(embed=discord.Embed(title=f"{error_emoji} Request Failed", description="There are no templates to load.", color=discord.Color.red(), timestamp=discord.utils.utcnow()), ephemeral=True)
                return         

            await interaction.response.send_message(embed=discord.Embed(title="Load Template",
                description="Select a template you would like to load.", color=discord.Color.green(), timestamp=discord.utils.utcnow()),
                view=LoadTemplateView(ctx=self.ctx, user_embed=interaction.message.embeds[0], options=options), ephemeral=True)
        else:
            await interaction.response.send_message(embed=discord.Embed(title=f"{error_emoji} Request Failed", description="There are no templates to load.", color=discord.Color.red(), timestamp=discord.utils.utcnow()), ephemeral=True)
            return         

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel_editing(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:

        if self.canceled_before:
            await interaction.response.defer()
            await interaction.delete_original_response()
            return
        self.canceled_before = True
        button.label = "Confirm"
        await interaction.response.edit_message(view=self)
    
    @discord.ui.select(placeholder="Select an option...", options=[discord.SelectOption(label="Add Field"), discord.SelectOption(label="Edit Field"), discord.SelectOption(label="Remove Field"), discord.SelectOption(label="Add Mention"), discord.SelectOption(label="Remove Template")] , min_values=1, max_values=1)
    async def select_option(self, select: discord.ui.Select, interaction: discord.Interaction) -> None:

        if select.values[0] == "Add Field":

            await interaction.response.send_modal(AddFieldModal(title="Add Field"))
       
        elif select.values[0] == "Edit Field":

            fields = interaction.message.embeds[0].fields

            if not fields:
                await interaction.response.send_message(embed=discord.Embed(title=f"{error_emoji} Request Failed",
                    description="There are no fields to edit.", color=discord.Color.red(), timestamp=discord.utils.utcnow()), ephemeral=True)
                return

            options = []
            for index, field in enumerate(fields):
                options.append(discord.SelectOption(label=field.name[:100], description=field.value[:100], value=str(index)))
            
            await interaction.response.send_message(embed=discord.Embed(title="Edit Field",
                description="Select the field you want to edit.", color=discord.Color.green(), timestamp=discord.utils.utcnow()),
                view=EditFieldView(ctx=self.ctx, user_embed=interaction.message.embeds[0], options=options), ephemeral=True)
            
        elif select.values[0] == "Remove Field":

            fields = interaction.message.embeds[0].fields

            if not fields:
                await interaction.response.send_message(embed=discord.Embed(title=f"{error_emoji} Request Failed",
                    description="There are no fields to remove.", color=discord.Color.red(), timestamp=discord.utils.utcnow()), ephemeral=True)
                return

            options = []
            for index, field in enumerate(fields):
                options.append(discord.SelectOption(label=field.name[:100], description=field.value[:100], value=str(index)))
            
            await interaction.response.send_message(embed=discord.Embed(title="Remove Field",
                description="Select the field you want to remove.", color=discord.Color.green(), timestamp=discord.utils.utcnow()), 
                view=RemoveFieldView(ctx=self.ctx, user_embed=interaction.message.embeds[0], options=options), ephemeral=True)
            
        elif select.values[0] == "Add Mention":

            content = interaction.message.content
            await interaction.response.send_message(embed=discord.Embed(title="Add Mention",
                description="Select a role to mention.", color=discord.Color.green(), timestamp=discord.utils.utcnow()), 
                view=AddMentionView(ctx=self.ctx, user_embed=interaction.message.embeds[0], content=content), ephemeral=True)
            
        elif select.values[0] == "Remove Template":

            templates = await db.get_value_from_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "TEMPLATES")
            if templates:
                templates = json.loads(templates)

                options = []
                for embed_name, embed_data in templates.items():
                    options.append(discord.SelectOption(label=embed_name, value=embed_name))

                if len(options) == 0:
                    await interaction.response.send_message(embed=discord.Embed(title=f"{error_emoji} Request Failed", description="There are no templates to remove.", color=discord.Color.red(), timestamp=discord.utils.utcnow()), ephemeral=True)
                    return                   

                await interaction.response.send_message(embed=discord.Embed(title="Remove Template",
                    description="Select a template you would like to remove.", color=discord.Color.green(), timestamp=discord.utils.utcnow()),
                    view=RemoveTemplateView(ctx=self.ctx, user_embed=interaction.message.embeds[0], options=options), ephemeral=True)
            else:
                await interaction.response.send_message(embed=discord.Embed(title=f"{error_emoji} Request Failed", description="There are no templates to remove.", color=discord.Color.red(), timestamp=discord.utils.utcnow()), ephemeral=True)