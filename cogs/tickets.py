# Discord Imports
from discord.utils import basic_autocomplete
from discord.ext import commands
from discord.ui import Button
from discord import Option
import discord

# Standard / Third-Party Library Imports
from datetime import datetime, timedelta
import chat_exporter
import json
import pytz
import io

# Local Module Imports
from utils.tickethelper import format_ticket_counter, get_category_channels
from EmbedBuilder import embedTool
from utils.database import Database
from utils.views import cancel_ticket_timer
from utils.lists import *
from Bot import is_blocked

db = Database()

class tickets(commands.Cog):
    def __init__(self, client):
        self.client = client

    tpanelSubCommands = discord.SlashCommandGroup("tpanel", "Setup, Reset, Move, Category Add, Category Remove, Category Edit.", default_member_permissions=discord.Permissions(administrator=True))
    tpanelCategory = tpanelSubCommands.create_subgroup("category", "Add, Edit, remove")

    ticketSubCommands = discord.SlashCommandGroup("ticket", "Open, Delete, Add Role, Add Member, Remove Role, Remove Member, Move, Find.", default_member_permissions=discord.Permissions(manage_channels=True, manage_roles=True))
    ticketAdd = ticketSubCommands.create_subgroup("add", "Member, Role")
    ticketRemove = ticketSubCommands.create_subgroup("remove", "Member, Role")

    @tpanelSubCommands.command(name="setup", description="Setup the ticket system.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_permissions(external_emojis=True, manage_channels=True, manage_roles=True, send_messages=True)
    async def setup(self, ctx: discord.ApplicationContext,
        channel: Option(discord.TextChannel, "The channel to send the ticket panel to."),
        name: Option(str, "The name of the ticket category button."),
        emoji: Option(str, "The emoji to use on the button."),
        color: Option(str, "The color of the button.", choices=["Blue", "Grey", "Green", "Red"],),
        role: Option(discord.Role, "The role that has access to this category.")):

        try:
            existing_data = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

            if existing_data:
                existing_data = json.loads(existing_data)
                ticket_data = existing_data.get("ticket_data")

            if ticket_data["ticket_panel"]["Channel ID"] is not None:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You already have a ticket panel setup, use </tpanel reset:1174737712473985119> to create a new one.")
                await ctx.respond(embed=embed, ephemeral=True)
                return

            if "category_roles" not in ticket_data:
                ticket_data["category_roles"] = {}

            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                role: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True)}
            
            category = await ctx.guild.create_category(name=name, overwrites=overwrites, reason="Create Ticket Category")
            await ctx.guild.create_text_channel(name="transcripts", reason="Ticket Category Created", category=category, overwrites=overwrites)

            ticket_data["category_roles"][str(category.id)] = role.id

            if color == "Blue":
                style = discord.ButtonStyle.blurple
            elif color == "Grey":
                style = discord.ButtonStyle.grey
            elif color == "Green":
                style = discord.ButtonStyle.green
            elif color == "Red":
                style = discord.ButtonStyle.red

            view = discord.ui.View(timeout=None)
            cat1 = Button(label=name, emoji=emoji, style=style, custom_id=f"ticket_category|{category.id}")
            view.add_item(cat1)

            user_embed = await db.build_embed(ctx.author.guild, title=f"Embed Builder", description=f"Click the buttons below to build your ticket panel embed.")
            embed_tool = embedTool.EmbedToolView(channel_or_message=channel, is_new_embed=True, custom=None, view=view, ctx=ctx)
            await ctx.respond(embed=user_embed, view=embed_tool, ephemeral=True)

            # Update the database once after all operations are successful.
            await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS", "ticket_data", ticket_data)

        except discord.HTTPException:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The emoji provided was invalid.")
            await ctx.respond(embed=embed, ephemeral=True)

        except Exception as e:
            print("[tpanel_setup]: ", e)
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Something went wrong, please try again later.")
            await ctx.respond(embed=embed, ephemeral=True)


    @tpanelSubCommands.command(name="reset", description="Reset the ticket system.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def reset_panel(self, ctx: discord.ApplicationContext):

        try:
            existing_data = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

            embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Resetting Ticket Panel", description="Resetting your ticket panel...")
            await ctx.respond(embed=embed)

            if existing_data:
                existing_data = json.loads(existing_data)
                ticket_data = existing_data.get("ticket_data")

            channel_id = ticket_data["ticket_panel"]["Channel ID"]
            message_id = ticket_data["ticket_panel"]["Message ID"]

            if channel_id is not None and message_id is not None:
                try:
                    channel = ctx.guild.get_channel(channel_id)
                    message = await channel.fetch_message(message_id)
                    await message.delete()
                except discord.NotFound:
                    pass

            category_roles = ticket_data["category_roles"]

            for category_id, _ in category_roles.items():
                category = ctx.guild.get_channel(int(category_id))

                if category and isinstance(category, discord.CategoryChannel):
                    for channel in category.channels:
                        await channel.delete()
                    await category.delete()

            ticket_data["category_roles"] = {}

            default_tickets = {
                    "category_roles": {},
                    "open_tickets": {},
                    "ticket_panel": {"Channel ID": None, "Message ID": None},
                    "ticket_counter": 0}

            await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS", "ticket_data", default_tickets)
            embed = await db.build_embed(ctx.guild, title="🔃 Ticket Panel Reset", description="The ticket panel has been reset.")
            await ctx.edit(embed=embed)

        except Exception as e:
            print("[tpanel_reset]: ", e)
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Something went wrong, please try again later.")
            await ctx.respond(embed=embed, ephemeral=True)


    @tpanelSubCommands.command(name="move", description="Resend the ticket panel to a new channel.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def move_panel(self, ctx: discord.ApplicationContext, channel: Option(discord.TextChannel, "The channel to send the ticket panel to.")):
        try:
            existing_data = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

            embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Moving Ticket Panel", description=f"Moving your ticket panel to {channel.mention}...")
            await ctx.respond(embed=embed)

            if existing_data:
                existing_data = json.loads(existing_data)
                ticket_data = existing_data.get("ticket_data")

                channel_id = ticket_data["ticket_panel"]["Channel ID"]
                message_id = ticket_data["ticket_panel"]["Message ID"]

                if channel_id is not None and message_id is not None:
                    panel_channel = ctx.guild.get_channel(channel_id)
                    try:
                        message = await panel_channel.fetch_message(message_id)
                    except discord.NotFound:
                        embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The panel channel or message was not found.")
                        await ctx.edit(embed=embed)
                        return

                    panel_embed = message.embeds[0]
                    panel_view = discord.ui.View.from_message(message)
                    panel_content = message.content
                    new_panel = await channel.send(content=panel_content, embed=panel_embed, view=panel_view)
                    await message.delete()
                else:
                    embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You need to setup a ticket panel first.")
                    await ctx.edit(embed=embed)
                    return

                ticket_data["ticket_panel"]["Channel ID"] = channel.id
                ticket_data["ticket_panel"]["Message ID"] = new_panel.id

                existing_data["ticket_data"] = ticket_data

                await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS", "ticket_data", existing_data["ticket_data"])
                embed = await db.build_embed(ctx.guild, title=f"{success_emoji} Ticket Panel Moved", description=f"The ticket panel has been moved to {channel.mention}.")
                await ctx.edit(embed=embed)

        except Exception as e:
            print("[tpanel_move]: ", e)
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Something went wrong, please try again later.")
            await ctx.respond(embed=embed, ephemeral=True)


    @ticketSubCommands.command(name="open", description="Open a ticket for a member.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def open_ticket(self, ctx: discord.ApplicationContext,
        member: Option(discord.Member, "The member to open the ticket for."),
        category: Option(str, "The ticket category.", autocomplete=basic_autocomplete(get_category_channels)), reason: Option(str, "The reason for opening the ticket.")):
        
        try:

            existing_data = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

            if existing_data:
                existing_data = json.loads(existing_data)
                ticket_data = existing_data.get("ticket_data")


            if ticket_data["ticket_panel"]["Channel ID"] is None:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You need to setup a ticket panel first. Use </tpanel setup:1174737712473985119> to get started. .")
                await ctx.respond(embed=embed, ephemeral=True)
                return
            
            if "category_roles" in ticket_data:
                category_roles = ticket_data["category_roles"]
                category_ids = [int(category_id) for category_id in category_roles.keys()]
                category_info = [f"{category.name}" for category in ctx.interaction.guild.categories if category.id in category_ids]

                if category not in category_info:
                    embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"There is no ticket category with the name **{category}**.")
                    return await ctx.respond(embed=embed, ephemeral=True)

            if member == ctx.guild.me or member == member.bot:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You can not open a ticket for a bot.")
                return await ctx.respond(embed=embed, ephemeral=True)
            
            category = discord.utils.get(ctx.guild.categories, name=category)

            embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Creating Ticket", description=f"Creating a ticket for {member.mention}...")
            await ctx.respond(embed=embed)

            role_id = ticket_data["category_roles"][str(category.id)]
            role = ctx.guild.get_role(role_id)

            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                member: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True), 
                role: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True)}
       
            ticket_data["ticket_counter"] = ticket_data["ticket_counter"] + 1
            ticket_number = format_ticket_counter(ticket_data["ticket_counter"])

            channel = await ctx.guild.create_text_channel(f"ticket-{member.name[:5].lower()}-{ticket_number}", reason=f"Ticket Channel Create", category=category, overwrites=overwrites)

            view = discord.ui.View(timeout=None)
            delButton = Button(label="Delete Ticket", custom_id="ticket_delete", emoji="🗑", style=discord.ButtonStyle.red)
            closeButton = Button(label="Close Ticket", custom_id="ticket_close", emoji="<a:Locked:1209072654808776714>", style=discord.ButtonStyle.red)
            claimButton = Button(label="Claim Ticket", custom_id="ticket_claim", emoji=f"{success_emoji}", style=discord.ButtonStyle.blurple)
            view.add_item(claimButton)
            view.add_item(closeButton)
            view.add_item(delButton)

            embed = await db.build_embed(ctx.guild, title=f"Ticket #{ticket_number} ({category.name})", description=f"Welcome {member.mention}, to your ticket!\n\nThank you for creating a ticket!\nSupport will be with you shortly.\n\n**Reason** ➭ {reason}")
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(f"{member.mention}, {role.mention}", embed=embed, view=view)

            ticket_data["open_tickets"][str(member.id)] = channel.id

            await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS", "ticket_data", ticket_data)

            embed = await db.build_embed(ctx.guild, title=f"{success_emoji} Ticket Opened", description=f"A ticket has been opened for {member.mention} ➭ {channel.mention}")
            await ctx.edit(embed=embed)

        except Exception as e:
            print("[ticket_open]: ", e)
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Something went wrong, please try again later.")
            await ctx.respond(embed=embed, ephemeral=True)


    @ticketSubCommands.command(name="move", description="Move a ticket to another category.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def move_ticket(self, ctx: discord.ApplicationContext, category: Option(str, "The ticket category.", autocomplete=basic_autocomplete(get_category_channels))):
        
        try:

            existing_data = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

            embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Moving Ticket", description=f"Moving ticket to **{category}**...")
            await ctx.respond(embed=embed)

            if existing_data:
                existing_data = json.loads(existing_data)
                ticket_data = existing_data.get("ticket_data")
                open_tickets = ticket_data["open_tickets"]

            if ticket_data["ticket_panel"]["Channel ID"] is None:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You need to setup a ticket panel first. Use </tpanel setup:1174737712473985119> to get started.")
                await ctx.edit(embed=embed)
                return
            
            if ctx.channel.id not in open_tickets.values():
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="This is not a ticket channel.")
                await ctx.edit(embed=embed)
                return
            
            if "category_roles" in ticket_data:
                category_roles = ticket_data["category_roles"]
                category_ids = [int(category_id) for category_id in category_roles.keys()]
                category_info = [f"{category.name}" for category in ctx.interaction.guild.categories if category.id in category_ids]

                if category not in category_info:
                    embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"There is no ticket category with the name **{category}**.")
                    await ctx.edit(embed=embed)
                    return 
            
            if ctx.channel.category.name == category:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"This channel is already in the **{category}** category.")
                await ctx.edit(embed=embed)
                return

            category_ch = discord.utils.get(ctx.guild.categories, name=category)
            role_id = ticket_data["category_roles"][str(category_ch.id)]
            user_id = [user_id for user_id, channel_id in open_tickets.items() if channel_id == ctx.channel.id][0]
            role = ctx.guild.get_role(role_id)
            member = ctx.guild.get_member(int(user_id))

            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                member: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True), 
                role: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True)}
    
            await ctx.channel.edit(reason="Ticket Channel Move", category=category_ch, overwrites=overwrites)

            embed = await db.build_embed(ctx.guild, title=f"{success_emoji} Ticket Moved", description=f"This ticket has been moved to **{category_ch}** by {ctx.author.mention}.")
            await ctx.edit(embed=embed)

        except Exception as e:
            print("[ticket_move]: ", e)
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Something went wrong, please try again later.")
            await ctx.edit(embed=embed)


    @ticketSubCommands.command(name="delete", description="Delete an open ticket.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def closetime_ticket(self, ctx: discord.ApplicationContext, timer: Option(str, "The amount of time before the ticket is deleted.", choices=["Now", "60 Seconds", "5 Minutes", "10 Minutes", "30 Minutes", "1 Hour", "5 Hours", "10 Hours", "1 Day"])):
        
        try:
            existing_data = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

            if existing_data:
                existing_data = json.loads(existing_data)
                ticket_data = existing_data.get("ticket_data")
                open_tickets = ticket_data["open_tickets"]

            open_tickets_list = [(channel_id) for user_id, channel_id in open_tickets.items()]

            if ctx.channel.id in open_tickets_list:
                if timer == "Now":
                    embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Deleting Ticket", description="This ticket is being deleted...")
                    await ctx.respond(embed=embed)

                    open_tickets = {user_id: ch_id for user_id, ch_id in open_tickets.items() if ch_id != ctx.channel.id}

                    search_value = ctx.channel.id
                    key_found = None

                    for key, value in ticket_data["open_tickets"].items():
                        if value == search_value:
                            key_found = key
                            break

                    transcriptChannel = discord.utils.get(ctx.channel.category.channels, name="transcripts")
                    fileChannel = self.client.get_channel(1153895371181928508)

                    transcript = await chat_exporter.export(ctx.channel, tz_info='UTC')
                    transcript_file = discord.File(io.BytesIO(transcript.encode()), filename=f"{ctx.channel.name}.html")
                    message = await fileChannel.send(file=transcript_file)
                    attachment = message.attachments[0]

                    created_datetime = ctx.channel.created_at
                    deleted_datetime = datetime.now(pytz.utc)
                    duration = deleted_datetime - created_datetime

                    def format_duration(duration):
                        days = duration.days
                        seconds = duration.seconds
                        minutes, seconds = divmod(seconds, 60)
                        hours, minutes = divmod(minutes, 60)

                        if days > 0:
                            if days == 1:
                                return f"{days} Day"
                            else:
                                return f"{days} Days"
                        elif hours > 0:
                            if hours == 1:
                                return f"{hours} Hour"
                            else:
                                return f"{hours} Hours"
                        elif minutes > 0:
                            if minutes == 1:
                                return f"{minutes} Minute"
                            else:
                                return f"{minutes} Minutes"
                        else:
                            if seconds == 1:
                                return f"{seconds} Second"
                            else:
                                return f"{seconds} Seconds"

                    formatted_duration = format_duration(duration)

                    view = discord.ui.View()
                    new_button = discord.ui.Button(label="View Transcript", url=f"https://api.xetrinityz.com/transcripts?url={attachment.url}", emoji="📋", style=discord.ButtonStyle.link)
                    download_button = discord.ui.Button(label="Download Transcript", url=f"https://api.xetrinityz.com/transcripts?url={attachment.url}&download", emoji="⬇", style=discord.ButtonStyle.link)
                    view.add_item(new_button)
                    view.add_item(download_button)

                    user = await self.client.get_or_fetch_user(int(key_found))
                    embed = await db.build_embed(ctx.guild, title="📋 Ticket Transcript")
                    embed.add_field(name="Server", value=ctx.guild.name, inline=True)
                    embed.add_field(name="Category", value=ctx.channel.category.name, inline=True)
                    embed.add_field(name="Ticket", value=ctx.channel.name, inline=True)
                    embed.add_field(name="Closer", value=f"{ctx.user.display_name}\n`({ctx.user.id})`", inline=True)
                    embed.add_field(name="Creator", value=f"{user.display_name}\n`({user.id})`", inline=True)
                    embed.add_field(name="Duration", value=formatted_duration, inline=True)
                    await transcriptChannel.send(embed=embed, view=view)

                    try:
                        await user.send(embed=embed, view=view)
                    except:
                        pass

                    ticket_data["open_tickets"] = open_tickets
                    await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS", "ticket_data", ticket_data)

                    await ctx.channel.delete()
                    await db.update_guild_leaderboard_stat(ctx.guild, "tickets_resolved", 1)

                else:

                    ticket_creator_id = next((key for key, value in open_tickets.items() if value == ctx.channel.id), None)
                    time_intervals = {
                        "60 Seconds": 60,
                        "5 Minutes": 300,
                        "10 Minutes": 600,
                        "30 Minutes": 1800,
                        "1 Hour": 3600,
                        "5 Hours": 18000,
                        "10 Hours": 36000,
                        "1 Day": 86400,
                    }

                    time_interval = time_intervals.get(timer)

                    # Get current time and calculate close time
                    current_time = datetime.now()
                    close_time = current_time + timedelta(seconds=time_interval)
                    close_timestamp = round(close_time.timestamp())

                    # Check if the channel already has timers, if not, create a list
                    if ctx.channel.id not in timed_close_tickets:
                        timed_close_tickets[ctx.channel.id] = []

                    # Add the close time and ticket creator ID to the list of timers for the channel

                    embed = await db.build_embed(ctx.author.guild, title="<a:Cooldown:1153886516456722443> Ticket Scheduled for Closure", description=f"This ticket will automatically be deleted <t:{close_timestamp}:R>. Sending a message within your ticket will cancel the timer.")
                    close_timer_embed = await ctx.channel.send(content=f"<@{ticket_creator_id}>", embed=embed, view=cancel_ticket_timer())
                    await ctx.respond("Timer Started", delete_after=0)
                    timed_close_tickets[ctx.channel.id].append((close_time, ticket_creator_id, close_timer_embed.id))
            else:
                embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="This is not a ticket channel.")
                await ctx.respond(embed=embed, ephemeral=True)

        except Exception as e:
            print("[closetime_ticket]: ", e)
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Something went wrong, please try again later.")
            await ctx.respond(embed=embed, ephemeral=True)


    @ticketAdd.command(name="member", description="Add a member to the ticket.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    async def ticket_add_member(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to add to the ticket.")):
        
        try:
            existing_data = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

            if existing_data:
                existing_data = json.loads(existing_data)
                ticket_data = existing_data.get("ticket_data")

            open_tickets = ticket_data["open_tickets"]

            open_tickets_list = [(channel_id) for user_id, channel_id in open_tickets.items()]

            if ctx.channel.id in open_tickets_list:
                await ctx.channel.set_permissions(member, view_channel=True, send_messages=True, attach_files=True, embed_links=True)

                embed = await db.build_embed(ctx.guild, title=f"{success_emoji} Member Added", description=f"{member.mention} has been **added** to the ticket by {ctx.author.mention}.")
                await ctx.respond(embed=embed)

            else:
                embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="This is not a ticket channel.")
                await ctx.respond(embed=embed, ephemeral=True)

        except Exception as e:
            print("[ticket_add_member]: ", e)
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Something went wrong, please try again later.")
            await ctx.respond(embed=embed, ephemeral=True)


    @ticketRemove.command(name="member", description="Remove a member from the ticket.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    async def ticket_remove_member(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to remove from the ticket.")):
        
        try:
            existing_data = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

            if existing_data:
                existing_data = json.loads(existing_data)
                ticket_data = existing_data.get("ticket_data")

            open_tickets = ticket_data["open_tickets"]

            open_tickets_list = [(channel_id) for user_id, channel_id in open_tickets.items()]

            if ctx.channel.id in open_tickets_list:
                await ctx.channel.set_permissions(member, view_channel=False, send_messages=False, attach_files=False, embed_links=False)

                embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Member Removed", description=f"{member.mention} has been **removed** from the ticket by {ctx.author.mention}.")
                await ctx.respond(embed=embed)

            else:
                embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="This is not a ticket channel.")
                await ctx.respond(embed=embed, ephemeral=True)

        except Exception as e:
            print("[ticket_remove_member]: ", e)
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Something went wrong, please try again later.")
            await ctx.respond(embed=embed, ephemeral=True)


    @ticketAdd.command(name="role", description="Add a role to the ticket.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    async def ticket_add_role(self, ctx: discord.ApplicationContext, role: Option(discord.Role, "The role to add to the ticket.")):
        
        try:
            existing_data = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

            if existing_data:
                existing_data = json.loads(existing_data)
                ticket_data = existing_data.get("ticket_data")

            open_tickets = ticket_data["open_tickets"]

            open_tickets_list = [(channel_id) for user_id, channel_id in open_tickets.items()]

            if ctx.channel.id in open_tickets_list:
                await ctx.channel.set_permissions(role, view_channel=True, send_messages=True, attach_files=True, embed_links=True)

                embed = await db.build_embed(ctx.guild, title=f"{success_emoji} Role Added", description=f"The {role.mention} role has been **added** to the ticket by {ctx.author.mention}.")
                await ctx.respond(embed=embed)

            else:
                embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="This is not a ticket channel.")
                await ctx.respond(embed=embed, ephemeral=True)

        except Exception as e:
            print("[ticket_add_role]: ", e)
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Something went wrong, please try again later.")
            await ctx.respond(embed=embed, ephemeral=True)


    @ticketRemove.command(name="role", description="Remove a role from the ticket.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    async def ticket_remove_role(self, ctx: discord.ApplicationContext, role: Option(discord.Role, "The role to remove from the ticket.")):

        try:
            existing_data = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

            if existing_data:
                existing_data = json.loads(existing_data)
                ticket_data = existing_data.get("ticket_data")

            open_tickets = ticket_data["open_tickets"]

            open_tickets_list = [(channel_id) for user_id, channel_id in open_tickets.items()]

            if ctx.channel.id in open_tickets_list:
                await ctx.channel.set_permissions(role, view_channel=False, send_messages=False, attach_files=False, embed_links=False)

                embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Role Removed", description=f"The {role.mention} role has been **removed** from the ticket by {ctx.author.mention}.")
                await ctx.respond(embed=embed)

            else:
                embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="This is not a ticket channel.")
                await ctx.respond(embed=embed, ephemeral=True)

        except Exception as e:
            print("[ticket_remove_role]: ", e)
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Something went wrong, please try again later.")
            await ctx.respond(embed=embed, ephemeral=True)


    @tpanelCategory.command(name="add", description="Add a ticket category.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def add_tcategory(self, ctx: discord.ApplicationContext,
        name: Option(str, "The name of the ticket category button."),
        emoji: Option(str, "The emoji to use on the button."),
        color: Option(str, "The color of the button.", choices=["Blue", "Grey", "Green", "Red"]), 
        role: Option(discord.Role, "The role that has access to this category.")):

        try:
            existing_data = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

            embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Adding Category", description=f"Adding the **{name}** category to your ticket panel...")
            await ctx.respond(embed=embed)

            if existing_data:
                existing_data = json.loads(existing_data)
                ticket_data = existing_data.get("ticket_data")

            panel_channel_id = ticket_data["ticket_panel"]["Channel ID"]
            panel_message_id = ticket_data["ticket_panel"]["Message ID"]

            panel_channel = ctx.guild.get_channel(panel_channel_id)
            panel_message = None

            if panel_message_id:
                try:
                    panel_message = await panel_channel.fetch_message(panel_message_id)
                except discord.NotFound:
                    panel_message = None

            if not panel_channel or not panel_message:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Ticket panel not found. Make sure to set up the ticket panel first using </tpanel setup:1174737712473985119>.")
                await ctx.edit(embed=embed)
                return

            if color == "Blue":
                style = discord.ButtonStyle.blurple
            elif color == "Grey":
                style = discord.ButtonStyle.grey
            elif color == "Green":
                style = discord.ButtonStyle.green
            elif color == "Red":
                style = discord.ButtonStyle.red

            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                role: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True)}
            
            category = await ctx.guild.create_category(name=name, overwrites=overwrites, reason="Create Ticket Category")
            await ctx.guild.create_text_channel(name="transcripts", reason="Ticket Category Created", category=category, overwrites=overwrites)

            view = discord.ui.View.from_message(panel_message)
            cat1 = Button(label=name, emoji=emoji, style=style, custom_id=f"ticket_category|{category.id}")
            view.add_item(cat1)

            ticket_data["category_roles"][category.id] = role.id
            await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS", "ticket_data", ticket_data)

            await panel_message.edit(view=view)

            embed = await db.build_embed(ctx.guild, title=f"{success_emoji} Ticket Category Added", description=f"The **{category.name}** category has been added to the ticket panel.")
            await ctx.edit(embed=embed)

        except discord.HTTPException as e:
            if e.code == 50035:
                await ctx.respond(embed=await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The emoji you provided was invalid."), ephemeral=True)
            else:
                await ctx.respond(embed=await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Unknown HTTP error occured."), ephemeral=True)

        except Exception as e:
            print("[add_tcategory]: ", e)
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Something went wrong, please try again later.")
            await ctx.edit(embed=embed)


    @tpanelCategory.command(name="edit", description="Edit a ticket category.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def edit_tcategory(self, ctx: discord.ApplicationContext,
        category: Option(str, "The ticket category to edit.", autocomplete=basic_autocomplete(get_category_channels)),
        name: Option(str, "The name of the ticket category button."),
        emoji: Option(str, "The emoji to use on the button."),
        color: Option(str, "The color of the button.", choices=["Blue", "Grey", "Green", "Red"]), 
        role: Option(discord.Role, "The role that has access to this category.")):

        try:
            existing_data = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

            embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Updating Category", description=f"Updating the **{category}** category...")
            await ctx.respond(embed=embed)

            if existing_data:
                existing_data = json.loads(existing_data)
                ticket_data = existing_data.get("ticket_data")

            panel_channel_id = ticket_data["ticket_panel"]["Channel ID"]
            panel_message_id = ticket_data["ticket_panel"]["Message ID"]

            panel_channel = ctx.guild.get_channel(panel_channel_id)
            panel_message = None

            if panel_message_id:
                try:
                    panel_message = await panel_channel.fetch_message(panel_message_id)
                except discord.NotFound:
                    panel_message = None

            if not panel_channel or not panel_message:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Ticket panel channel or message not found. Make sure to set up the ticket panel first.")
                await ctx.edit(embed=embed)
                return
            
            if "category_roles" in ticket_data:
                category_roles = ticket_data["category_roles"]
                category_ids = [int(category_id) for category_id in category_roles.keys()]
                category_info = [f"{category.name}" for category in ctx.interaction.guild.categories if category.id in category_ids]

                if category not in category_info:
                    embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"There is no ticket category with the name **{category}**.")
                    await ctx.edit(embed=embed)
                    return 

            if color == "Blue":
                style = discord.ButtonStyle.blurple
            elif color == "Grey":
                style = discord.ButtonStyle.grey
            elif color == "Green":
                style = discord.ButtonStyle.green
            elif color == "Red":
                style = discord.ButtonStyle.red

            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                role: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True)}
            
            category = discord.utils.get(ctx.guild.categories, name=category)
            await category.edit(name=name, overwrites=overwrites, reason="Edit Ticket Category")
            transcriptChannel = discord.utils.get(category.channels, name="transcripts")
            await transcriptChannel.edit(name="transcripts", reason="Edit Ticket Category", overwrites=overwrites)

            view = discord.ui.View.from_message(panel_message)
            button = view.get_item(custom_id=f"ticket_category|{category.id}")
            button.label = name
            button.emoji = emoji
            button.style = style

            ticket_data["category_roles"][category.id] = role.id
            await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS", "ticket_data", ticket_data)

            await panel_message.edit(view=view)

            embed = await db.build_embed(ctx.guild, title=f"{success_emoji} Ticket Category Updated", description=f"The **{category.name}** category has been updated with your changes.")
            await ctx.edit(embed=embed)

        except discord.HTTPException as e:
            if e.code == 50035:
                await ctx.respond(embed=await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The emoji you provided was invalid."), ephemeral=True)
            else:
                await ctx.respond(embed=await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Unknown HTTP error occured."), ephemeral=True)

        except Exception as e:
            print("[edit_tcategory]: ", e)
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Something went wrong, please try again later.")
            await ctx.edit(embed=embed)


    @tpanelCategory.command(name="remove", description="Remove a ticket category.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def remove_tcategory(self, ctx: discord.ApplicationContext, category: Option(str, "The ticket category to remove.", autocomplete=basic_autocomplete(get_category_channels))):

        try:
            existing_data = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")
            
            embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Removing Category", description=f"Removing the **{category}** category from your ticket panel...")
            await ctx.respond(embed=embed)

            if existing_data:
                existing_data = json.loads(existing_data)
                ticket_data = existing_data.get("ticket_data")

            panel_channel_id = ticket_data["ticket_panel"]["Channel ID"]
            panel_message_id = ticket_data["ticket_panel"]["Message ID"]

            panel_channel = ctx.guild.get_channel(panel_channel_id)
            panel_message = None

            if panel_message_id:
                try:
                    panel_message = await panel_channel.fetch_message(panel_message_id)
                except discord.NotFound:
                    panel_message = None

            if not panel_channel or not panel_message:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Ticket panel channel or message not found. Make sure to set up the ticket panel first.")
                await ctx.edit(embed=embed)
                return
            
            if "category_roles" in ticket_data:
                category_roles = ticket_data["category_roles"]
                category_ids = [int(category_id) for category_id in category_roles.keys()]
                category_info = [f"{category.name}" for category in ctx.interaction.guild.categories if category.id in category_ids]

                if category not in category_info:
                    embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"There is no ticket category with the name **{category}**.")
                    await ctx.edit(embed=embed)
                    return 

            category = discord.utils.get(ctx.guild.categories, name=category)
            view = discord.ui.View.from_message(panel_message)
            button = view.get_item(custom_id=f"ticket_category|{category.id}")
            view.remove_item(button)

            del ticket_data["category_roles"][str(category.id)]
            await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS", "ticket_data", ticket_data)

            for channel in category.channels:
                await channel.delete()

            await category.delete()
            await panel_message.edit(view=view)

            embed = await db.build_embed(ctx.guild, title=f"{success_emoji} Ticket Category Removed", description=f"The **{category.name}** category has been removed from the ticket panel.")
            await ctx.edit(embed=embed)

        except Exception as e:
            print("[remove_tcategory]: ", e)
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Something went wrong, please try again later.")
            await ctx.edit(embed=embed, ephemeral=True)


    @ticketSubCommands.command(name="find", description="Find a ticket by a member.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def find_ticket(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to find the ticket for.")):

        try:
            existing_data = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")
            embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Finding Ticket", description=f"Finding a ticket for {member.mention}...")
            await ctx.respond(embed=embed)

            if existing_data:
                existing_data = json.loads(existing_data)
                ticket_data = existing_data.get("ticket_data")

            open_tickets = ticket_data["open_tickets"]

            if str(member.id) in open_tickets:
                channel_id = open_tickets[str(member.id)]
                channel = ctx.guild.get_channel(channel_id)

                embed = await db.build_embed(ctx.guild, title=f"{success_emoji} Ticket Found", description=f"A ticket has been found for {member.mention} ➭ {channel.mention}")
                await ctx.edit(embed=embed)

            else:
                embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Ticket Not Found", description=f"I could not find an open ticket for {member.mention}.")
                await ctx.edit(embed=embed)

        except Exception as e:
            print("[find_ticket]: ", e)
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Something went wrong, please try again later.", ephemeral=True)
            await ctx.edit(embed=embed)


def setup(client):
    client.add_cog(tickets(client))