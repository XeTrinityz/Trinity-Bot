# Third-Party Library Imports
import discord
from discord.ui import Button
from datetime import datetime, timedelta
import pytz
import io
import json
import chat_exporter

# Local Module Imports
from utils.database import Database
from utils.functions import Utils
from utils.lists import interaction_cooldowns
from utils.lists import *

db = Database()
last_execution_time = {}

def format_ticket_counter(counter_value, width=4):
    return f"{counter_value:0{width}d}"

async def get_category_channels(ctx: discord.AutocompleteContext):
    try:

        existing_data = await db.get_value_from_table(ctx.interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

        if existing_data:
            existing_data = json.loads(existing_data)
            ticket_data = existing_data.get("ticket_data")

            if "category_roles" in ticket_data:
                category_roles = ticket_data["category_roles"]
                category_ids = [int(category_id) for category_id in category_roles.keys()]
                category_info = [f"{category.name}" for category in ctx.interaction.guild.categories if category.id in category_ids]

                return category_info

    except Exception as e:
        print("[get_category_channels]: ", e)

    return []


class ticketReason(discord.ui.Modal):
    def __init__(self, category):
        super().__init__(
            discord.ui.InputText(label="Ticket Reason", placeholder=None, style=discord.InputTextStyle.paragraph, max_length=1000), title=category.name)
        self.category = category

    async def callback(self, interaction: discord.Interaction):
        
        await interaction.response.send_message("# <a:Loading:1247220769511964673> Creating Ticket\n\nYour ticket is being created...", ephemeral=True)

        existing_data = await db.get_value_from_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

        if existing_data:
            existing_data = json.loads(existing_data)
            ticket_data = existing_data.get("ticket_data")
            category_role = ticket_data.get("category_roles")

        role = interaction.guild.get_role(category_role[str(self.category.id)])

        if role is None:
            return await interaction.edit_original_response(content=f"# {error_emoji} Failed\nRole not found for this category. Please contact an administrator.")

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True),
            role: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True)}

        ticket_data["ticket_counter"] = ticket_data["ticket_counter"] + 1

        ticket_number = format_ticket_counter(ticket_data["ticket_counter"])
        channel = await interaction.guild.create_text_channel(f"ticket-{interaction.user.name[:5].lower()}-{ticket_number}", reason=f"Ticket Channel Create", category=self.category, overwrites=overwrites)

        view = discord.ui.View(timeout=None)
        delButton = Button(label="Delete Ticket", custom_id="ticket_delete", emoji=f"{error_emoji}", style=discord.ButtonStyle.red)
        closeButton = Button(label="Close Ticket", custom_id="ticket_close", emoji="<a:Locked:1209072654808776714>", style=discord.ButtonStyle.red)
        claimButton = Button(label="Claim Ticket", custom_id="ticket_claim", emoji=f"{success_emoji}", style=discord.ButtonStyle.blurple)
        view.add_item(claimButton)
        view.add_item(closeButton)
        view.add_item(delButton)

        embed = await db.build_embed(interaction.guild, title=f"Ticket #{ticket_number} ({self.category.name})",
            description=f"Welcome {interaction.user.mention}, to your ticket!\n\nSupport will be with you shortly.\nWe appreciate your patiance.\n\n**Ticket Reason** ➭ {self.children[0].value}")
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        ticketMsg = await channel.send(f"{interaction.user.mention}, {role.mention}", embed=embed, view=view)
        await ticketMsg.pin()

        await interaction.edit_original_response(content=f"# {success_emoji} Ticket Created\n\nYou can access your ticket here ➭ {channel.mention}")

        ticket_data["open_tickets"][str(interaction.user.id)] = channel.id

        await db.update_value_in_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS", "ticket_data", ticket_data)


class TicketSettings(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def delete_button_callback(self, interaction: discord.Interaction):

        # Check cooldown
        if interaction.user.id in interaction_cooldowns and datetime.utcnow() - interaction_cooldowns[interaction.user.id] < timedelta(seconds=5):
            remaining_time = (interaction_cooldowns[interaction.user.id] + timedelta(seconds=5) - datetime.utcnow()).seconds
            embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description=f"You are on cooldown. Please try again in **{remaining_time}** seconds.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await interaction.message.edit(view=discord.ui.View.from_message(interaction.message))
            return

        interaction_cooldowns[interaction.user.id] = datetime.utcnow()

        existing_data = await db.get_value_from_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

        if existing_data:
            existing_data = json.loads(existing_data)
            ticket_data = existing_data.get("ticket_data")

        role_id = ticket_data["category_roles"].get(str(interaction.channel.category.id))
        role = interaction.guild.get_role(role_id)

        if role in interaction.user.roles or interaction.user.guild_permissions.manage_channels:
            embed = await db.build_embed(interaction.guild, title="<a:Loading:1247220769511964673> Deleting Ticket", description="This ticket is being deleted...")
            await interaction.response.send_message(embed=embed)

            open_tickets = ticket_data["open_tickets"]
            open_tickets_list = [channel_id for user_id, channel_id in open_tickets.items()]

            if interaction.channel.id in open_tickets_list:
                open_tickets = {user_id: ch_id for user_id, ch_id in open_tickets.items() if ch_id != interaction.channel.id}

                search_value = interaction.channel.id
                key_found = next((key for key, value in ticket_data["open_tickets"].items() if value == search_value), None)

                transcript_channel = discord.utils.get(interaction.channel.category.channels, name="transcripts")
                if transcript_channel is None:
                    transcript_channel = await interaction.guild.create_text_channel(name="transcripts", reason="Transcript Channel Missing", category=interaction.channel.category)
                file_channel = self.client.get_channel(1208740085047234621)

                transcript = await chat_exporter.export(interaction.channel, tz_info='UTC')
                transcript_file = discord.File(io.BytesIO(transcript.encode()), filename=f"{interaction.channel.name}.html")
                message = await file_channel.send(file=transcript_file)
                attachment = message.attachments[0]

                created_datetime = interaction.channel.created_at
                deleted_datetime = datetime.now(pytz.utc)
                duration = deleted_datetime - created_datetime

                def format_duration(duration):
                    days = duration.days
                    seconds = duration.seconds
                    minutes, seconds = divmod(seconds, 60)
                    hours, minutes = divmod(minutes, 60)

                    if days > 0:
                        return f"{days} {'Day' if days == 1 else 'Days'}"
                    elif hours > 0:
                        return f"{hours} {'Hour' if hours == 1 else 'Hours'}"
                    elif minutes > 0:
                        return f"{minutes} {'Minute' if minutes == 1 else 'Minutes'}"
                    else:
                        return f"{seconds} {'Second' if seconds == 1 else 'Seconds'}"

                formatted_duration = format_duration(duration)

                view = discord.ui.View()
                buttons = [
                    discord.ui.Button(label="View Transcript", url=f"https://api.xetrinityz.com/transcripts?url={attachment.url}", emoji="📋", style=discord.ButtonStyle.link),
                    discord.ui.Button(label="Download Transcript", url=f"https://api.xetrinityz.com/transcripts?url={attachment.url}&download", emoji="⬇", style=discord.ButtonStyle.link)
                ]
                view.add_item(buttons[0])
                view.add_item(buttons[1])

                user = await self.client.get_or_fetch_user(int(key_found))
                embed = await db.build_embed(interaction.guild, title="📋 Ticket Transcript")
                embed.add_field(name="Server", value=interaction.guild.name, inline=True)
                embed.add_field(name="Category", value=interaction.channel.category.name, inline=True)
                embed.add_field(name="Ticket", value=interaction.channel.name, inline=True)
                embed.add_field(name="Closer", value=f"{interaction.user.display_name}\n`({interaction.user.id})`", inline=True)
                embed.add_field(name="Creator", value=f"{user.display_name}\n`({user.id})`", inline=True)
                embed.add_field(name="Duration", value=formatted_duration, inline=True)
                await transcript_channel.send(embed=embed, view=view)

                try:
                    await user.send(embed=embed, view=view)
                except:
                    pass

                await interaction.channel.delete()
                ticket_data["open_tickets"] = open_tickets
                await db.update_value_in_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS", "ticket_data", ticket_data)
                await db.update_guild_leaderboard_stat(interaction.guild, "tickets_resolved", 1)

            else:
                if interaction.channel:
                    await interaction.channel.delete()
        else:
            embed = await db.build_embed(interaction.guild, title="<a:Information:1247223152367636541> Close Request", description=f"{interaction.user.mention} has requested this ticket to be closed.")
            await interaction.response.send_message(embed=embed)


    async def close_button_callback(self, button, interaction: discord.Interaction):

        # Check cooldown
        if interaction.user.id in interaction_cooldowns and datetime.utcnow() - interaction_cooldowns[interaction.user.id] < timedelta(seconds=5):
            remaining_time = (interaction_cooldowns[interaction.user.id] + timedelta(seconds=5) - datetime.utcnow()).seconds
            embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description=f"You are on cooldown. Please try again in **{remaining_time}** seconds.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await interaction.message.edit(view=discord.ui.View.from_message(interaction.message))
            return

        interaction_cooldowns[interaction.user.id] = datetime.utcnow()

        existing_data = await db.get_value_from_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

        if existing_data:
            existing_data = json.loads(existing_data)
            ticket_data = existing_data.get("ticket_data")

            role_id = ticket_data["category_roles"].get(str(interaction.channel.category.id))
            role = interaction.guild.get_role(role_id)

            if role in interaction.user.roles or interaction.user.guild_permissions.manage_channels:
                embed = await db.build_embed(interaction.guild, title="<a:Loading:1247220769511964673> Closing Ticket", description="This ticket is being closed...")
                await interaction.response.send_message(embed=embed)

                open_tickets = ticket_data["open_tickets"]
                open_tickets_list = [channel_id for user_id, channel_id in open_tickets.items()]

                if interaction.channel.id in open_tickets_list:
                    open_tickets = {user_id: ch_id for user_id, ch_id in open_tickets.items() if ch_id != interaction.channel.id}

                    search_value = interaction.channel.id
                    key_found = next((key for key, value in ticket_data["open_tickets"].items() if value == search_value), None)

                    transcript_channel = discord.utils.get(interaction.channel.category.channels, name="transcripts")
                    if transcript_channel is None:
                        transcript_channel = await interaction.guild.create_text_channel(name="transcripts", reason="Transcript Channel Missing", category=interaction.channel.category)
                    file_channel = self.client.get_channel(1208740085047234621)

                    transcript = await chat_exporter.export(interaction.channel, tz_info='UTC')
                    transcript_file = discord.File(io.BytesIO(transcript.encode()), filename=f"{interaction.channel.name}.html")
                    message = await file_channel.send(file=transcript_file)
                    attachment = message.attachments[0]

                    created_datetime = interaction.channel.created_at
                    deleted_datetime = datetime.now(pytz.utc)
                    duration = deleted_datetime - created_datetime

                    def format_duration(duration):
                        days = duration.days
                        seconds = duration.seconds
                        minutes, seconds = divmod(seconds, 60)
                        hours, minutes = divmod(minutes, 60)

                        if days > 0:
                            return f"{days} {'Day' if days == 1 else 'Days'}"
                        elif hours > 0:
                            return f"{hours} {'Hour' if hours == 1 else 'Hours'}"
                        elif minutes > 0:
                            return f"{minutes} {'Minute' if minutes == 1 else 'Minutes'}"
                        else:
                            return f"{seconds} {'Second' if seconds == 1 else 'Seconds'}"

                    formatted_duration = format_duration(duration)

                    view = discord.ui.View()
                    buttons = [
                        discord.ui.Button(label="View Transcript", url=f"https://api.xetrinityz.com/transcripts?url={attachment.url}", emoji="📋", style=discord.ButtonStyle.link),
                        discord.ui.Button(label="Download Transcript", url=f"https://api.xetrinityz.com/transcripts?url={attachment.url}&download", emoji="⬇", style=discord.ButtonStyle.link)
                    ]
                    view.add_item(buttons[0])
                    view.add_item(buttons[1])

                    user = await self.client.get_or_fetch_user(int(key_found))
                    embed = await db.build_embed(interaction.guild, title="📋 Ticket Transcript")
                    embed.add_field(name="Server", value=interaction.guild.name, inline=True)
                    embed.add_field(name="Category", value=interaction.channel.category.name, inline=True)
                    embed.add_field(name="Ticket", value=interaction.channel.name, inline=True)
                    embed.add_field(name="Closer", value=f"{interaction.user.display_name}\n`({interaction.user.id})`", inline=True)
                    embed.add_field(name="Creator", value=f"{user.display_name}\n`({user.id})`", inline=True)
                    embed.add_field(name="Duration", value=formatted_duration, inline=True)
                    await transcript_channel.send(embed=embed, view=view)

                    try:
                        await user.send(embed=embed, view=view)
                    except:
                        pass

                    if interaction.channel.topic is None:
                        await interaction.channel.edit(topic=user.id)

                    try:
                        await interaction.channel.set_permissions(user, view_channel=False, send_messages=False, attach_files=False, embed_links=False)
                    except:
                        pass

                    this_view = discord.ui.View.from_message(interaction.message)
                    close_button = this_view.get_item("ticket_close")
                    close_button.label = "Open Ticket"
                    close_button.emoji = "<a:Locked:1209072654808776714>"
                    close_button.custom_id = "ticket_open"
                    close_button.style = discord.ButtonStyle.green

                    embed = await db.build_embed(interaction.guild, title="<a:Locked:1209072654808776714> Ticket Closed", description=f"This ticket has been closed by {interaction.user.mention}.")
                    await interaction.edit_original_response(embed=embed)
                    await db.update_guild_leaderboard_stat(interaction.guild, "tickets_resolved", 1)
                    await interaction.message.edit(view=this_view)

                    ticket_data["open_tickets"] = open_tickets
                    await db.update_value_in_table(str(interaction.guild.id), "ServerConfigurations", "Setting", "Feature", "TICKETS", "ticket_data", ticket_data)

                else:
                    if "ticket" in interaction.channel.name:
                        embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description="This ticket was already closed.")
                        await interaction.edit_original_response(embed=embed)
                    else:
                        embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description="This is not a ticket channel.")
                        await interaction.edit_original_response(embed=embed)

            else:
                embed = await db.build_embed(interaction.guild, title="<a:Information:1247223152367636541> Close Request", description=f"{interaction.user.mention} has requested this ticket to be closed.")
                await interaction.response.send_message(embed=embed)


    async def open_button_callback(self, button, interaction: discord.Interaction):

        # Check cooldown
        if interaction.user.id in interaction_cooldowns and datetime.utcnow() - interaction_cooldowns[interaction.user.id] < timedelta(seconds=5):
            remaining_time = (interaction_cooldowns[interaction.user.id] + timedelta(seconds=5) - datetime.utcnow()).seconds
            embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description=f"You are on cooldown. Please try again in **{remaining_time}** seconds.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await interaction.message.edit(view=discord.ui.View.from_message(interaction.message))
            return

        interaction_cooldowns[interaction.user.id] = datetime.utcnow()

        existing_data = await db.get_value_from_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

        if existing_data:
            existing_data = json.loads(existing_data)
            ticket_data = existing_data.get("ticket_data")

        role_id = ticket_data["category_roles"].get(str(interaction.channel.category.id))
        role = interaction.guild.get_role(role_id)

        if role in interaction.user.roles or interaction.user.guild_permissions.manage_channels:
            embed = await db.build_embed(interaction.guild, title="<a:Loading:1247220769511964673> Opening Ticket", description="This ticket is being re-opened...")
            await interaction.response.send_message(embed=embed)

            user_id = int(interaction.channel.topic)
            user = interaction.guild.get_member(user_id)

            if user is None:
                embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description="The ticket creator is no longer in the server.")
                return await interaction.edit_original_response(embed=embed)

            await interaction.channel.set_permissions(user, view_channel=True, send_messages=True, attach_files=True, embed_links=True)

            this_view = discord.ui.View.from_message(interaction.message)
            open_button = this_view.get_item("ticket_open")
            open_button.label = "Close Ticket"
            open_button.emoji = "<a:Locked:1209072654808776714>"
            open_button.custom_id = "ticket_close"
            open_button.style = discord.ButtonStyle.red

            user_id = str(user_id)

            ticket_data["open_tickets"][str(user_id)] = interaction.channel.id
            await db.update_value_in_table(str(interaction.guild.id), "ServerConfigurations", "Setting", "Feature", "TICKETS", "ticket_data", ticket_data)

            embed = await db.build_embed(interaction.guild, title="<a:Locked:1209072654808776714> Ticket Opened", description=f"This ticket has been re-opened by {interaction.user.mention}.")
            await interaction.edit_original_response(embed=embed)
            await db.update_guild_leaderboard_stat(interaction.guild, "tickets_resolved", -1)
            await interaction.message.edit(view=this_view)
        else:
            embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description="You lack the required role to open this ticket.")
            await interaction.response.send_message(embed=embed, ephemeral=True)


    async def claim_button_callback(self, button, interaction: discord.Interaction):

        # Check cooldown
        if interaction.user.id in interaction_cooldowns and datetime.utcnow() - interaction_cooldowns[interaction.user.id] < timedelta(seconds=5):
            remaining_time = (interaction_cooldowns[interaction.user.id] + timedelta(seconds=5) - datetime.utcnow()).seconds
            embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description=f"You are on cooldown. Please try again in **{remaining_time}** seconds.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await interaction.message.edit(view=discord.ui.View.from_message(interaction.message))
            return

        interaction_cooldowns[interaction.user.id] = datetime.utcnow()
        
        existing_data = await db.get_value_from_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

        if existing_data:
            existing_data = json.loads(existing_data)
            ticket_data = existing_data.get("ticket_data")

        role_id = ticket_data["category_roles"].get(str(interaction.channel.category.id))
        role = interaction.guild.get_role(role_id)

        if role in interaction.user.roles or interaction.user.guild_permissions.manage_channels:
            embed = await db.build_embed(interaction.guild, title="<a:Loading:1247220769511964673> Claiming Ticket", description="This ticket is being claimed...")
            await interaction.response.send_message(embed=embed)

            await db.update_leaderboard_stat(interaction.user, "tickets_claimed", 1)

            view = discord.ui.View.from_message(interaction.message)
            button = view.children[0]
            button.label = "Unclaim Ticket"
            button.emoji = f"{error_emoji}"
            button.custom_id = "ticket_unclaim"
            button.style = discord.ButtonStyle.blurple

            embed = await db.build_embed(interaction.guild, title=f"{success_emoji} Ticket Claimed", description=f"This ticket has been **claimed** by {interaction.user.mention}.")
            await interaction.edit_original_response(embed=embed)
            await interaction.message.edit(view=view)
        else:
            embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description="You lack the required role to claim this ticket.")
            await interaction.response.send_message(embed=embed, ephemeral=True)


    async def unclaim_button_callback(self, button, interaction: discord.Interaction):

        # Check cooldown
        if interaction.user.id in interaction_cooldowns and datetime.utcnow() - interaction_cooldowns[interaction.user.id] < timedelta(seconds=5):
            remaining_time = (interaction_cooldowns[interaction.user.id] + timedelta(seconds=5) - datetime.utcnow()).seconds
            embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description=f"You are on cooldown. Please try again in **{remaining_time}** seconds.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await interaction.message.edit(view=discord.ui.View.from_message(interaction.message))
            return

        interaction_cooldowns[interaction.user.id] = datetime.utcnow()
        
        existing_data = await db.get_value_from_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

        if existing_data:
            existing_data = json.loads(existing_data)
            ticket_data = existing_data.get("ticket_data")

        role_id = ticket_data["category_roles"].get(str(interaction.channel.category.id))
        role = interaction.guild.get_role(role_id)

        if role in interaction.user.roles or interaction.user.guild_permissions.manage_channels:
            embed = await db.build_embed(interaction.guild, title="<a:Loading:1247220769511964673> Unclaiming Ticket", description="This ticket is being unclaimed...")
            await interaction.response.send_message(embed=embed)

            await db.update_leaderboard_stat(interaction.user, "tickets_claimed", -1)

            view = discord.ui.View.from_message(interaction.message)
            button = view.children[0]
            button.label = "Claim Ticket"
            button.emoji = f"{success_emoji}"
            button.custom_id = "ticket_claim"
            button.style = discord.ButtonStyle.blurple

            embed = await db.build_embed(interaction.guild, title=f"{success_emoji} Ticket Unclaimed", description=f"This ticket has been **unclaimed** by {interaction.user.mention}.")
            await interaction.edit_original_response(embed=embed)
            await interaction.message.edit(view=view)
        else:
            embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description="You lack the required role to unclaim this ticket.")
            await interaction.response.send_message(embed=embed, ephemeral=True)