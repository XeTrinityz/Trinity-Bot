# Discord Imports
from discord.ext import commands, tasks
import discord

# Standard / Third-Party Library Imports
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import chat_exporter
import aiohttp
import asyncio
import random
import openai
import json
import time
import pytz
import re
import io

# Local Module Imports
from utils.views import verificationButton, verificationCaptcha, TOD, AutoMod, cancel_ticket_timer
from utils.tickethelper import ticketReason, TicketSettings
from utils.suggestionhelper import SuggestionButtons
from utils.database import Database
from utils.functions import Utils
from utils.lists import *
from Bot import config
import utils.logger

openai.api_key = ""
logging = utils.logger.logging.getLogger("bot")
db = Database()
message_counts = {}
ready = False

class listener(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.webhook_updated = False
        self.mod_rule = False
        self.last_execution_time = {}
        self.join_time = {}
        self.join_times = defaultdict(list)
        self.anti_spam = commands.CooldownMapping.from_cooldown(5, 15, commands.BucketType.user)
        self.too_many_violations = commands.CooldownMapping.from_cooldown(4, 60, commands.BucketType.user)
        self.chatbot_cooldown = commands.CooldownMapping.from_cooldown(1, 10, commands.BucketType.user)

    async def initialize_views(self):
        views = [verificationButton(), verificationCaptcha(), SuggestionButtons(), AutoMod(self.client), cancel_ticket_timer(), TOD()]
        for view in views:
            self.client.add_view(view)

    async def cache_guild_data(self, guild):
        await db.initialize_tables_and_settings(guild.id)
        bot_servers.append(f"{guild.name} ({guild.id})")
        counters = await db.get_value_from_table(guild.id, "ServerConfigurations", "Setting", "Feature", "COUNTERS")
        if counters:
            counters = json.loads(counters)
            for counter_name, counter_value in counters.items():
                getattr(self, f"{counter_name}_counters", {})[guild.id] = counter_value

        afk_data = await db.get_value_from_table(guild.id, "ServerConfigurations", "Setting", "Feature", "AFK")
        if afk_data:
            afk_data = json.loads(afk_data)
            for user_id, data in afk_data.items():
                afk[int(user_id)] = data

        try:
            invites = await guild.invites()
            for invite in invites:
                invite_cache[invite.code] = invite.uses
        except:
            pass

    async def cache_global_settings(self):
        block_data = await db.get_single_value_from_table("global_settings", "ARG1", "FEATURE", "BLOCKED")
        data_dict = json.loads(block_data)
        blacklist.extend(data_dict["users"])
        blacklist_guilds.extend(data_dict["guilds"])

        appearance, activity, status = await asyncio.gather(
            db.get_single_value_from_table("global_settings", "ARG1", "Feature", "STATUS"),
            db.get_single_value_from_table("global_settings", "ARG2", "Feature", "STATUS"),
            db.get_single_value_from_table("global_settings", "ARG3", "Feature", "STATUS")
        )

        status_map = {
            "Online": discord.Status.online,
            "Idle": discord.Status.idle,
            "Do Not Disturb": discord.Status.dnd,
            "Invisible": discord.Status.invisible,
            "Offline": discord.Status.offline,
        }

        activity_type_map = {
            "Playing": discord.ActivityType.playing,
            "Watching": discord.ActivityType.watching,
            "Listening": discord.ActivityType.listening,
            "None": None
        }

        activity_type = activity_type_map.get(activity)
        if activity_type:
            await self.client.change_presence(activity=discord.Activity(type=activity_type, name=status), status=status_map[appearance])
        else:
            await self.client.change_presence(activity=discord.CustomActivity(name=status), status=status_map[appearance])

    @commands.Cog.listener("on_connect")
    async def on_connect(self):
        await db.initialize_db_pool()
        await self.initialize_views()
        
        for guild in self.client.guilds:
            await self.cache_guild_data(guild)

        await self.cache_global_settings()


    @commands.Cog.listener("on_shard_connect")
    async def on_shard_connect(self, shard_id):
        logging.info(f"Shard #{shard_id} Connected")


    # ON READY
    # -------
    @commands.Cog.listener("on_ready")
    async def on_ready(self):
        ascii_art = """
████████╗██████╗░██╗███╗░░██╗██╗████████╗██╗░░░██╗
╚══██╔══╝██╔══██╗██║████╗░██║██║╚══██╔══╝╚██╗░██╔╝
░░░██║░░░██████╔╝██║██╔██╗██║██║░░░██║░░░░╚████╔╝░
░░░██║░░░██╔══██╗██║██║╚████║██║░░░██║░░░░░╚██╔╝░░
░░░██║░░░██║░░██║██║██║░╚███║██║░░░██║░░░░░░██║░░░
░░░╚═╝░░░╚═╝░░╚═╝╚═╝╚═╝░░╚══╝╚═╝░░░╚═╝░░░░░░╚═╝░░░
"""
        print(ascii_art + f"Username: {self.client.user.name} | ID: {self.client.user.id}\n")

        tasks_to_check = [self.check_reminders, self.check_timed_close_tickets, self.check_active_giveaways]
        for task in tasks_to_check:
            if not task.is_running():
                task.start()
   
    
    @tasks.loop(seconds=5)
    async def check_timed_close_tickets(self):
        current_time = datetime.utcnow()

        for channel_id, timers in list(timed_close_tickets.items()):
            for close_time, ticket_creator_id, message_id in list(timers):
                if current_time > close_time:
                    channel = self.client.get_channel(int(channel_id))
                    if not channel:
                        continue

                    ticket_data = await db.get_ticket_data(channel.guild.id)
                    if not ticket_data:
                        continue

                    embed = await db.build_embed(channel.guild, title="<a:Loading:1247220769511964673> Deleting Ticket", description="This ticket is being deleted...")
                    await channel.send(embed=embed)

                    if channel.id in ticket_data["open_tickets"].values():
                        transcript_file, formatted_duration = await self.prepare_ticket_transcript(channel)
                        await self.send_transcript_to_channel(transcript_file, channel, formatted_duration, ticket_creator_id)
                        await self.cleanup_ticket_data(channel, ticket_data)

                    await channel.delete()
                    await db.update_guild_leaderboard_stat(channel.guild, "tickets_resolved", 1)

    async def prepare_ticket_transcript(self, channel):
        transcript = await chat_exporter.export(channel, tz_info='UTC')
        transcript_file = discord.File(io.BytesIO(transcript.encode()), filename=f"{channel.name}.html")

        created_datetime = channel.created_at
        deleted_datetime = datetime.now(pytz.utc)
        duration = deleted_datetime - created_datetime
        formatted_duration = self.format_duration(duration)

        return transcript_file, formatted_duration

    async def send_transcript_to_channel(self, transcript_file, channel, formatted_duration, ticket_creator_id):
        fileChannel = self.client.get_channel(1153895371181928508)
        message = await fileChannel.send(file=transcript_file)
        attachment = message.attachments[0]

        transcriptChannel = discord.utils.get(channel.category.channels, name="transcripts")
        view = self.build_transcript_view(attachment.url)
        user = await self.client.get_or_fetch_user(int(ticket_creator_id))

        embed = await db.build_embed(channel.guild, title="📋 Ticket Transcript")
        embed.add_field(name="Server", value=channel.guild.name, inline=True)
        embed.add_field(name="Category", value=channel.category.name, inline=True)
        embed.add_field(name="Ticket", value=channel.name, inline=True)
        embed.add_field(name="Closer", value=f"Trinity\n`({self.client.user.id})`", inline=True)
        embed.add_field(name="Creator", value=f"{user.display_name}\n`({user.id})`", inline=True)
        embed.add_field(name="Duration", value=formatted_duration, inline=True)
        await transcriptChannel.send(embed=embed, view=view)

        try:
            await user.send(embed=embed, view=view)
        except:
            pass

    async def cleanup_ticket_data(self, channel, ticket_data):
        ticket_data["open_tickets"] = {user_id: ch_id for user_id, ch_id in ticket_data["open_tickets"].items() if ch_id != channel.id}
        await db.update_value_in_table(channel.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS", "ticket_data", ticket_data)

    def format_duration(self, duration):
        days, remainder = divmod(duration.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        if days > 0:
            return f"{int(days)} Days, {int(hours)} Hours"
        elif hours > 0:
            return f"{int(hours)} Hours, {int(minutes)} Minutes"
        elif minutes > 0:
            return f"{int(minutes)} Minutes, {int(seconds)} Seconds"
        else:
            return f"{int(seconds)} Seconds"

    def build_transcript_view(self, url):
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="View Transcript", url=url, emoji="📋", style=discord.ButtonStyle.link))
        view.add_item(discord.ui.Button(label="Download Transcript", url=f"{url}&download", emoji="⬇", style=discord.ButtonStyle.link))
        return view


    @tasks.loop(seconds=5)
    async def check_raided(self):
        now = datetime.now().timestamp()
        to_remove = [guild_id for guild_id, raided_servers in self.raided.items() for end_time_list in raided_servers if any(now >= end_time for end_time in end_time_list)]
        for guild_id in to_remove:
            del self.raided[guild_id]


    @tasks.loop(seconds=5)
    async def check_reminders(self):
        now = datetime.now().timestamp()
        expired_reminders = []
        for user_id, user_reminders in reminders.items():
            for reminder_data in user_reminders:
                reminder, reminder_time, channel, time_started = reminder_data
                if now >= reminder_time:
                    user = self.client.get_user(user_id)
                    if user:
                        embed = await db.build_embed(channel.guild, title="⏰ Reminder", description=f"You asked me to remind you about this <t:{time_started}:R>:\n\n**{reminder}**")
                        await channel.send(content=user.mention, embed=embed)
                    expired_reminders.append((user_id, reminder_data))
        
        for user_id, reminder_data in expired_reminders:
            reminders[user_id].remove(reminder_data)
            if not reminders[user_id]:
                del reminders[user_id]


    @tasks.loop(seconds=10)
    async def check_active_giveaways(self):
        current_time = time.time()

        for guild in self.client.guilds:
            try:
                guild_id = guild.id
                existing_data = await db.get_value_from_table(guild_id, "ServerConfigurations", "Setting", "Feature", "GIVEAWAYS")

                if existing_data:
                    existing_data = json.loads(existing_data)
                    active_giveaways = existing_data.get("active_giveaways", {})
                    completed_giveaways = existing_data.get("completed_giveaways", {})
                    keys_to_remove = []
                    update_required = False

                    for key, giveaway_data in active_giveaways.items():
                        channel_id, _ = key.split('-')
                        channel = guild.get_channel(int(channel_id))

                        if channel is None or current_time < giveaway_data.get("end_time"):
                            continue  # Skip to the next iteration if channel is None or giveaway hasn't ended yet

                        message_id = giveaway_data.get("message")
                        try:
                            message = await channel.fetch_message(message_id)
                        except discord.errors.NotFound:
                            keys_to_remove.append(key)
                            continue

                        prize = giveaway_data.get("prize")
                        hosted_by = f"<@{giveaway_data.get('hosted_by')}>"
                        formatted_end_time = f"<t:{int(giveaway_data.get('end_time'))}:R>"
                        winners_count = giveaway_data.get("winners")

                        reactions = message.reactions
                        if reactions:
                            users = await reactions[0].users().flatten()
                            eligible_users = [user for user in users if not user.bot]

                            if len(eligible_users) >= winners_count:
                                selected_winners = random.sample(eligible_users, winners_count)
                                winner_mentions = ", ".join([winner.mention for winner in selected_winners])
                                winners_text = f"Congratulations to {winner_mentions} for winning **{prize}**!"
                            else:
                                winners_text = "There were not enough participants for the giveaway."
                                winner_mentions = "None"

                            await message.reply(f"# 🎉 Giveaway Ended 🎉\n{winners_text}")
                        else:
                            winner_mentions = "None"
                            await message.reply(f"There were not enough participants for the giveaway.")

                        embed = await db.build_embed(guild, title="🎉 Giveaway Ended 🎉", description=f"**Prize** ➭ {prize}\n**Winners** ➭ {winner_mentions}\n**Hosted By** ➭ {hosted_by}\n**Ended** ➭ {formatted_end_time}")
                        await message.edit(embed=embed)

                        completed_giveaways[key] = {"message": message_id, "prize": prize}
                        keys_to_remove.append(key)
                        update_required = True
                    
                    if update_required: 
                        for key in keys_to_remove:
                            active_giveaways.pop(key, None)

                        existing_data["active_giveaways"] = active_giveaways
                        existing_data["completed_giveaways"] = completed_giveaways

                        await db.update_value_in_table(guild.id, "ServerConfigurations", "Setting", "Feature", "GIVEAWAYS", "active_giveaways", active_giveaways)
                        await db.update_value_in_table(guild.id, "ServerConfigurations", "Setting", "Feature", "GIVEAWAYS", "completed_giveaways", completed_giveaways)

            except Exception as e:
                print("[check_active_giveaways]: ", e)
                continue


    # ERROR HANDLING
    # --------------
    @commands.Cog.listener("on_error")
    async def on_error(self, ctx: discord.ApplicationContext, error):
        logging.error(f"Command Error: {error}\nInteraction Data: {ctx.interaction.data}")
        await self.respond_with_error(ctx, "An error has occurred and the developer was informed.")

    @commands.Cog.listener("on_application_command_error")
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error):
        error_mapping = {
            discord.ApplicationCommandInvokeError: lambda e: getattr(e, 'original', e),
            discord.errors.NotFound: lambda e: e,
            discord.errors.HTTPException: lambda e: e,
            commands.CommandNotFound: lambda e: e,
            commands.PrivateMessageOnly: lambda e: e,
            commands.NoPrivateMessage: lambda e: e,
            commands.MissingPermissions: lambda e: e,
            discord.Forbidden: lambda e: e,
            commands.BotMissingPermissions: lambda e: e,
            commands.MissingRole: lambda e: e,
            commands.BadArgument: lambda e: e,
            commands.NotOwner: lambda e: "This command can only be used by the bot owner.",
            commands.DisabledCommand: lambda e: e,
            commands.CheckFailure: lambda e: e,
            commands.CommandOnCooldown: self.format_cooldown_message,
        }

        error_type = type(error)
        if error_type in error_mapping:
            message = error_mapping[error_type](error)
            await self.respond_with_error(ctx, message)
        else:
            logging.error(f"Unhandled Command Error: {error}\nInteraction Data: {ctx.interaction.data}")

    async def respond_with_error(self, ctx: discord.ApplicationContext, message):
        try:
            embed = discord.Embed(title="", color=discord.Color.red())
            embed.add_field(name=f"{error_emoji} Command Error", value=message, inline=False)
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            logging.error(f"Error sending error response: {e}")

    def format_cooldown_message(self, error):
        total_seconds = round(error.retry_after)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"Command on cooldown for **{hours}** hours, **{minutes}** minutes, and **{seconds}** seconds."
        elif minutes:
            return f"Command on cooldown for **{minutes}** minutes and **{seconds}** seconds."
        else:
            return f"Command on cooldown for **{seconds}** seconds."


    @commands.Cog.listener("on_interaction")
    async def on_interaction(self, interaction: discord.Interaction):

        if interaction.guild:
            try:
                default_role = interaction.guild.default_role

                if not default_role.permissions.external_emojis:
                    permissions = default_role.permissions
                    permissions.update(external_emojis=True)
                    await default_role.edit(permissions=permissions)
            except:
                print(f"{interaction.guild} - Failed to set external emoji permission.")

        if not isinstance(interaction, discord.Interaction) or interaction.type is not discord.InteractionType.component:
            return

        # Dropdown Menus
        if interaction.custom_id == "self_menu":
            user_id = interaction.user.id
            # Check if the user is on cooldown for this interaction ID
            if user_id in interaction_cooldowns and datetime.utcnow() - interaction_cooldowns[user_id] < timedelta(seconds=30):
                remaining_time = (interaction_cooldowns[user_id] + timedelta(seconds=30) - datetime.utcnow()).seconds
                embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description=f"You are on cooldown. Please try again in **{remaining_time}** seconds.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                await interaction.message.edit(view=discord.ui.View.from_message(interaction.message))
                return

            await interaction.response.defer(ephemeral=True, invisible=False)
            removed_roles = []
            added_roles = []

            for value in interaction.data["values"]:
                action_message = ""
                _, role_id = value.split("|")
                target_role = interaction.guild.get_role(int(role_id))

                if target_role:
                    if target_role in interaction.user.roles:
                        await interaction.user.remove_roles(target_role)
                        removed_roles.append(target_role.mention)
                    else:
                        await interaction.user.add_roles(target_role)
                        added_roles.append(target_role.mention)
                else:
                    embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description="This self-role menu needs to be re-configured.")
                    return await interaction.response.send_message(embed=embed, ephemeral=True)

            added_roles_str = "\n".join(added_roles)
            removed_roles_str = "\n".join(removed_roles)

            if added_roles and not removed_roles:
                title = f"{success_emoji} {'Role' if len(added_roles) == 1 else 'Roles'} Added"
                description = f"You received the following {'role' if len(added_roles) == 1 else 'roles'}:\n\n{added_roles_str}"
            elif not added_roles and removed_roles:
                title = f"{success_emoji} {'Role' if len(removed_roles) == 1 else 'Roles'} Removed"
                description = f"You removed the following {'role' if len(removed_roles) == 1 else 'roles'}:\n\n{removed_roles_str}"
            elif added_roles and removed_roles:
                title = f"{success_emoji} Roles Added & Removed"
                description = f"You received the following {'role' if len(added_roles) == 1 else 'roles'}:\n\n{added_roles_str}\n\nYou removed the following {'role' if len(removed_roles) == 1 else 'roles'}:\n\n{removed_roles_str}"

            embed = await db.build_embed(interaction.guild, title=title, description=description)
            await interaction.followup.send(embed=embed, ephemeral=True)
            await interaction.message.edit(view=discord.ui.View.from_message(interaction.message))
            interaction_cooldowns[user_id] = datetime.utcnow()
            return

        # Ticket Category Buttons
        if interaction.custom_id.startswith("ticket_category"):
            category_id = interaction.custom_id.split("|")[1]
            category = interaction.guild.get_channel(int(category_id))

            if not category:
                return await interaction.response.send_message("Category not found.", ephemeral=True)
            
            ticket_data = await db.get_value_from_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

            if ticket_data:
                ticket_data = json.loads(ticket_data)
                ticket_data = ticket_data.get("ticket_data")
            
            open_tickets = ticket_data["open_tickets"]

            if str(interaction.user.id) in open_tickets:
                channel_id = open_tickets[str(interaction.user.id)]
                channel = interaction.guild.get_channel(int(channel_id))
                if channel:
                    return await interaction.response.send_message(f"# {error_emoji} Failed\n\nYou already have an open ticket ➭ <#{channel.id}>.", ephemeral=True)
                else:
                    # Remove invalid open ticket entry if the channel does not exist
                    open_tickets.pop(str(interaction.user.id))
                    # Update the database with the corrected open_tickets data
                    ticket_data["open_tickets"] = open_tickets
                    await db.update_value_in_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS", "ticket_data", ticket_data)
            
            await interaction.response.send_modal(ticketReason(category))
            return

        # Ticket Buttons
        if interaction.custom_id.startswith("ticket_"):
            ticket_button_handlers = {
                "ticket_delete": TicketSettings.delete_button_callback,
                "ticket_close": TicketSettings.close_button_callback,
                "ticket_open": TicketSettings.open_button_callback,
                "ticket_claim": TicketSettings.claim_button_callback,
                "ticket_unclaim": TicketSettings.unclaim_button_callback,
            }

            handler = ticket_button_handlers.get(interaction.custom_id)
            if handler:
                view = discord.ui.View.from_message(interaction.message)
                if interaction.custom_id in ["ticket_close", "ticket_open"]:
                    button = view.children[1] 
                elif interaction.custom_id == "ticket_delete":
                    button = view.children[2]
                else: 
                    button = view.children[0]

                if interaction.custom_id != "ticket_delete":
                    await handler(self, button, interaction)
                else:
                    await handler(self, interaction)
            return

        # Role Buttons
        if "role" in interaction.custom_id:
            _, role_id = interaction.custom_id.split("|")
            target_role = interaction.guild.get_role(int(role_id))

            if target_role:
                if target_role in interaction.user.roles:
                    await interaction.user.remove_roles(target_role)
                    action_message = f"You removed the {target_role.mention} role."
                else:
                    await interaction.user.add_roles(target_role)
                    action_message = f"You received the {target_role.mention} role."

                await interaction.response.send_message(action_message, ephemeral=True)
            else:
                await interaction.response.send_message("Role not found.", ephemeral=True)
            return

        # Bot Logs
        if not interaction.user.id == 1206945231719899167:
            bot_logs = self.client.get_channel(1247266830129696921)
            embed = await db.build_embed(interaction.guild, title="<a:Folder:1247220756547502160> Interaction Logged", description=f"**User** ➭ {interaction.user.mention}\n**Custom ID** ➭ {interaction.custom_id}\n**Server** ➭ {interaction.guild.name}\n**Channel** ➭ {interaction.channel.name}")
            await bot_logs.send(embed=embed)


    # ON JOIN EVENTS
    # --------------
    @commands.Cog.listener("on_guild_join")
    async def on_guild_join(self, guild: discord.Guild):

        if guild.id in blacklist_guilds:
            bot_logs = self.client.get_channel(1247266830129696921)
            embed = discord.Embed(title="", color=discord.Colour.red())
            embed.add_field(name="<a:Banned:1247220734233804831> Blocked Guild", value=f"**Guild** ➭ {guild.name}\n**ID** ➭ {guild.id}\n**Owner** ➭ {guild.owner.mention}\n**Members** ➭ {guild.member_count}", inline=False)
            await bot_logs.send(embed=embed)
            return await guild.leave()

        bot_servers.append(f"{guild.name} ({guild.id})")
        await db.initialize_tables_and_settings(guild.id)

        try:
            invites = await guild.invites()

            for invite in invites:
                invite_code = invite.code
                uses = invite.uses
                invite_cache[invite_code] = uses
        except:
            pass
        
        bot_logs = self.client.get_channel(1247266830129696921)
        embed = await db.build_embed(guild, title="")
        embed.add_field(name="<a:Information:1247223152367636541> Guild Joined", value=f"**Guild** ➭ {guild.name}\n**ID** ➭ {guild.id}\n**Owner** ➭ {guild.owner.mention}\n**Members** ➭ {guild.member_count}", inline=False)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else "")
        await bot_logs.send(embed=embed)


    # ON REMOVE EVENTS
    # ----------------
    @commands.Cog.listener("on_guild_remove")
    async def on_guild_remove(self, guild: discord.Guild):

        try:
            bot_servers.remove(f"{guild.name} ({guild.id})")

            bot_logs = self.client.get_channel(1247266830129696921)
            embed = discord.Embed(title="", color=discord.Colour.red())
            embed.add_field(name="<a:Information:1247223152367636541> Guild Removed", value=f"**Guild** ➭ {guild.name}\n**ID** ➭ {guild.id}\n**Owner** ➭ {guild.owner.mention}\n**Members** ➭ {guild.member_count}", inline=False)
            embed.set_thumbnail(url=guild.icon.url if guild.icon else "")
            await bot_logs.send(embed=embed)
        except:
            pass


    # ON COMMAND COMPLETION EVENTS
    # ----------------------------
    @commands.Cog.listener("on_application_command_completion")
    async def on_application_command_completion(self, context: discord.ApplicationContext):

        # Bot Logs
        if not context.author.id == 1206945231719899167:

            bot_logs = self.client.get_channel(1247266830129696921)
            embed = await db.build_embed(context.author.guild, title="<a:Folder:1247220756547502160> Command Logged")

            desc = f"**User** ➭ {context.author.mention}\n**Command** ➭ {context.command}\n**Server** ➭ {context.guild.name}\n**Channel** ➭ {context.channel.name}\n"
            if "options" in context.interaction.data:
                args = ""
                for options in context.interaction.data["options"]:
                    args += f"{options['name'].capitalize()} ➭ {options['value']}\n"
                desc += f"\n<a:Information:1247223152367636541> **Arguments**```{args}```"
            embed.description = desc
            await bot_logs.send(embed=embed)


    # ON MESSAGE EVENTS
    # -----------------
    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        
        if message.channel.id in timed_close_tickets:
            timers_for_channel = timed_close_tickets[message.channel.id]

            if timers_for_channel:  # Check if the list is not empty
                close_time, ticket_creator_id, original_message = timers_for_channel[0]
                original_message = await message.channel.fetch_message(original_message)

                if message.author.id == int(ticket_creator_id):
                    # Remove the timer for the channel
                    del timed_close_tickets[message.channel.id]
                    await original_message.delete()

                    embed = await db.build_embed(message.guild, title="🕒 Ticket Closure Cancelled", description=f"The scheduled closure of this ticket has been cancelled for {message.author.mention}.")
                    await message.channel.send(embed=embed)
           
                    
        # Message Count
        await db.update_leaderboard_stat(message.author, "messages", 1)


        # Ticket Message Count
        ticket_data = await db.get_value_from_table(message.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")
        if ticket_data:
            ticket_data = json.loads(ticket_data)
            ticket_data = ticket_data.get("ticket_data")
            ticket_category = ticket_data.get("category_roles")
            category_list = list(ticket_category.keys())

            if message.channel.category and str(message.channel.category_id) in category_list:
                ticket_role = ticket_category.get(str(message.channel.category_id))
                ticket_role = message.guild.get_role(int(ticket_role))
                if ticket_role in message.author.roles:
                    await db.update_leaderboard_stat(message.author, "ticket_messages", 1)


        # XP System
        toggles = await db.get_value_from_table(message.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES")
        if toggles:
            toggles = json.loads(toggles)
            xp_system_state = toggles.get("xp_system")
            suggestions_state = toggles.get("suggestions")
            chatbot_state = toggles.get("chatbot")
            link_embedding_state = toggles.get("message_link_embed")

        if xp_system_state:
            xp = random.randint(1, 35)
            await db.update_leaderboard_stat(message.author, "xp", xp)
            await db.check_level_up(message, message.author)


        # Protections
        protections, channels = await asyncio.gather(
            db.get_value_from_table(message.guild.id, "ServerConfigurations", "Setting", "Feature", "PROTECTIONS"),
            db.get_value_from_table(message.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")
        )
        if protections and channels:
            message_deleted = False
            protections = json.loads(protections)
            channels = json.loads(channels)
            moderation_log_channel = channels.get("moderation_log_channel")
            anti_spam_state = protections.get("anti_spam")

            if anti_spam_state and not message.author.guild_permissions.manage_messages:
                user_id = str(message.author.id)
                message_counts[user_id] = message_counts.get(user_id, 0) + 1
                bucket = self.anti_spam.get_bucket(message)
                reply_after = bucket.update_rate_limit()

                if reply_after:
                    violations = self.too_many_violations.get_bucket(message)
                    if violations.update_rate_limit():
                        mute_duration = timedelta(minutes=5)
                        await message.author.timeout_for(mute_duration, reason="Anti-Spam Protection")
                        timeout_message = await db.build_embed(message.guild, title="<a:Alert:1153886506566561822> Server Notice", description=f"You were muted in **{message.guild.name}** for **5 Minutes**.")
                        timeout_message.add_field(name="Reason", value="Spamming.", inline=False)
                        timeout_message.timestamp = datetime.now(timezone.utc)
                        
                        def userCheck(m):
                            return m.author.id == message.author.id

                        await message.channel.purge(limit=10, check=userCheck)
                        message_deleted = True

                        try:
                            await message.author.send(embed=timeout_message)
                        except discord.Forbidden:
                            pass

                        if moderation_log_channel:
                            channel = self.client.get_channel(moderation_log_channel)
                            if channel:
                                embed = await db.build_embed(message.guild, title="<a:Moderation:1247220777627942974> Spam Detected", description=f"{message.author.mention} `({message.author.id})` was spamming in {message.channel.mention} and was muted for 5 minutes.")
                                await channel.send(embed=embed)
                            else:
                                await db.update_value_in_table(message.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "moderation_log_channel", None)


        # Suggestions
        if suggestions_state and not message_deleted:
            suggestions = await db.get_value_from_table(message.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")
            if suggestions:
                suggestions = json.loads(suggestions)
                suggestion_channel = suggestions.get("suggestion_channel")

                if message.channel.id == suggestion_channel:
                    embed = await db.build_embed(message.guild, title="")
                    embed.set_author(name=message.author.name, icon_url=message.author.display_avatar.url)
                    embed.add_field(name="Suggestion", value=message.content, inline=False)
                    embed.add_field(name="Status", value="🕗 Pending Review...", inline=False)
                    
                    if message.attachments:
                        embed.set_image(url=message.attachments[0].url)

                    embed.set_thumbnail(url="https://i.ibb.co/s37fWg5/idea.png")
                    embed.set_footer(text=str(message.author.id))
                    await message.delete()
                    suggestion = await message.channel.send(embed=embed, view=SuggestionButtons())
                    data = {"upvotes": 0, "downvotes": 0, "upvoted_users": [], "downvoted_users": []}
                    await db.update_value_in_table(message.guild.id, "ServerConfigurations", "Setting", "Feature", "SUGGESTIONS", suggestion.id, data)
                    await suggestion.create_thread(name=f"{message.author.display_name}'s Suggestion")

      
        # AFK
        if not message_deleted:
            if message.author.id in afk:
                afk_data = json.loads(await db.get_value_from_table(message.guild.id, "ServerConfigurations", "Setting", "Feature", "AFK"))
                is_afk = afk_data.get(str(message.author.id))
                if is_afk:
                    afk.pop(message.author.id)
                    if message.author.nick and "[AFK]" in message.author.nick:
                        await message.author.edit(nick=message.author.nick.replace("[AFK] ", ""))
                    embed = await db.build_embed(message.guild, title="<a:Wave:1247223147044798484> AFK Status Updated", description=f"Welcome back {message.author.mention}!\nI have removed your AFK status.")
                    await message.reply(embed=embed, delete_after=10)
                    await db.remove_value_from_table(message.guild.id, "ServerConfigurations", "Setting", "Feature", "AFK", str(message.author.id))

            mentioned_users = message.mentions or (message.reference.cached_message.mentions if message.reference and message.reference.cached_message else [])
            for mentioned_user in mentioned_users:
                if mentioned_user.id in afk:
                    afk_info = afk[mentioned_user.id]
                    reason, timestamp = afk_info
                    embed = await db.build_embed(message.guild, title="<a:Information:1247223152367636541> AFK", description=f"{mentioned_user.mention} is currently AFK.")
                    embed.add_field(name="Reason", value=reason, inline=True)
                    embed.add_field(name="Last Seen", value=f"<t:{round(timestamp)}:R>", inline=True)
                    await message.reply(embed=embed, delete_after=15)


        # Auto-Responses
        if not message_deleted:
            triggers = await db.get_value_from_table(message.guild.id, "ServerConfigurations", "Setting", "Feature", "TRIGGERS")
            if triggers:
                content = message.content.lower()
                triggers = json.loads(triggers)
                for trigger, data in triggers.items():
                    pattern = rf'\b{re.escape(trigger.lower())}\b'
                    if re.search(pattern, content):
                        response_type = data["type"]

                        if response_type == "Embed":
                            embed = discord.Embed.from_dict(data["response"])
                            return await message.reply(embed=embed)
                        
                        response = data["response"]
                        if response_type == "Text":
                            await message.reply(response)
                        elif response_type == "Reaction":
                            try:
                                await message.add_reaction(response)
                            except:
                                await db.remove_value_from_table(message.guild.id, "ServerConfigurations", "Setting", "Feature", "TRIGGERS", trigger)
                                await message.reply(f"The '{trigger}' reaction trigger was removed due to the provided emoji being invalid.", delete_after=10)
                        break


        # Sticky Messages
        if not message_deleted:
            sticky_messages = await db.get_value_from_table(message.guild.id, "ServerConfigurations", "Setting", "Feature", "STICKY")
            if sticky_messages:
                sticky_messages = json.loads(sticky_messages)
                sticky_message_info = sticky_messages.get(str(message.channel.id))

                if sticky_message_info:
                    sticky_channel_id = sticky_message_info.get("Channel ID")
                    sticky_message_id = sticky_message_info.get("Message ID")

                    sticky_channel = self.client.get_channel(sticky_channel_id)
                    if sticky_channel:
                        try:
                            sticky_message = await sticky_channel.fetch_message(sticky_message_id)
                            await sticky_message.delete()
                            new_message = await sticky_channel.send(embed=sticky_message.embeds[0] if sticky_message.embeds else None)
                            data = {"Channel ID": message.channel.id, "Message ID": new_message.id}
                            await db.update_value_in_table(message.guild.id, "ServerConfigurations", "Setting", "Feature", "STICKY", str(message.channel.id), data)
                        except discord.NotFound:
                            await db.delete_sticky_entry(message.guild.id, str(message.channel.id), sticky_message_id)
                
            
        # Message URL Fetcher
        if link_embedding_state and not message_deleted:
            pattern = r"https://(?:canary\.|ptb\.|)discord(?:app)?\.com/channels/(\d+)/(\d+)/(\d+)"
            match = re.search(pattern, message.content)
            
            if match:
                guild_id, channel_id, message_id = match.groups()

                try:
                    guild = self.client.get_guild(int(guild_id))
                    if guild:
                        channel = guild.get_channel(int(channel_id))
                        if channel:
                            fetched = await channel.fetch_message(int(message_id))

                            if fetched.content or fetched.attachments:
                                view = discord.ui.View()
                                view.add_item(discord.ui.Button(label="Jump to Message", url=fetched.jump_url, style=discord.ButtonStyle.link))
                                embed = discord.Embed(description=fetched.content)
                                embed.set_author(name=fetched.author.display_name, url=fetched.jump_url, icon_url=fetched.author.display_avatar.url)
                                embed.set_footer(text=fetched.guild.name, icon_url=fetched.guild.icon.url if fetched.guild.icon else None)
                                
                                if fetched.attachments and fetched.attachments[0].content_type in ["image/png", "image/jpg", "image/jpeg", "image/gif"]:
                                    embed.set_image(url=fetched.attachments[0].url)
                                
                                embed.timestamp = fetched.created_at
                                await message.reply(embed=embed, view=view, mention_author=False, allowed_mentions=discord.AllowedMentions(users=False))
                            elif fetched.embeds:
                                embed = fetched.embeds[0]
                                view = discord.ui.View()
                                view.add_item(discord.ui.Button(label="Jump to Message", url=fetched.jump_url, style=discord.ButtonStyle.link))
                                await message.reply(content=f"**[{fetched.guild.name}]** {fetched.author.mention} - <t:{round(fetched.created_at.timestamp())}:R>", embed=embed, view=view, mention_author=False, allowed_mentions=discord.AllowedMentions(users=False))
                except:
                    pass


        # Chatbot
        if chatbot_state and not message_deleted:
            chatbot = await db.get_value_from_table(message.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")
            if chatbot:
                chatbot = json.loads(chatbot)
                chatbot_channel = chatbot.get("chatbot_channel")

                if message.channel.id == chatbot_channel and not message.reference:
                    bucket = self.chatbot_cooldown.get_bucket(message)
                    retry_after = bucket.update_rate_limit()

                    if retry_after:
                        embed = discord.Embed(title=f"{error_emoji} Request Failed", description=f"You are on cooldown. Try again in {round(retry_after)} seconds.")
                        await message.reply(embed=embed, delete_after=5)
                        await message.delete()
                        return
                    
                    if message.channel.slowmode_delay < 10:
                        try:
                            await message.channel.edit(slowmode_delay=10)
                        except Exception as e:
                            logging.error(f"Failed to set slowmode: {e}")
                            await message.reply("The chatbot channel must have a slowmode delay of at least 30 seconds.")
                            return

                    async with message.channel.typing():
                        try:
                            async with aiohttp.ClientSession() as session:
                                async with session.post(
                                    'https://api.openai.com/v1/chat/completions',
                                    headers={
                                        'Authorization': f'Bearer {openai.api_key}',
                                        'Content-Type': 'application/json'
                                    },
                                    json={
                                        "model": "gpt-3.5-turbo",
                                        "messages": [
                                            {"role": "system", "content": "You are Trinity, a helpful, conversational Discord Bot assistant created by XeTrinityz."},
                                            {"role": "user", "content": message.content},
                                        ],
                                        "max_tokens": 300,
                                        "temperature": 0.2
                                    }
                                ) as resp:
                                    if resp.status != 200:
                                        return await message.reply("The chatbot API is down. Please try again later.")
                                    
                                    response = await resp.json()
                                    await message.reply(response['choices'][0]['message']['content'])
                                            
                        except Exception as e:
                            logging.error(f"[Chatbot Error]: {e}")
                            await message.reply("The chatbot is currently unavailable. Please try again later.")
                

    # ON MESSAGE EDIT
    # ---------------
    @commands.Cog.listener("on_message_edit")
    async def on_message_edit(self, before, after):
        if before.author.bot or not before.guild:
            return

        #protections = await db.get_value_from_table(after.guild.id, "ServerConfigurations", "Setting", "Feature", "PROTECTIONS")
        channels =  await db.get_value_from_table(after.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS") 
        toggles = await db.get_value_from_table(after.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES")

        if channels and toggles:
            channels = json.loads(channels)
            toggles = json.loads(toggles)
            audit_log_state = toggles.get("audit_logs")
            audit_log_channel = channels.get("audit_log_channel")
        
            if audit_log_state:
                logChannel = self.client.get_channel(audit_log_channel)
                if logChannel is None:
                    await db.update_value_in_table(before.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "audit_log_channel", None)
                    await db.update_value_in_table(before.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "audit_logs", False)
                    return
                
                view = discord.ui.View()
                jump_message = discord.ui.Button(label="Message", url=after.jump_url, style=discord.ButtonStyle.link)
                view.add_item(jump_message)
                
                embed = await db.build_embed(before.guild, title="<a:Information:1247223152367636541> Message Updated", description=f"{before.author.mention} edited a message in {before.channel.mention}.")
                embed.set_thumbnail(url="")
                embed.add_field(name="Before", value=f"{before.content[:1024]}", inline=True)
                embed.add_field(name="After", value=f"{after.content[:1024]}", inline=True)
                if before.attachments and before.attachments[0].content_type in ["image/png", "image/jpg", "image/jpeg", "image/gif"]:
                    embed.set_image(url=before.attachments[0].url)
                await logChannel.send(embed=embed, view=view)


    @commands.Cog.listener("on_raw_reaction_add")
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        async def create_starboard_embed(message):
            embed = await db.build_embed(message.guild, title="💬 Starboard Message", description=message.content if message.content else None)
            embed.set_author(name=f"{message.author.display_name} ({message.author.name})", icon_url=message.author.display_avatar.url)
            embed.set_footer(text=f"⭐ {target_reaction_count} | {message.author.id}")

            if message.attachments and "image" in message.attachments[0].content_type:
                embed.set_image(url=message.attachments[0].url)

            embed.set_thumbnail(url="")
            embed.timestamp = message.created_at
            return embed

        if payload.emoji.name == "⭐":
            channels = await db.get_value_from_table(payload.member.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")

            if channels:
                channels_ = json.loads(channels)
                starboard_channel = channels_.get("starboard_channel")

                if starboard_channel:
                    starboard_channel = self.client.get_channel(starboard_channel)

                    if starboard_channel is None:
                        await db.update_value_in_table(payload.guild_id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "starboard_channel", None)
                        return

                    message_id = payload.message_id
                    channel_id = payload.channel_id
                    message_channel = self.client.get_channel(channel_id)
                    message = await message_channel.fetch_message(message_id)

                    starboard = await db.get_value_from_table(payload.member.guild.id, "ServerConfigurations", "Setting", "Feature", "STARBOARD")
                    starboard = json.loads(starboard)
                    starboard_data = starboard.get(str(message_id))

                    if message.author.id == payload.user_id:
                        await message.remove_reaction(emoji="⭐", member=payload.member)
                        return

                    target_reaction = next((reaction for reaction in message.reactions if reaction.emoji == "⭐"), None)
                    target_reaction_count = target_reaction.count if target_reaction else 0

                    if message.content or (message.attachments and "image" in message.attachments[0].content_type):
                        await db.update_leaderboard_stat(message.author, "stars", 1)

                        if target_reaction_count == 2 and starboard_data is None:
                            embed = await create_starboard_embed(message)
                            view = discord.ui.View()
                            source = discord.ui.Button(emoji="⭐", url=message.jump_url, style=discord.ButtonStyle.link)
                            view.add_item(source)

                            starboarded = await starboard_channel.send(embed=embed, view=view)

                            data = {"channel": channel_id, "starboard_message": starboarded.id}
                            await db.update_value_in_table(payload.member.guild.id, "ServerConfigurations", "Setting", "Feature", "STARBOARD", message_id, data)

                        elif target_reaction_count >= 2:
                            try:
                                if starboard_data:
                                    starboard_message = await starboard_channel.fetch_message(starboard_data["starboard_message"])
                                else:
                                    raise discord.NotFound  # Force a NotFound exception to trigger the creation of a new starboard message
                            except discord.NotFound:
                                # Handle the case where the starboard message is not found
                                embed = await create_starboard_embed(message)
                                view = discord.ui.View()
                                source = discord.ui.Button(emoji="⭐", url=message.jump_url, style=discord.ButtonStyle.link)
                                view.add_item(source)

                                starboarded = await starboard_channel.send(embed=embed, view=view)

                                data = {"channel": channel_id, "starboard_message": starboarded.id}
                                await db.update_value_in_table(payload.member.guild.id, "ServerConfigurations", "Setting", "Feature", "STARBOARD", message_id, data)
                                return

                            starboard_embed = starboard_message.embeds[0].to_dict()
                            starboard_embed["footer"]["text"] = f"⭐ {target_reaction_count} | {message.author.id}"
                            embed = discord.Embed.from_dict(starboard_embed)
                            await starboard_message.edit(embed=embed)


    @commands.Cog.listener("on_raw_reaction_remove")
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        async def create_starboard_embed(message):
            embed = await db.build_embed(message.guild, title="💬 Starboard Message", description=message.content if message.content else None)
            embed.set_author(name=f"{message.author.display_name} ({message.author.name})", icon_url=message.author.display_avatar.url)
            embed.set_footer(text=f"⭐ {target_reaction_count} | {message.author.id}")

            if message.attachments and "image" in message.attachments[0].content_type:
                embed.set_image(url=message.attachments[0].url)

            embed.set_thumbnail(url="")
            embed.timestamp = message.created_at
            return embed

        if payload.emoji.name == "⭐":
            channels = await db.get_value_from_table(payload.guild_id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")

            if channels:
                channels_ = json.loads(channels)
                starboard_channel = channels_.get("starboard_channel")

                if starboard_channel:
                    starboard_channel = self.client.get_channel(starboard_channel)

                    if starboard_channel is None:
                        await db.update_value_in_table(payload.guild_id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "starboard_channel", None)
                        return

                    message_id = payload.message_id
                    channel_id = payload.channel_id
                    message_channel = self.client.get_channel(channel_id)
                    message = await message_channel.fetch_message(message_id)

                    if message.author.id == payload.user_id:
                        try:
                            await message.remove_reaction(emoji="⭐", member=payload.member)
                        except:
                            pass
                        return

                    target_reaction = next((reaction for reaction in message.reactions if reaction.emoji == "⭐"), None)
                    target_reaction_count = target_reaction.count if target_reaction else 0

                    starboard = await db.get_value_from_table(message.guild.id, "ServerConfigurations", "Setting", "Feature", "STARBOARD")
                    starboard = json.loads(starboard)
                    starboard_data = starboard.get(str(message_id))

                    if starboard_data is None:
                        return

                    try:
                        starboard_message_id = await starboard_channel.fetch_message(starboard_data["starboard_message"])
                    except discord.NotFound:
                        # Handle the case where the starboard message is not found
                        if target_reaction_count != 0:
                            embed = await create_starboard_embed(message)
                            view = discord.ui.View()
                            source = discord.ui.Button(emoji="⭐", url=message.jump_url, style=discord.ButtonStyle.link)
                            view.add_item(source)

                            starboarded = await starboard_channel.send(embed=embed, view=view)

                            data = {"channel": channel_id, "starboard_message": starboarded.id}
                            await db.update_value_in_table(payload.guild_id, "ServerConfigurations", "Setting", "Feature", "STARBOARD", message_id, data)
                        return

                    starboard_embed = starboard_message_id.embeds[0].to_dict()

                    await db.update_leaderboard_stat(message.author, "stars", -1)
                    starboard_embed["footer"]["text"] = f"⭐ {target_reaction_count} | {message.author.id}"

                    if target_reaction_count != 0:
                        embed = discord.Embed.from_dict(starboard_embed)
                        await starboard_message_id.edit(embed=embed)
                    else:
                        await starboard_message_id.delete()
                        await db.remove_value_from_table(message.guild.id, "ServerConfigurations", "Setting", "Feature", "STARBOARD", str(message_id))
                        return


    # ON AUTOMOD RULE CREATE
    # ----------------------
    @commands.Cog.listener("on_auto_moderation_rule_create")
    @commands.Cog.listener()
    async def on_auto_moderation_rule_create(self, rule: discord.AutoModRule):

        if self.mod_rule:
            self.mod_rule = False
            return

        self.mod_rule = True

        guild = self.client.get_guild(rule.guild_id)
        
        channels = await db.get_value_from_table(guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")
        toggles = await db.get_value_from_table(guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES")
        
        if channels and toggles:
            toggles = json.loads(toggles)
            channels = json.loads(channels)
            audit_log_toggle = toggles.get("audit_logs")
            audit_log_channel = channels.get("audit_log_channel")

            if audit_log_toggle:
                logChannel = guild.get_channel(audit_log_channel)
                if logChannel is None:
                    await db.update_value_in_table(guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "audit_log_channel", None)
                    await db.update_value_in_table(guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "audit_logs", False)
                    return

                creator = guild.get_member(rule.creator_id)
                embed = await db.build_embed(guild, title="<a:Information:1247223152367636541> AutoMod Rule Created", description=f"{creator.mention} created the **{rule.name}** AutoMod rule.")
                embed.set_thumbnail(url="")
                await logChannel.send(embed=embed)


    # ON AUTOMOD RULE DELETE
    # ----------------------
    @commands.Cog.listener("on_auto_moderation_rule_delete")
    @commands.Cog.listener()
    async def on_auto_moderation_rule_delete(self, rule: discord.AutoModRule):
       
        if self.mod_rule:
            self.mod_rule = False
            return
        
        self.mod_rule = True

        guild = self.client.get_guild(rule.guild_id)

        channels = await db.get_value_from_table(guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")
        toggles = await db.get_value_from_table(guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES")
        
        if channels and toggles:
            toggles = json.loads(toggles)
            channels = json.loads(channels)
            audit_log_toggle = toggles.get("audit_logs")
            audit_log_channel = channels.get("audit_log_channel")

            if audit_log_toggle:
                entry = list(await guild.audit_logs(limit=1).flatten())[0]

                logChannel = guild.get_channel(audit_log_channel)
                if logChannel is None:
                    await db.update_value_in_table(guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "audit_log_channel", None)
                    await db.update_value_in_table(guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "audit_logs", False)
                    return

                embed = await db.build_embed(guild, title="<a:Information:1247223152367636541> AutoMod Rule Deleted", description=f"{entry.user.mention} deleted the **{rule.name}** AutoMod rule.")
                embed.set_thumbnail(url="")
                await logChannel.send(embed=embed)


    # ON AUTOMOD RULE UPDATE
    # ----------------------
    @commands.Cog.listener("on_auto_moderation_rule_update")
    @commands.Cog.listener()
    async def on_auto_moderation_rule_update(self, rule: discord.AutoModRule):

        if self.mod_rule:
            self.mod_rule = False
            return
        
        self.mod_rule = True

        guild = self.client.get_guild(rule.guild_id)

        channels = await db.get_value_from_table(guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")
        toggles = await db.get_value_from_table(guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES")
        
        if channels and toggles:
            toggles = json.loads(toggles)
            channels = json.loads(channels)
            audit_log_toggle = toggles.get("audit_logs")
            audit_log_channel = channels.get("audit_log_channel")

            if audit_log_toggle:
                entry = list(await guild.audit_logs(limit=1).flatten())[0]

                logChannel = guild.get_channel(audit_log_channel)
                if logChannel is None:
                    await db.update_value_in_table(guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "audit_log_channel", None)
                    await db.update_value_in_table(guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "audit_logs", False)
                    return
                
                embed = await db.build_embed(guild, title="<a:Information:1247223152367636541> AutoMod Rule Updated", description=f"{entry.user.mention} updated the **{rule.name}** AutoMod rule.")
                embed.set_thumbnail(url="")
                await logChannel.send(embed=embed)
    

    # ON AUTOMOD RULE EXECUTION
    # -------------------------
    @commands.Cog.listener("on_auto_moderation_action_execution")
    @commands.Cog.listener()
    async def on_auto_moderation_action_execution(self, payload: discord.AutoModActionExecutionEvent):

        cooldown_seconds = 1
        current_time = time.time()

        if payload.guild.id in self.last_execution_time:
            last_execution = self.last_execution_time[payload.guild.id]
            if current_time - last_execution < cooldown_seconds:
                return False

        self.last_execution_time[payload.guild.id] = current_time
    
        channels = await db.get_value_from_table(payload.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")
        toggles = await db.get_value_from_table(payload.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES")
        
        if channels and toggles:
            toggles = json.loads(toggles)
            channels = json.loads(channels)
            moderation_log_channel = channels.get("moderation_log_channel")

            if moderation_log_channel:
                logChannel = discord.utils.get(payload.guild.channels, id=moderation_log_channel)
                
                if logChannel is None:
                    await db.update_value_in_table(payload.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "moderation_log_channel", None)
                    return

                if payload.matched_keyword is not None:
                    payload_content = payload.content.replace(payload.matched_keyword, f"**{payload.matched_keyword}**")
                else:
                    payload_content = payload.content

                payload_rule = await payload.guild.fetch_auto_moderation_rule(payload.rule_id)
                embed = await db.build_embed(payload.guild, title="<a:Moderation:1247220777627942974> AutoMod Rule Executed", description=f"**{payload.member.display_name}**'s message was blocked by the **{payload_rule}** rule in {payload.channel.mention}.")
                embed.add_field(name="Message", value=payload_content[:1024], inline=True)
                embed.set_footer(text=f"Member ID ➭ {payload.member.id}")
                embed.set_thumbnail(url="https://i.imgur.com/01FhEhR.png")
                await logChannel.send(embed=embed, view=AutoMod(self.client))
    
    
    # ON WEBHOOK UPDATE
    # -----------------
    @commands.Cog.listener("on_webhooks_update")
    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):

        if self.webhook_updated:
            self.webhook_updated = False
            return
        
        self.webhook_updated = True
        channels = await db.get_value_from_table(channel.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")
        toggles = await db.get_value_from_table(channel.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES")

        if channels and toggles:
            toggles = json.loads(toggles)
            channels = json.loads(channels)
            audit_log_toggle = toggles.get("audit_logs")
            audit_log_channel = channels.get("audit_log_channel")

            if audit_log_toggle:
                logChannel = self.client.get_channel(audit_log_channel)
                if logChannel is None:
                    await db.update_value_in_table(channel.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "audit_log_channel", None)
                    await db.update_value_in_table(channel.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "audit_logs", False)
                    return
                    
                entry = list(await channel.guild.audit_logs(limit=1).flatten())[0]
                if entry.action == discord.AuditLogAction.webhook_update:
                    before = entry.before
                    after = entry.after

                    if "channel" in before.__dict__ and before.channel != after.channel:
                        embed = await db.build_embed(channel.guild, title="<a:Information:1247223152367636541> Webhook Channel Updated", description=f"{entry.user.mention} moved a webhook to a new channel.")
                        embed.add_field(name="Before", value=before.channel.mention, inline=True)
                        embed.add_field(name="After", value=after.channel.mention, inline=True)
                        embed.set_thumbnail(url="")

                        await logChannel.send(embed=embed)
                        return
            
                    if "name" in before.__dict__ and before.name != after.name:
                        embed = await db.build_embed(channel.guild, title="<a:Information:1247223152367636541> Webhook Name Updated", description=f"{entry.user.mention} updated the name of a webhook for the {channel.mention} channel.")
                        embed.add_field(name="Before", value=before.name, inline=True)
                        embed.add_field(name="After", value=after.name, inline=True)
                        embed.set_thumbnail(url="")

                        await logChannel.send(embed=embed)
                        return

                    if "avatar" in before.__dict__ and before.avatar != after.avatar:
                        embed = await db.build_embed(channel.guild, title="<a:Information:1247223152367636541> Webhook Avatar Updated", description=f"{entry.user.mention} updated the avatar of a webhook for the {channel.mention} channel.")
                        embed.set_thumbnail(url=after.display_avatar.url)
                        await logChannel.send(embed=embed)
                        return
                
                elif entry.action == discord.AuditLogAction.webhook_create:
                    action = "created"
                elif entry.action == discord.AuditLogAction.webhook_delete:
                    action = "deleted"
                else:
                    action = "updated"

                embed = await db.build_embed(channel.guild, title=f"<a:Information:1247223152367636541> Webhook {action.title()}", description=f"{entry.user.mention} {action} a webhook for the {channel.mention} channel.")
                embed.set_thumbnail(url="")
                await logChannel.send(embed=embed)


    # ON STICKER UPDATE
    # -----------------
    @commands.Cog.listener("on_guild_stickers_update")
    async def on_guild_stickers_update(self, guild, before, after):
        channels = await db.get_value_from_table(guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")
        toggles = await db.get_value_from_table(guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES")
        
        if channels and toggles:
            toggles = json.loads(toggles)
            channels = json.loads(channels)
            audit_log_toggle = toggles.get("audit_logs")
            audit_log_channel = channels.get("audit_log_channel")

            if audit_log_toggle:
                logChannel = discord.utils.get(guild.channels, id=audit_log_channel)
                if logChannel is None:
                    await db.update_value_in_table(guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "audit_log_channel", None)
                    await db.update_value_in_table(guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "audit_logs", False)
                    return
                
                entry = list(await guild.audit_logs(limit=1).flatten())[0]

                added_stickers = set(after) - set(before)
                removed_stickers = set(before) - set(after)

                for sticker in added_stickers:
                    embed = await db.build_embed(guild, title="<a:Information:1247223152367636541> Sticker Added", description=f"{entry.user.mention} added the **{sticker.name}** sticker to the server.")
                    embed.set_thumbnail(url=sticker.url)
                    await logChannel.send(embed=embed)

                for sticker in removed_stickers:
                    embed = await db.build_embed(guild, title="<a:Information:1247223152367636541> Sticker Removed", description=f"{entry.user.mention} removed the **{sticker.name}** sticker from the server.")
                    embed.set_thumbnail(url=sticker.url)
                    await logChannel.send(embed=embed)


    # ON EMOJI UPDATE
    # ---------------
    @commands.Cog.listener("on_guild_emojis_update")
    async def on_guild_emojis_update(self, guild, before, after):
        channels = await db.get_value_from_table(guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")
        toggles = await db.get_value_from_table(guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES")
        
        if channels and toggles:
            toggles = json.loads(toggles)
            channels = json.loads(channels)
            audit_log_toggle = toggles.get("audit_logs")
            audit_log_channel = channels.get("audit_log_channel")

            if audit_log_toggle:
                logChannel = discord.utils.get(guild.channels, id=audit_log_channel)
                if logChannel is None:
                    await db.update_value_in_table(guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "audit_log_channel", None)
                    await db.update_value_in_table(guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "audit_logs", False)
                    return
                
                entry = list(await guild.audit_logs(limit=1).flatten())[0]

                added_emojis = set(after) - set(before)
                removed_emojis = set(before) - set(after)

                for emoji in added_emojis:
                    embed = await db.build_embed(guild, title="<a:Information:1247223152367636541> Emoji Added", description=f"{entry.user.mention} added the **{emoji.name}** emoji to the server.")
                    embed.set_thumbnail(url=emoji.url)
                    await logChannel.send(embed=embed)

                for emoji in removed_emojis:
                    embed = await db.build_embed(guild, title="<a:Information:1247223152367636541> Emoji Removed", description=f"{entry.user.mention} removed the **{emoji.name}** emoji from the server.")
                    embed.set_thumbnail(url=emoji.url)
                    await logChannel.send(embed=embed)


    # ON BULK MESSAGE DELETE
    # ----------------------
    @commands.Cog.listener("on_bulk_message_delete")
    async def on_bulk_message_delete(self, messages):

            guild = messages[0].guild if messages else None

            if guild:
                channels = await db.get_value_from_table(guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")

                if channels:
                    channels = json.loads(channels)
                    moderation_log_channel = channels.get("moderation_log_channel")

                    if moderation_log_channel:
                        logChannel = discord.utils.get(guild.channels, id=moderation_log_channel)
            
                        if logChannel is None:
                            await db.update_value_in_table(guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "moderation_log_channel", None)
                            return

                        entry = list(await guild.audit_logs(limit=1).flatten())[0]
                        embed = await db.build_embed(guild, title="<a:Moderation:1247220777627942974> Messages Cleared", description=f"{entry.user.mention} cleared **{len(messages)}** messages in {messages[0].channel.mention}.")
                        try:
                            await logChannel.send(embed=embed)
                        except discord.Forbidden:
                            await db.update_value_in_table(guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "moderation_log_channel", None)


    # ON MESSAGE DELETE
    # -----------------
    @commands.Cog.listener("on_message_delete")
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        
        sniped[message.channel.id] = {"message": message.content, "author": message.author.display_name}
        toggles = await db.get_value_from_table(message.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES")
        protections = await db.get_value_from_table(message.guild.id, "ServerConfigurations", "Setting", "Feature", "PROTECTIONS")
        channels = await db.get_value_from_table(message.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")

        if toggles and channels:
            toggles = json.loads(toggles)
            channels = json.loads(channels)
            audit_log_channel = channels.get("audit_log_channel")
            moderation_log_channel = channels.get("moderation_log_channel")
            audit_log_state = toggles.get("audit_logs")
            
            # Message Deletion Logs
            if audit_log_state:
                logChannel = discord.utils.get(message.guild.channels, id=audit_log_channel)
                if logChannel is None:
                    await db.update_value_in_table(message.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "audit_log_channel", None)
                    await db.update_value_in_table(message.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "audit_logs", False)
                    return

                entry = list(await message.guild.audit_logs(limit=1).flatten())[0]
                if entry.action == discord.AuditLogAction.message_delete:
                    descr = f"{message.author.mention}'s message was deleted in {message.channel.mention} by {entry.user.mention}."
                else:
                    descr = f"{message.author.mention} deleted a message in {message.channel.mention}."

                embed = await db.build_embed(message.guild, title="<a:Information:1247223152367636541> Message Deleted", description=descr)
                embed.set_thumbnail(url="")
                if message.attachments:
                    embed.set_image(url=message.attachments[0].url)
                embed.add_field(name="Message", value=message.content[:1024], inline=False)
                await logChannel.send(embed=embed)

                if message.embeds:
                    embed_msg = message.embeds[0]
                    await logChannel.send(embed=embed_msg)


        if protections:
            protections = json.loads(protections)
            anti_ghost_ping = protections.get("anti_ghost_ping")
            anti_selfbot = protections.get("anti_selfbot")

            # Anti-Ghost Ping
            if message.mentions and not message.author.bot and not message.author.guild_permissions.manage_messages:
                if anti_ghost_ping:
                    current_time = datetime.now(timezone.utc)

                    time_difference = (current_time - message.created_at).total_seconds()

                    threshold = 20

                    if time_difference <= threshold:
                        ghost_pinged_users = [user.mention for user in message.mentions if not user.bot and user != message.author]

                        if ghost_pinged_users:
                            mentioned_users = ", ".join(ghost_pinged_users)

                            embed = await db.build_embed(message.guild, title="<a:Moderation:1247220777627942974> Ghost Ping Detected", description=f"{message.author.mention} `({message.author.id})` ghost pinged {mentioned_users}.")
                            embed.set_thumbnail(url="")
                            embed.add_field(name="Message", value=message.content, inline=False)
                            await message.channel.send(embed=embed)

                            if moderation_log_channel:
                                logChannel = discord.utils.get(message.guild.channels, id=moderation_log_channel)
                
                                if logChannel is None:
                                    await db.update_value_in_table(message.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "moderation_log_channel", None)
                                    return
                                
                                embed = await db.build_embed(message.guild, title="<a:Moderation:1247220777627942974> Ghost Ping Detected", description=f"{message.author.mention} `({message.author.id})` ghost pinged {mentioned_users} in {message.channel.mention}.")
                                embed.set_thumbnail(url="")
                                embed.add_field(name="Message", value=message.content, inline=False)
                                await logChannel.send(embed=embed)


            # Anti-Selfbot
            if not message.author.guild_permissions.manage_messages:
                if anti_selfbot:
                    selfbot_prefixes = [".", ",", "!", ">", "<", "?", "/", ":", ";", "'", '"', "[", "]", "{", "}", "|", "\\", "`", "~", "#", "$", "%", "^", "&", "*", "(", ")", "_", "-", "+", "="]
                    for prefix in selfbot_prefixes:
                        if message.content.startswith(prefix):
                            current_time = datetime.utcnow().replace(tzinfo=pytz.utc)
                            if (current_time - message.created_at).total_seconds() <= 1:
                                
                                suggestions = await db.get_value_from_table(message.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")
                                if suggestions:
                                    suggestions = json.loads(suggestions)
                                    suggestion_channel = suggestions.get("suggestion_channel")

                                    if message.channel.id == suggestion_channel:
                                        return
                                    
                                embed = await db.build_embed(message.guild, title="<a:Moderation:1247220777627942974> Selfbot Detected", description=f"Selfbots are prohibited in {message.guild.name}.")
                                embed.set_thumbnail(url="")
                                embed.add_field(name="Message", value=message.content, inline=False)
                                await message.channel.send(embed=embed, delete_after=10)

                                def userCheck(m):
                                    return m.author.id == message.author.id

                                await message.channel.purge(limit=2, check=userCheck)

                                if moderation_log_channel:
                                    logChannel = discord.utils.get(message.guild.channels, id=moderation_log_channel)

                                    if logChannel is None:
                                        await db.update_value_in_table(message.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "moderation_log_channel", None)
                                        return        
                                    
                                    embed = await db.build_embed(message.guild, title="<a:Moderation:1247220777627942974> Selfbot Detected", description=f"{message.author.mention} `({message.author.id})` used a selfbot in {message.channel.mention}.")
                                    embed.set_thumbnail(url="")
                                    embed.add_field(name="Message", value=message.content, inline=False)
                                    await logChannel.send(embed=embed)                                   


    # ON GUILD UPDATE
    # ---------------
    @commands.Cog.listener("on_guild_update")
    async def on_guild_update(self, before, after):

        channels = await db.get_value_from_table(before.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")
        toggles = await db.get_value_from_table(before.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES")

        if channels and toggles:
            channels = json.loads(channels)
            toggles = json.loads(toggles)
            audit_log_channel = channels.get("audit_log_channel")
            audit_logs = toggles.get("audit_logs")

            if audit_logs:
                logChannel = discord.utils.get(before.channels, id=audit_log_channel)
                if logChannel is None:
                    await db.update_value_in_table(before.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "audit_log_channel", None)
                    await db.update_value_in_table(before.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "audit_logs", False)
                    return

                try:
                    entry = list(await before.audit_logs(limit=1).flatten())[0]
                except:
                    return
                
                explicit_filter_labels = {
                    discord.ContentFilter.all_members: "All Members",
                    discord.ContentFilter.no_role: "No Roles",
                    discord.ContentFilter.disabled: "Disabled",
                }

                notif_dict = {
                    discord.NotificationLevel.all_messages: "All Messages",
                    discord.NotificationLevel.only_mentions: "Only Mentions"
                }
                
                if before.name != after.name:
                    embed = await db.build_embed(before, title="<a:Information:1247223152367636541> Server Name Updated", description=f"The servers name was changed by {entry.user.mention}.")
                    embed.set_thumbnail(url="")
                    embed.add_field(name="Old Name", value=before.name, inline=True)
                    embed.add_field(name="New Name", value=after.name, inline=True)
                    await logChannel.send(embed=embed)

                if before.preferred_locale != after.preferred_locale:
                    embed = await db.build_embed(before, title="<a:Information:1247223152367636541> Server Region Updated", description=f"The servers preferred region was changed by {entry.user.mention}.")
                    embed.set_thumbnail(url="")
                    embed.add_field(name="Old Region", value=before.preferred_locale, inline=True)
                    embed.add_field(name="New Region", value=after.preferred_locale, inline=True)
                    await logChannel.send(embed=embed)

                if before.verification_level != after.verification_level:
                    embed = await db.build_embed(before, title="<a:Information:1247223152367636541> Server Verification Updated", description=f"The servers verification level was changed by {entry.user.mention}.")
                    embed.set_thumbnail(url="")
                    embed.add_field(name="Old Level", value=str(before.verification_level).capitalize(), inline=True)
                    embed.add_field(name="New Level", value=str(after.verification_level).capitalize(), inline=True)
                    await logChannel.send(embed=embed)

                if before.default_notifications != after.default_notifications:
                    embed = await db.build_embed(before, title="<a:Information:1247223152367636541> Server Notifications Updated", description=f"The server's default notification setting was updated by {entry.user.mention}.")
                    embed.set_thumbnail(url="")
                    embed.add_field(name="Old Notification Setting", value=notif_dict.get(before.default_notifications, "Unknown"), inline=True)
                    embed.add_field(name="New Notification Setting", value=notif_dict.get(after.default_notifications, "Unknown"), inline=True)
                    await logChannel.send(embed=embed)

                if before.explicit_content_filter != after.explicit_content_filter:
                    event_value_before = explicit_filter_labels.get(before.explicit_content_filter, "Unknown")
                    event_value_after = explicit_filter_labels.get(after.explicit_content_filter, "Unknown")
                    embed = await db.build_embed(before, title="<a:Information:1247223152367636541> Server Filter Updated", description=f"The servers explicit filter setting was changed by {entry.user.mention}.")
                    embed.set_thumbnail(url="")
                    embed.add_field(name="Old Filter Setting", value=event_value_before, inline=True)
                    embed.add_field(name="New Filter Setting", value=event_value_after, inline=True)
                    await logChannel.send(embed=embed)

                if before.mfa_level != after.mfa_level:
                    embed = await db.build_embed(before, title="<a:Information:1247223152367636541> Server MFA Updated", description=f"The servers MFA level was changed by {entry.user.mention}.")
                    embed.set_thumbnail(url="")
                    embed.add_field(name="Old MFA Level", value=before.mfa_level, inline=True)
                    embed.add_field(name="New MFA Level", value=after.mfa_level, inline=True)
                    await logChannel.send(embed=embed)


    # ON MEMBER UPDATE
    # ----------------
    @commands.Cog.listener("on_member_update")
    async def on_member_update(self, before, after):

        channels = await db.get_value_from_table(before.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")
        toggles = await db.get_value_from_table(before.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES")
        roles = await db.get_value_from_table(before.guild.id, "ServerConfigurations", "Setting", "Feature", "ROLES")

        if channels and toggles:
            channels = json.loads(channels)
            toggles = json.loads(toggles)
            roles = json.loads(roles)
            audit_log_channel = channels.get("audit_log_channel")
            moderation_log_channel = channels.get("moderation_log_channel")
            audit_logs = toggles.get("audit_logs")
            counter_role = roles.get("custom_role_counter")

            if moderation_log_channel is not None:
                
                try:
                    entry = list(await before.guild.audit_logs(limit=1).flatten())[0]
                except:
                    return
                
                cmdChannel = discord.utils.get(before.guild.channels, id=moderation_log_channel)
                if cmdChannel is None:
                    await db.update_value_in_table(before.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "moderation_log_channel", None)
                    return

                if before.timed_out < after.timed_out:
                    embed = await db.build_embed(before.guild, title="<a:Moderation:1247220777627942974> Member Muted", description=f"{before.mention} has been muted.")
                    embed.add_field(name="Reason", value=entry.reason, inline=False)
                    embed.set_thumbnail(url="")
                    await cmdChannel.send(embed=embed)

                if before.timed_out > after.timed_out:
                    embed = await db.build_embed(before.guild, title="<a:Moderation:1247220777627942974> Member Unmuted", description=f"{before.mention} was unmuted.")
                    embed.add_field(name="Reason", value=entry.reason, inline=False)
                    embed.set_thumbnail(url="")
                    await cmdChannel.send(embed=embed)

            if audit_logs:
                try:
                    entry = list(await before.guild.audit_logs(limit=1).flatten())[0]
                except:
                    return
                
                logChannel = self.client.get_channel(audit_log_channel)
                
                if logChannel is None:
                    await db.update_value_in_table(before.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "audit_log_channel", None)
                    await db.update_value_in_table(before.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "audit_logs", False)
                    return

                if before.display_name != after.display_name:
                    embed = await db.build_embed(before.guild, title="<a:Information:1247223152367636541> Nickname Changed", description=f"The nickname of {before.mention} was changed by {entry.user.mention}.")
                    embed.set_thumbnail(url="")
                    embed.add_field(name="Old Nickname", value=before.display_name, inline=True)
                    embed.add_field(name="New Nickname", value=after.display_name, inline=True)
                    await logChannel.send(embed=embed)

                if before.roles != after.roles:
                    totalBefore = [role.mention for role in before.roles]
                    totalAfter = [role.mention for role in after.roles]

                    addedRole = [x for x in totalAfter if x not in totalBefore]
                    removedRole = [x for x in totalBefore if x not in totalAfter]

                    if len(totalBefore) < len(totalAfter):
                        embed = await db.build_embed(before.guild, title="<a:Information:1247223152367636541> Role Added", description=f"{before.mention} has received the {' '.join(addedRole)} {'role' if len(addedRole) == 1 else 'roles'} from {entry.user.mention}.")
                        embed.set_thumbnail(url="")
                        await logChannel.send(embed=embed)
                    else:
                        embed = await db.build_embed(before.guild, title="<a:Information:1247223152367636541> Role Removed", description=f"{before.mention} was removed from the {' '.join(removedRole)} {'role' if len(removedRole) == 1 else 'roles'} by {entry.user.mention}.")
                        embed.set_thumbnail(url="")
                        await logChannel.send(embed=embed)

                    role_id_present = any(role.id == counter_role for role in before.roles) or any(role.id == counter_role for role in after.roles)
                    if role_id_present:
                        try:
                            channel = custom_role_counters.get(before.guild.id)
                            role = before.guild.get_role(int(counter_role))
                            channel = before.guild.get_channel(int(channel))

                            if channel is None:
                                # Channel no longer exists; remove from database and cache
                                await db.update_value_in_table(before.guild.id, "ServerConfigurations", "Setting", "Feature", "COUNTERS", "custom_role_counter", None)
                                await db.update_value_in_table(before.guild.id, "ServerConfigurations", "Setting", "Feature", "ROLES", "custom_role_counter", None)
                                del custom_role_counters[before.guild.id]
                            elif role is None:
                                # Role no longer exists; remove from database and cache
                                await db.update_value_in_table(before.guild.id, "ServerConfigurations", "Setting", "Feature", "COUNTERS", "custom_role_counter", None)
                                await db.update_value_in_table(before.guild.id, "ServerConfigurations", "Setting", "Feature", "ROLES", "custom_role_counter", None)
                                del custom_role_counters[before.guild.id]
                            else:
                                name_parts = channel.name.split(":")
                                if len(name_parts) >= 2:
                                    text_part = name_parts[0].strip()
                                    await channel.edit(name=f"{text_part}: {len(role.members) if role else 0}")
                        except Exception as e:
                            print("[custom_role_counter]: ", e)


    # ON MEMBER BAN
    # -------------
    @commands.Cog.listener("on_member_ban")
    async def on_member_ban(self, guild, member: discord.Member):

        channels = await db.get_value_from_table(guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")

        if channels:
            channels = json.loads(channels)
            moderation_log_channel = channels.get("moderation_log_channel")

            if moderation_log_channel:
                channel = discord.utils.get(guild.channels, id=moderation_log_channel)
                
                if channel is None:
                    await db.update_value_in_table(guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "moderation_log_channel", None)
                    return

                try:
                    entry = list(await guild.audit_logs(limit=1).flatten())[0]
                except:
                    return
                
                if not entry.user == self.client.user:
                    embed = await db.build_embed(guild, title="<a:Moderation:1247220777627942974> Member Banned", description=f"{member.mention} was banned by {entry.user.mention}.")
                    embed.set_thumbnail(url="")
                    embed.add_field(name="Reason", value=entry.reason if entry.reason != None else "No Reason Provided.", inline=False)
                    await channel.send(embed=embed)


    # ON MEMBER UNBAN
    # ---------------
    @commands.Cog.listener("on_member_unban")
    async def on_member_unban(self, guild, member: discord.Member):
        channels = await db.get_value_from_table(guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")

        if channels:
            channels = json.loads(channels)
            moderation_log_channel = channels.get("moderation_log_channel")

            if moderation_log_channel:
                channel = discord.utils.get(guild.channels, id=moderation_log_channel)
                if channel is None:
                    await db.update_value_in_table(guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "moderation_log_channel", None)
                    return

                try: 
                    entry = list(await channel.guild.audit_logs(limit=1).flatten())[0] 
                except: 
                    return

            if not entry.user == self.client.user:
                embed = await db.build_embed(guild, title="<a:Moderation:1247220777627942974> Ban Removed", description=f"{member.mention} was unbanned by {entry.user.mention}.")
                embed.set_thumbnail(url="")
                embed.add_field(name="Reason", value=entry.reason, inline=False)
                await channel.send(embed=embed)


    # ON MEMBER JOIN
    # --------------
    @commands.Cog.listener("on_member_join")
    async def on_member_join(self, member: discord.Member):

        channels = await db.get_value_from_table(member.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")
        toggles = await db.get_value_from_table(member.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES")
        protections = await db.get_value_from_table(member.guild.id, "ServerConfigurations", "Setting", "Feature", "PROTECTIONS")

        if member.guild.id in raided:
            await member.send(content="The server is currently being raided, please try rejoining later.")
            await member.kick(reason="Anti-Raid Triggered")
            return

        inviter_obj = None
        if not member.bot:
            try:
                invites = await member.guild.invites()
            except Exception as e:
                invites = None

            if invites is not None:
                inviter = None
                inviter_obj = None

                for invite in invites:
                    if invite_cache.get(invite.code) is not None and invite_cache[invite.code] < invite.uses:
                        inviter = invite.inviter
                        break

                if inviter:
                    try:
                        await db.update_invite_data(member.guild, inviter, member)
                        invite_cache[invite.code] += 1
                        inviter = member.guild.get_member(inviter.id)
                        if inviter:
                            total_invites = await db.get_leaderboard_data(inviter, "invited_users")
                            inviter_obj = inviter
                            invite_code = invite.code
                            inviter = f"{inviter.name} ({len(total_invites)} Invites)"
                        else:
                            inviter = "Vanity URL"
                    except Exception as e:
                        print(f"Error updating invite data: {e}")
                        inviter = "Error"
                else:
                    inviter = "Vanity URL"
            else:
                inviter = "Missing Permissions"
        else:
            inviter = "OAuth"

        if protections and channels:
            protections = json.loads(protections)
            anti_raid = protections.get("anti_raid")

            if anti_raid:
                if inviter_obj is not None:
                    await Utils.check_anti_raid(self, member, inviter_obj, invite_code)
                else:
                    await Utils.check_anti_raid(self, member, None, None)

        if channels and toggles:
            channels = json.loads(channels)
            toggles = json.loads(toggles)
            welcome_channel = channels.get("welcome_channel")
            auto_roles = toggles.get("auto_roles")
            welcome_messages = toggles.get("welcome_messages")

            if auto_roles:
                roles = await db.get_value_from_table(member.guild.id, "ServerConfigurations", "Setting", "Feature", "ROLES")
                
                if roles:
                    roles = json.loads(roles)
                    auto_role_id = roles.get("auto_role")

                    bot_user = member.guild.me
                    role = member.guild.get_role(auto_role_id)
                    bot_role = bot_user.top_role.position

                    if role and bot_user.guild_permissions.manage_roles and role.position < bot_role:
                        await member.add_roles(role)

            if welcome_messages:
                try:
                    log_channel = discord.utils.get(member.guild.channels, id=welcome_channel)
                except:
                    await db.update_value_in_table(member.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "welcome_channel", None)
                    await db.update_value_in_table(member.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "welcome_messages", False)
                    return

                if log_channel is None:
                    await db.update_value_in_table(member.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "welcome_channel", None)
                    await db.update_value_in_table(member.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "welcome_messages", False)
                    return
                
                headers = {
                    "Accept": "application/json",
                    "content-type": "application/json",
                    "Authorization": "Bot " + config["token"]}

                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://discord.com/api/users/{member.id}", headers=headers) as a:
                        data = await a.json(content_type="application/json")

                if data["banner"] == None:
                    banner_url = ""
                elif data["banner"].startswith("a_"):
                    banner_url = f"https://cdn.discordapp.com/banners/{member.id}/{data['banner']}.gif?size=4096"
                elif data["banner"] != None:
                    banner_url = f"https://cdn.discordapp.com/banners/{member.id}/{data['banner']}.png?size=4096"

                welcome_messages = [
                    "Enjoy your time in the server!",
                    "Feel at home and have a great time!",
                    "Excited to have you with us!",
                    "Welcome to the community!",
                    "Get ready for an awesome experience!",
                    "Your journey in the server begins!",
                    "Let the fun and adventure commence!",
                    "Thrilled to welcome you!",
                    "Thanks for joining us!",
                    "Glad to have you here!",
                    "Welcome to our friendly community!",
                    "The server just got better with you!",
                    "Happy to see you join!",
                    "Get ready for some great moments!",
                    "Your presence is appreciated!",
                    "Welcome aboard!",
                    "We hope you enjoy your stay!",
                    "Looking forward to great times together!",
                    "Cheers to a fantastic experience!",
                    "Welcome to the server family!",
                    "Exciting times ahead!",
                    "Enjoy the ride!",
                ]
                
                if member.guild.rules_channel:
                    welcome_messages.append(f"Make sure to check out the {member.guild.rules_channel.mention} channel!")

                random_message = random.choice(welcome_messages)
                
                creation_timestamp = int(member.created_at.timestamp())
                embed = await db.build_embed(member.guild, title=f"<a:Wave:1247223147044798484> Welcome, {member.display_name}!",
                description=
                    f"{random_message}\n\n"
                    + f"**__About {member.display_name}__**\n"
                    + f"**Username** ➭ {member.mention} / {member.name}\n"
                    + f"**ID** ➭ {member.id}\n"
                    + f"**Invited By** ➭ {inviter}\n"
                    + f"**Creation Date** ➭ <t:{creation_timestamp}:d> (<t:{creation_timestamp}:R>)\n"
                )
                
                embed.set_thumbnail(url=member.display_avatar.with_size(64).url)
                embed.set_image(url=banner_url)
                embed.set_footer(text=f"Total Members: {member.guild.member_count}")
                embed.timestamp = datetime.now()
                try:
                    await log_channel.send(embed=embed)
                except discord.Forbidden:
                    await db.update_value_in_table(member.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "welcome_channel", None)
                    await db.update_value_in_table(member.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "welcome_messages", False)
                    return               


        # Member Counter
        if member.guild.id in member_counters:
            try:
                channel = member_counters[member.guild.id]
                channel = member.guild.get_channel(int(channel))
                if channel is None:
                    await db.update_value_in_table(member.guild.id, "ServerConfigurations", "Setting", "Feature", "COUNTERS", "member_counter", None)
                    del member_counters[member.guild.id]
                else:
                    name_parts = channel.name.split(":")
                    if len(name_parts) >= 2:
                        text_part = name_parts[0].strip()
                        await channel.edit(name=f"{text_part}: {member.guild.member_count}")

            except Exception as e:
                print(f"[member_counter]: ", e)


    # ON MEMBER LEAVE
    # ---------------
    @commands.Cog.listener("on_member_remove")
    async def on_member_remove(self, member: discord.Member):

        if member == self.client.user:
            return
        
        inviter = None
        if not member.bot:
            guild_data = await db.get_all_leaderboard_data_1(member.guild.id)
            leaving_member_id = member.id

            if guild_data:

                for inviter_id, user_data in guild_data.items():
                    invited_users = user_data.get("invited_users", [])
                    if leaving_member_id in invited_users:
                        inviter = member.guild.get_member(int(inviter_id))
                        if inviter:
                            await db.remove_user_from_invite_list(member.guild, inviter, member)
                            total_invites = await db.get_leaderboard_data(inviter, "invited_users")
                            break  # Break the loop once the inviter is found and processed

                if inviter is None:
                    inviter = "Vanity URL"
                else:
                    total_invites = await db.get_leaderboard_data(inviter, "invited_users")
                    total_invites = len(total_invites) if total_invites else 0
                    inviter = f"{inviter.name} ({total_invites} Invites)"
        else:
            inviter = "OAuth"

        channels = await db.get_value_from_table(member.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")
        toggles = await db.get_value_from_table(member.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES")

        if channels and toggles:
            channels = json.loads(channels)
            toggles = json.loads(toggles)
            welcome_channel = channels.get("welcome_channel")
            moderation_log_channel = channels.get("moderation_log_channel")
            welcome_messages = toggles.get("welcome_messages")

            if welcome_messages:
                log_channel = discord.utils.get(member.guild.channels, id=welcome_channel)
                
                if log_channel is None:
                    await db.update_value_in_table(member.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "welcome_channel", None)
                    await db.update_value_in_table(member.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "welcome_messages", False)
                    return
                    
                join_date = member.joined_at.replace(tzinfo=timezone.utc)
                current_time = datetime.now(timezone.utc)
                total_time_in_server = current_time - join_date

                total_seconds = int(total_time_in_server.total_seconds())
                days, remainder = divmod(total_seconds, 86400)
                hours, remainder = divmod(remainder, 3600)
                minutes, seconds = divmod(remainder, 60)

                if days > 0:
                    formatted_total_time = f"**{days}** days"
                elif hours > 0:
                    formatted_total_time = f"**{hours}** hours"
                elif minutes > 0:
                    formatted_total_time = f"**{minutes}** minutes"
                else:
                    formatted_total_time = f"**{seconds}** seconds"

                ban_list = member.guild.bans()
                ban_list_data = []

                async for banned in ban_list:
                    ban_list_data.append(banned.user.id)
                
                if member.id not in ban_list_data:

                    farewell_messages = [
                        "I enjoyed our {} together.",
                        "I remember when you joined just {} ago...",
                        "Time flies! We had {} together.",
                        "Thanks for being part of our community for {}!",
                        "Wishing you all the best after {} with us.",
                        "Farewell! We'll miss the last {} with you.",
                        "It's been a great {} with you around.",
                        "Cheers to {} of memories together!",
                        "I'll never forget the first {} you joined.",
                        "Goodbye, and thanks for the {} of friendship.",
                        "You made the last {} unforgettable.",
                        "We'll always remember the {} you spent here.",
                        "Thanks for the memories during your {} here.",
                        "Your presence made the last {} special.",
                        "Best wishes on your journey after {} with us.",
                        "I can't believe it's been {} already!",
                        "Time spent with you – {} of pure joy.",
                        "We'll cherish the {} of laughter and fun.",
                        "Remembering the {} of great moments.",
                    ]

                    if inviter != "OAuth" and inviter != "Vanity URL":
                        farewell_messages.extend([
                            f"A big shoutout to **{inviter}** for bringing you into our community. I enjoyed our {{}} together.",
                            f"Thanks to **{inviter}** for the introduction! I remember when you joined just {{}} ago...",
                            f"Special thanks to **{inviter}** for inviting such a fantastic person. Time flies! We had {{}} together.",
                            f"A heartfelt thanks to **{inviter}**. Thanks for being part of our community for {{}}!",
                            f"**{inviter}** deserves credit for bringing you in. Wishing you all the best after {{}} with us.",
                            f"A special thanks to **{inviter}** for introducing us. Farewell! We'll miss the last {{}} with you.",
                            f"**{inviter}** played a key role in bringing you into our circle. It's been a great {{}} with you around.",
                            f"Shoutout to **{inviter}** for making it happen. Cheers to {{}} of memories together!",
                            f"Thanks to **{inviter}** for the invite. I'll never forget the first {{}} you joined.",
                            f"**{inviter}** introduced us to a great friend. Goodbye, and thanks for the {{}} of friendship.",
                            f"**{inviter}** had a hand in this unforgettable journey. You made the last {{}} unforgettable.",
                            f"Big thanks to **{inviter}** for bringing you into our community. We'll always remember the {{}} you spent here.",
                            f"Kudos to **{inviter}** for inviting you! Thanks for the memories during your {{}} here.",
                            f"Special thanks to **{inviter}**. Your presence made the last {{}} special.",
                            f"A huge thanks to **{inviter}** for bringing you in. Best wishes on your journey after {{}} with us.",
                            f"Time really does fly, doesn't it? I can't believe it's been {{}} already! Thanks to **{inviter}** for bringing you in.",
                            f"**{inviter}**, you brought pure joy into our community. Time spent with you – {{}} of pure joy.",
                            f"**{inviter}**, the memories of laughter and fun are priceless. We'll cherish the {{}} of laughter and fun.",
                            f"**{inviter}**, thanks for bringing this incredible person into our community. Remembering the {{}} of great moments.",
                        ])
                else:
                    farewell_messages = [
                        "Well, it seems the ban hammer has spoken. Farewell! Your time in the server was {}.",
                        "Breaking up is hard to do! Wishing you a drama-free journey wherever you go after {} here.",
                        "They say all good things must come to an end. Apparently, that includes your time here. Farewell, after {} with us!",
                        "Adiós! Your account may be banned, but your memories with us over the past {} are not forgotten.",
                        "Looks like your membership card got revoked. Farewell and good luck finding a new club after {} with us!",
                        "Farewell! We're sending you off with a virtual wave and a real ban. Take care after {} here!",
                        "They say parting is such sweet sorrow. Well, this is more on the bitter side. Goodbye after {} with us!",
                        "Banned but not forgotten. We'll always have the memories... and the ban log from your {} here.",
                        "So long! If life gives you lemons, hopefully, they're not in the form of ban notifications after {} with us.",
                        "Farewell! May your future endeavors be as un-banned as possible after {} here!",
                    ]

                random_message = random.choice(farewell_messages)

                embed = await db.build_embed(member.guild, title=f"<a:Wave:1247223147044798484> Goodbye, {member.display_name}.",
                description=
                f"{random_message.format(formatted_total_time)}\n\n")
                embed.set_thumbnail(url=member.display_avatar.with_size(64).url)
                embed.set_footer(text=f"Total Members: {member.guild.member_count}")
                embed.timestamp = datetime.now()
                await log_channel.send(embed=embed)

            try:
                entry = list(await member.guild.audit_logs(limit=1).flatten())[0]
            except:
                return
            
            if (str(entry.action) == "AuditLogAction.kick" and entry.target.id == member.id and moderation_log_channel != None):
                await asyncio.sleep(1)

                try:
                    log_channel = discord.utils.get(member.guild.channels, id=moderation_log_channel)
                    if log_channel is None:
                        await db.update_value_in_table(member.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "moderation_log_channel", None)
                        return
                    
                    embed = await db.build_embed(member.guild, title="<a:Moderation:1247220777627942974> Member Kicked", description=f"{member.mention} `({member.id})` has been kicked by {entry.user.mention}.")
                    embed.add_field(name="Reason", value=entry.reason, inline=False)
                    await log_channel.send(embed=embed)
                except discord.Forbidden:
                    await db.update_value_in_table(member.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "moderation_log_channel", None)


        # Member Counter
        if member.guild.id in member_counters:
            try:
                channel = member_counters[member.guild.id]
                channel = member.guild.get_channel(int(channel))
                if channel is None:
                    await db.update_value_in_table(member.guild.id, "ServerConfigurations", "Setting", "Feature", "COUNTERS", "member_counter", None)
                    del member_counters[member.guild.id]
                else:
                    name_parts = channel.name.split(":")
                    if len(name_parts) >= 2:
                        text_part = name_parts[0].strip()
                        await channel.edit(name=f"{text_part}: {member.guild.member_count}")

            except Exception as e:
                print(f"[member_counter]: ", e)
        
        # Check if the member has an open ticket
        ticket_data = await db.get_value_from_table(member.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

        if ticket_data:
            ticket_data = json.loads(ticket_data)
            ticket_data = ticket_data.get("ticket_data")
        
        open_tickets = ticket_data["open_tickets"]

        if str(member.id) in open_tickets:
            channel_id = open_tickets[str(member.id)]
            channel = member.guild.get_channel(int(channel_id))
            if channel:
                return await channel.send(f"<:left:1162404805583581255> {member.display_name} has left the server.")


    # ON ROLE CREATE
    # --------------
    @commands.Cog.listener("on_guild_role_create")
    async def on_guild_role_create(self, role: discord.Role):

        toggles = await db.get_value_from_table(role.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES")
        channels = await db.get_value_from_table(role.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")

        if channels and toggles:
            channels = json.loads(channels)
            toggles = json.loads(toggles)
            audit_log_channel = channels.get("audit_log_channel")
            audit_logs = toggles.get("audit_logs")

            if audit_logs:
                logChannel = self.client.get_channel(audit_log_channel)
                if logChannel is None:
                    await db.update_value_in_table(role.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "audit_log_channel", None)
                    await db.update_value_in_table(role.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "audit_logs", False)
                    return
                
                try:
                    entry = list(await role.guild.audit_logs(limit=1).flatten())[0]
                except:
                    return
                
                embed = await db.build_embed(role.guild, title="<a:Information:1247223152367636541> Role Created", description=f"Role {role.mention} has been created by {entry.user.mention}.")
                embed.set_thumbnail(url="")

                permissions_list = [
                    role_permission_names[perm]
                    for perm, value in role.permissions
                    if value and perm in role_permission_names]
                
                permissions = ", ".join(permissions_list) + "." if permissions_list else "None"

                members_with_role = len(role.members)
                role_mentionable = "Yes" if role.mentionable else "No"
                role_hoisted = "Yes" if role.hoist else "No"

                role_position = role.position
                max_roles = len(role.guild.roles) - 1

                role_color = str(role.color).upper()

                embed.add_field(
                    name="**__Main Details__**",
                    value=f"**Name** ➭ {role.mention}\n**ID** ➭ {role.id}\n**Color** ➭ {role_color}\n"
                    + f"**Creation Date** ➭ <t:{int(role.created_at.timestamp())}:D> (<t:{int(role.created_at.timestamp())}:R>)\n"
                    + f"**Role Member Count** ➭ {members_with_role}\n**Mentionable** ➭ {role_mentionable}\n**Hoisted** ➭ {role_hoisted}\n"
                    + f"**Hierarchy Position** ➭ {role_position}/{max_roles}",
                    inline=False)

                role_managed = "Yes" if role.managed else "No"
                role_emoji = str(role.icon) if role.icon else "None"

                role_emoji_formatted = (
                    f"[Click Here]({role_emoji})"
                    if role_emoji != "None" and role_emoji.startswith("http")
                    else role_emoji)

                embed.add_field(
                    name="**__Additional Details__**",
                    value=f"**Managed** ➭ {role_managed}\n**Emoji** ➭ {role_emoji_formatted}\n",
                    inline=False)

                embed.add_field(name="**__Permissions__**", value=permissions, inline=False)
                await logChannel.send(embed=embed)


        if role_counters.get(role.guild.id):
            try:
                channel = role_counters.get(role.guild.id)
                channel = role.guild.get_channel(int(channel))
                if channel is None:
                    # Channel no longer exists; remove from database
                    await db.update_value_in_table(role.guild.id, "ServerConfigurations", "Setting", "Feature", "COUNTERS", "role_counter", None)
                else:
                    name_parts = channel.name.split(":")
                    if len(name_parts) >= 2:
                        text_part = name_parts[0].strip()
                        await channel.edit(name=f"{text_part}: {len(role.guild.roles) if len(role.guild.roles) > 0 else 0}")
            except Exception as e:
                print("[role_counter]: ", e)


    # ON ROLE DELETE
    # --------------
    @commands.Cog.listener("on_guild_role_delete")
    async def on_guild_role_delete(self, role: discord.Role):

        toggles = await db.get_value_from_table(role.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES")
        channels = await db.get_value_from_table(role.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")

        if channels and toggles:
            channels = json.loads(channels)
            toggles = json.loads(toggles)
            audit_log_channel = channels.get("audit_log_channel")
            audit_logs = toggles.get("audit_logs")

            if audit_logs == True:
                logChannel = self.client.get_channel(audit_log_channel)
                if logChannel is None:
                    await db.update_value_in_table(role.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "audit_log_channel", None)
                    await db.update_value_in_table(role.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "audit_logs", False)
                    return
                
                try:
                    entry = list(await role.guild.audit_logs(limit=1).flatten())[0]
                except:
                    return

                embed = await db.build_embed(role.guild, title="<a:Information:1247223152367636541> Role Deleted", description=f"The **{role.name}** role was deleted by {entry.user.mention}.")
                embed.set_thumbnail(url="")
                try:
                    await logChannel.send(embed=embed)
                except discord.Forbidden:
                    await db.update_value_in_table(role.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "audit_log_channel", None)
                    await db.update_value_in_table(role.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "audit_logs", False)
                    return


        if role_counters.get(role.guild.id):
            try:
                channel = role_counters.get(role.guild.id)
                channel = role.guild.get_channel(int(channel))
                if channel is None:
                    await db.update_value_in_table(role.guild.id, "ServerConfigurations", "Setting", "Feature", "COUNTERS", "role_counter", None)
                else:
                    name_parts = channel.name.split(":")
                    if len(name_parts) >= 2:
                        text_part = name_parts[0].strip()
                        await channel.edit(name=f"{text_part}: {len(role.guild.roles) if len(role.guild.roles) > 0 else 0}")
            except Exception as e:
                print("[role_counter]: ", e)


    # ON ROLE UPDATE
    # --------------
    @commands.Cog.listener("on_guild_role_update")
    async def on_guild_role_update(self, before, after):

        toggles = await db.get_value_from_table(before.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES")
        channels = await db.get_value_from_table(before.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")

        if channels and toggles:
            channels = json.loads(channels)
            toggles = json.loads(toggles)
            audit_log_channel = channels.get("audit_log_channel")
            audit_logs = toggles.get("audit_logs")

            if audit_logs:
                logChannel = self.client.get_channel(audit_log_channel)
                if logChannel is None:
                    await db.update_value_in_table(before.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "audit_log_channel", None)
                    await db.update_value_in_table(before.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "audit_logs", False)
                    return
                
                try:
                    entry = list(await before.guild.audit_logs(limit=1).flatten())[0]
                except:
                    return

                if before.name != after.name:
                    embed = await db.build_embed(before.guild, title="<a:Information:1247223152367636541> Role Name Updated", description=f"Name changed for role {after.mention} by {entry.user.mention}.")
                    embed.set_thumbnail(url="")
                    embed.add_field(name="Old Name", value=before.name[:1024], inline=True)
                    embed.add_field(name="New Name", value=after.name[:1024], inline=True)
                    await logChannel.send(embed=embed)

                if before.permissions != after.permissions:

                    emoji_mapping = {
                        True: "<:SwitchOn:1247220822066860073>",
                        False: "<:SwitchOff:1247235832977559592>",
                    }

                    permissions_changed = []

                    for permission, value in before.permissions:
                        if value != getattr(after.permissions, permission):
                            permissions_changed.append(permission)

                    if permissions_changed:
                        entry = list(await after.guild.audit_logs(limit=1).flatten())[0]
                        message = f"Permissions changed for role {after.mention} by {entry.user.mention}."
                        after_permissions = ""

                        for permission in permissions_changed:
                            after_value = emoji_mapping.get(getattr(after.permissions, permission), "")
                            formatted_permission = role_permission_names.get(permission, permission)
                            after_permissions += (f"**{formatted_permission}** ➭ {after_value}\n")

                        embed = await db.build_embed(before.guild, title="<a:Information:1247223152367636541> Role Permissions Updated", description=message)
                        embed.set_thumbnail(url="")
                        embed.add_field(name="Permissions", value=after_permissions[:1024], inline=False)
                        await logChannel.send(embed=embed)

                if before.color != after.color:
                    embed = await db.build_embed(before.guild, title="<a:Information:1247223152367636541> Role Color Updated", description=f"Color changed for role {after.mention} by {entry.user.mention}.")
                    embed.set_thumbnail(url="")
                    embed.add_field(name="Old Color", value=before.color, inline=True)
                    embed.add_field(name="New Color", value=after.color, inline=True)
                    await logChannel.send(embed=embed)

                if before.hoist != after.hoist:
                    embed = await db.build_embed(before.guild, title="<a:Information:1247223152367636541> Role Hoist Updated", description=f"Hoist setting changed for role {after.mention} by {entry.user.mention}.")
                    embed.set_thumbnail(url="")
                    embed.add_field(name="Old Setting", value=before.hoist, inline=True)
                    embed.add_field(name="New Setting", value=after.hoist, inline=True)
                    await logChannel.send(embed=embed)


    # ON INVITE DELETE
    # ----------------
    @commands.Cog.listener("on_invite_delete")
    async def on_invite_delete(self, invite: discord.Invite):
        try:
            del invite_cache[invite.code]
        except:
            pass


    # ON INVITE CREATE
    # ----------------
    @commands.Cog.listener("on_invite_create")
    async def on_invite_create(self, invite: discord.Invite):

        if invite.guild.me.guild_permissions.manage_guild:
            if invite.guild.id in raided:
                return await invite.delete()

            toggles = await db.get_value_from_table(invite.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES")
            channels = await db.get_value_from_table(invite.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")

            if channels and toggles:
                channels = json.loads(channels)
                toggles = json.loads(toggles)
                audit_log_channel = channels.get("audit_log_channel")
                audit_logs = toggles.get("audit_logs")

                if audit_logs:
                    logChannel = self.client.get_channel(audit_log_channel)

                    if logChannel is None:
                        await db.update_value_in_table(invite.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "audit_log_channel", None)
                        await db.update_value_in_table(invite.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "audit_logs", False)
                        return

                    creation_timestamp = int(invite.created_at.timestamp())
                    max_age_timestamp = f"<t:{creation_timestamp + invite.max_age}:d> (<t:{creation_timestamp + invite.max_age}:R>)" if invite.max_age else "Never"
                    max_uses = invite.max_uses if invite.max_uses else "No Limit"
                    invite_cache[invite.code] = invite.uses
                    inviter = invite.inviter
                    if inviter:
                        inviter = inviter
                    else:
                        inviter = None

                    embed = await db.build_embed(invite.guild, title="<a:Information:1247223152367636541> Invite Created", description=f"A new invite has been created by {inviter.mention if inviter else 'Unknown'}.")
                    embed.set_thumbnail(url="")
                    embed.add_field(name="Created By", value=inviter.name if inviter else "Unknown", inline=True)
                    embed.add_field(name="Code", value=invite.code, inline=True)
                    embed.add_field(name="Creation Date", value=f"<t:{creation_timestamp}:d> (<t:{creation_timestamp}:R>)", inline=True)
                    embed.add_field(name="Max Uses", value=str(max_uses), inline=True)
                    embed.add_field(name="Temporary", value=str(invite.temporary), inline=True)
                    embed.add_field(name="Expiration", value=max_age_timestamp, inline=True) 
                    await logChannel.send(embed=embed)

  
    # ON THREAD CREATE
    # ----------------
    @commands.Cog.listener("on_thread_create")
    async def on_thread_create(self, thread: discord.Thread):
        toggles = await db.get_value_from_table(thread.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES")
        channels = await db.get_value_from_table(thread.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")

        if channels and toggles:
            channels = json.loads(channels)
            toggles = json.loads(toggles)
            audit_log_channel = channels.get("audit_log_channel")
            audit_logs = toggles.get("audit_logs")

            if audit_logs:
                logChannel = self.client.get_channel(audit_log_channel)
                if logChannel is None:
                    await db.update_value_in_table(thread.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "audit_log_channel", None)
                    await db.update_value_in_table(thread.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "audit_logs", False)
                    return
                
                try:
                    entry = list(await thread.guild.audit_logs(limit=1).flatten())[0]
                except:
                    return
                
                embed = await db.build_embed(thread.guild, title="<a:Information:1247223152367636541> Thread Created", description=f"A new thread named {thread.mention} has been **created** by {entry.user.mention}.")
                embed.set_thumbnail(url="")
                await logChannel.send(embed=embed)


    # ON THREAD DELETE
    # ----------------
    @commands.Cog.listener("on_thread_delete")
    async def on_thread_delete(self, thread: discord.Thread):
        toggles = await db.get_value_from_table(thread.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES")
        channels = await db.get_value_from_table(thread.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")

        if channels and toggles:
            channels = json.loads(channels)
            toggles = json.loads(toggles)
            audit_log_channel = channels.get("audit_log_channel")
            audit_logs = toggles.get("audit_logs")

            if audit_logs:
                logChannel = self.client.get_channel(audit_log_channel)
                if logChannel is None:
                    await db.update_value_in_table(thread.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "audit_log_channel", None)
                    await db.update_value_in_table(thread.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "audit_logs", False)
                    return
                
                try:
                    entry = list(await thread.guild.audit_logs(limit=1).flatten())[0]
                except:
                    return
                
                embed = await db.build_embed(thread.guild, title="<a:Information:1247223152367636541> Thread Deleted", description=f"The thread named **{thread.name}** has been **deleted** by {entry.user.mention}.")
                embed.set_thumbnail(url="")
                await logChannel.send(embed=embed)

    # ON CHANNEL CREATE
    # -----------------
    @commands.Cog.listener("on_guild_channel_create")
    async def on_guild_channel_create(self, channel: discord.TextChannel):

        toggles = await db.get_value_from_table(channel.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES")
        channels = await db.get_value_from_table(channel.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")

        if channels and toggles:
            channels = json.loads(channels)
            toggles = json.loads(toggles)
            audit_log_channel = channels.get("audit_log_channel")
            audit_logs = toggles.get("audit_logs")

            if audit_logs == True:
                logChannel = self.client.get_channel(audit_log_channel)
                if logChannel is None:
                    await db.update_value_in_table(channel.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "audit_log_channel", None)
                    await db.update_value_in_table(channel.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "audit_logs", False)
                    return

                try:
                    entry = list(await channel.guild.audit_logs(limit=1).flatten())[0]
                except:
                    return
                
                embed = await db.build_embed(channel.guild, title="<a:Information:1247223152367636541> Channel Created", description=f"A new **{channel.type}** channel named {channel.mention} has been **created** by {entry.user.mention}.")
                embed.set_thumbnail(url="")
                await logChannel.send(embed=embed)


            # Resolved Ticket Counter
            if channel.guild.id in resolved_ticket_counters:
                try:
                    try:
                        resolved_ticket_channel = resolved_ticket_counters[channel.guild.id]
                        resolved_ticket_channel = channel.guild.get_channel(int(resolved_ticket_channel))
                    except discord.NotFound:
                        await db.update_value_in_table(channel.guild.id, "ServerConfigurations", "Setting", "Feature", "COUNTERS", "resolved_ticket_counter", None)
                        del resolved_ticket_counters[channel.guild.id]

                    if resolved_ticket_channel is None:
                        await db.update_value_in_table(channel.guild.id, "ServerConfigurations", "Setting", "Feature", "COUNTERS", "active_ticket_counter", None)
                        del resolved_ticket_counters[channel.guild.id]

                    else:
                        stat = await db.get_guild_leaderboard_data(channel.guild, "tickets_resolved")
                        name_parts = resolved_ticket_channel.name.split(":")
                        if len(name_parts) >= 2:
                            text_part = name_parts[0].strip()
                            await resolved_ticket_channel.edit(name=f"{text_part}: {stat}")
                except Exception as e:
                    print(f"[resolved_ticket_counter]: ", e)


            # Active Ticket Counter
            if channel.guild.id in active_ticket_counters:
                try:
                    try:
                        active_ticket_channel = active_ticket_counters[channel.guild.id]
                        active_ticket_channel = channel.guild.get_channel(int(active_ticket_channel))
                    except discord.NotFound:
                        await db.update_value_in_table(channel.guild.id, "ServerConfigurations", "Setting", "Feature", "COUNTERS", "active_ticket_counter", None)
                        del active_ticket_counters[channel.guild.id]

                    if active_ticket_channel is None:
                        await db.update_value_in_table(channel.guild.id, "ServerConfigurations", "Setting", "Feature", "COUNTERS", "active_ticket_counter", None)
                        del active_ticket_counters[channel.guild.id]

                    else:
                        ticket_data = await db.get_value_from_table(channel.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

                        if ticket_data:
                            ticket_data = json.loads(ticket_data)
                            ticket_data = ticket_data.get("ticket_data")
                        
                        open_tickets = ticket_data["open_tickets"]
                        name_parts = active_ticket_channel.name.split(":")
                        if len(name_parts) >= 2:
                            text_part = name_parts[0].strip()
                            await active_ticket_channel.edit(name=f"{text_part}: {len(open_tickets)}")

                except Exception as e:
                    print(f"[active_ticket_counter]: ", e)


    # ON CHANNEL DELETE
    # -----------------
    @commands.Cog.listener("on_guild_channel_delete")
    async def on_guild_channel_delete(self, channel: discord.TextChannel):
        
        toggles = await db.get_value_from_table(channel.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES")
        channels = await db.get_value_from_table(channel.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")

        if channel.id in timed_close_tickets:
            del timed_close_tickets[channel.id]

        if channels and toggles:
            channels = json.loads(channels)
            toggles = json.loads(toggles)
            audit_log_channel = channels.get("audit_log_channel")
            audit_logs = toggles.get("audit_logs")

            if audit_logs == True:
                logChannel = self.client.get_channel(audit_log_channel)
                if logChannel is None:
                    await db.update_value_in_table(channel.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "audit_log_channel", None)
                    await db.update_value_in_table(channel.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "audit_logs", False)
                    return
                
                try:
                    entry = list(await channel.guild.audit_logs(limit=1).flatten())[0]
                except:
                    return
                
                embed = await db.build_embed(channel.guild, title="<a:Information:1247223152367636541> Channel Deleted", description=f"The **{channel.type}** channel named **{channel.name}** has been **deleted** by {entry.user.mention}.")
                embed.set_thumbnail(url="")
                await logChannel.send(embed=embed)


            # Resolved Ticket Counter
            if channel.guild.id in resolved_ticket_counters:
                try:
                    try:
                        resolved_ticket_channel = resolved_ticket_counters[channel.guild.id]
                        resolved_ticket_channel = channel.guild.get_channel(int(resolved_ticket_channel))
                    except discord.NotFound:
                        await db.update_value_in_table(channel.guild.id, "ServerConfigurations", "Setting", "Feature", "COUNTERS", "resolved_ticket_counter", None)
                        del resolved_ticket_counters[channel.guild.id]

                    else:
                        stat = await db.get_guild_leaderboard_data(channel.guild, "tickets_resolved")
                        name_parts = resolved_ticket_channel.name.split(":")
                        if len(name_parts) >= 2:
                            text_part = name_parts[0].strip()
                            await resolved_ticket_channel.edit(name=f"{text_part}: {stat}")
                except Exception as e:
                    print(f"[resolved_ticket_counter]: ", e)


            # Active Ticket Counter
            if channel.guild.id in active_ticket_counters:
                try:
                    try:
                        active_ticket_channel = active_ticket_counters[channel.guild.id]
                        active_ticket_channel = channel.guild.get_channel(int(active_ticket_channel))
                    except discord.NotFound:
                        await db.update_value_in_table(channel.guild.id, "ServerConfigurations", "Setting", "Feature", "COUNTERS", "active_ticket_counter", None)
                        del active_ticket_counters[channel.guild.id]

                    else:
                        ticket_data = await db.get_value_from_table(channel.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

                        if ticket_data:
                            ticket_data = json.loads(ticket_data)
                            ticket_data = ticket_data.get("ticket_data")
                        
                        open_tickets = ticket_data["open_tickets"]
                        name_parts = active_ticket_channel.name.split(":")
                        if len(name_parts) >= 2:
                            text_part = name_parts[0].strip()
                            await active_ticket_channel.edit(name=f"{text_part}: {len(open_tickets)}")

                except Exception as e:
                    print(f"[active_ticket_counter]: ", e)


    # ON CHANNEL UPDATE
    # -----------------
    @commands.Cog.listener("on_guild_channel_update")
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after):

        cooldown_seconds = 1
        current_time = time.time()

        if before.guild.id in self.last_execution_time:
            last_execution = self.last_execution_time[before.guild.id]
            if current_time - last_execution < cooldown_seconds:
                return False

        self.last_execution_time[before.guild.id] = current_time

        toggles = await db.get_value_from_table(before.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES")
        channels = await db.get_value_from_table(before.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")

        if channels and toggles:
            channels = json.loads(channels)
            toggles = json.loads(toggles)
            audit_log_channel = channels.get("audit_log_channel")
            audit_logs = toggles.get("audit_logs")

            if audit_logs and before.guild.me.guild_permissions.view_audit_log:
                logChannel = self.client.get_channel(audit_log_channel)
                if logChannel is None:
                    await db.update_value_in_table(before.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "audit_log_channel", None)
                    await db.update_value_in_table(before.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "audit_logs", False)
                    return

                # Channel name change
                if before.name != after.name:
                    entry = list(await after.guild.audit_logs(limit=1).flatten())[0]
                    embed = await db.build_embed(before.guild, title="<a:Information:1247223152367636541> Channel Renamed", description=f"Name changed for channel {before.mention} by {entry.user.mention}.")
                    embed.set_thumbnail(url="")
                    embed.add_field(name="Before", value=before, inline=True)
                    embed.add_field(name="After", value=after, inline=True)
                    await logChannel.send(embed=embed)

                # Channel type change
                if before.type != after.type:
                    entry = list(await after.guild.audit_logs(limit=1).flatten())[0]
                    embed = await db.build_embed(before.guild, title="<a:Information:1247223152367636541> Channel Type Updated", description=f"Type changed for channel {before.mention} by {entry.user.mention}.")
                    embed.add_field(name="Before", value=before.type, inline=True)
                    embed.add_field(name="After", value=after.type, inline=True)
                    await logChannel.send(embed=embed)

                # Channel topic change (for text channels)
                if isinstance(before, discord.TextChannel) and before.topic != after.topic:
                    if after.topic != "" or after.topic != None:
                        entry = list(await after.guild.audit_logs(limit=1).flatten())[0]
                        embed = await db.build_embed(before.guild, title="<a:Information:1247223152367636541> Channel Topic Updated", description=f"Topic changed for channel {before.mention} by {entry.user.mention}.")
                        embed.add_field(name="Before", value=before.topic, inline=True)
                        embed.add_field(name="After", value=after.topic, inline=True)
                        await logChannel.send(embed=embed)

                # Channel Slowmode Change
                if isinstance(before, discord.TextChannel) and before.slowmode_delay != after.slowmode_delay:
                    entry = list(await after.guild.audit_logs(limit=1).flatten())[0]
                    embed = await db.build_embed(before.guild, title="<a:Information:1247223152367636541> Channel Slowmode Updated", description=f"Slowmode changed for channel {before.mention} by {entry.user.mention}.")
                    embed.add_field(name="Before", value=before.slowmode_delay, inline=True)
                    embed.add_field(name="After", value=after.slowmode_delay, inline=True)
                    await logChannel.send(embed=embed)

                # Channel category change
                if before.category != after.category:
                    if before.category != after.category:
                        if before.category and not after.category:
                            before_category = (before.category.name if before.category else "None")
                            after_category = (after.category.name if after.category else "None")
                            
                            embed = await db.build_embed(before.guild, title="<a:Information:1247223152367636541> Channel Category Change", description=f"Channel {before.mention} had its category changed.")
                            embed.add_field(name="Before", value=before_category, inline=True)
                            embed.add_field(name="After", value=after_category, inline=True)
                            return await logChannel.send(embed=embed)

                    entry = list(await after.guild.audit_logs(limit=1).flatten())[0]
                    before_category = before.category.name if before.category else "None"
                    after_category = after.category.name if after.category else "None"
                    
                    embed = await db.build_embed(before.guild, title="<a:Information:1247223152367636541> Channel Category Updated", description=f"Category changed for channel {before.mention} by {entry.user.mention}.")
                    embed.add_field(name="Before", value=before_category, inline=True)
                    embed.add_field(name="After", value=after_category, inline=True)
                    await logChannel.send(embed=embed)


                permissions_changed = []

                emoji_mapping = {
                    True: "<:SwitchOn:1247220822066860073>",
                    False: "<:SwitchOff:1247235832977559592>",
                    None: "<:SwitchDefault:1247220819298488361>",
                }

                for target, before_overwrite in before.overwrites.items():
                    if target in after.overwrites:
                        after_overwrite = after.overwrites[target]
                        if before_overwrite != after_overwrite:
                            permission_changes = []

                            for permission, value in before_overwrite:
                                if getattr(before_overwrite, permission) != getattr(after_overwrite, permission):
                                    permission_changes.append((permission, value))

                            if permission_changes:
                                permissions_changed.append((target, permission_changes))

                if permissions_changed:
                        
                    try:
                        entry = list(await after.guild.audit_logs(limit=1).flatten())[0]
                    except:
                        return
                    
                    message = f"Permissions changed for channel {after.mention} by {entry.user.mention}."
                    after_permissions = ""

                    for target, changes in permissions_changed:
                        target_info = f"{target.mention}\n"

                        after_info = ""

                        for permission, value in changes:
                            after_value = emoji_mapping.get(getattr(after.overwrites[target], permission), "")
                            formatted_permission = channel_permission_names.get(permission, permission)
                            after_info += f"**{formatted_permission}** ➭ {after_value}\n"

                        after_permissions += f"{after_info}\n"

                    embed = await db.build_embed(before.guild, title="<a:Information:1247223152367636541> Channel Permissions Updated", description=message)
                    embed.set_thumbnail(url="")
                    embed.add_field(name="Target", value=target_info, inline=False)
                    embed.add_field(name="Permissions", value=after_permissions[:1024], inline=False)
                    await logChannel.send(embed=embed)

            # Resolved Ticket Counter
            if before.guild.id in resolved_ticket_counters:
                try:
                    try:
                        resolved_ticket_channel = resolved_ticket_counters[before.guild.id]
                        resolved_ticket_channel = before.guild.get_channel(int(resolved_ticket_channel))
                    except discord.NotFound:
                        await db.update_value_in_table(before.guild.id, "ServerConfigurations", "Setting", "Feature", "COUNTERS", "resolved_ticket_counter", None)
                        del resolved_ticket_counters[before.guild.id]

                    else:
                        stat = await db.get_guild_leaderboard_data(before.guild, "tickets_resolved")
                        name_parts = resolved_ticket_channel.name.split(":")
                        if len(name_parts) >= 2:
                            text_part = name_parts[0].strip()
                            await resolved_ticket_channel.edit(name=f"{text_part}: {stat}")
                except Exception as e:
                    print(f"[resolved_ticket_counter]: ", e)


            # Active Ticket Counter
            if before.guild.id in active_ticket_counters:
                try:
                    try:
                        active_ticket_channel = active_ticket_counters[before.guild.id]
                        active_ticket_channel = before.guild.get_channel(int(active_ticket_channel))
                    except discord.NotFound:
                        await db.update_value_in_table(before.guild.id, "ServerConfigurations", "Setting", "Feature", "COUNTERS", "active_ticket_counter", None)
                        del active_ticket_counters[before.guild.id]

                    else:
                        ticket_data = await db.get_value_from_table(before.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

                        if ticket_data:
                            ticket_data = json.loads(ticket_data)
                            ticket_data = ticket_data.get("ticket_data")
                        
                        open_tickets = ticket_data["open_tickets"]
                        name_parts = active_ticket_channel.name.split(":")
                        if len(name_parts) >= 2:
                            text_part = name_parts[0].strip()
                            await active_ticket_channel.edit(name=f"{text_part}: {len(open_tickets)}")

                except Exception as e:
                    print(f"[active_ticket_counter]: ", e)

# LOAD COG
# --------
def setup(client):
    client.add_cog(listener(client))