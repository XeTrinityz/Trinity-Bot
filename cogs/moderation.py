# Discord Imports
from discord.utils import basic_autocomplete
from discord.ext import commands, pages
from discord import Option
import discord

# Standard / Third-Party Library Imports
from datetime import datetime, timedelta
import json
import re

# Local Module Imports
from utils.database import Database
from utils.functions import Utils
from utils.lists import *
from Bot import is_blocked

db = Database()

class moderation(commands.Cog):
    def __init__(self, client):
        self.client = client

    clearSubCommands = discord.SlashCommandGroup("clear", "Default, Humans, Bots, Invites, Links, Attachments, Member.", default_member_permissions=discord.Permissions(manage_messages=True))
    banSubCommands = discord.SlashCommandGroup("ban", "Member, ID, Remove, Remove All, List.", default_member_permissions=discord.Permissions(ban_members=True))
    warningSubCommands = discord.SlashCommandGroup("warnings", "Add, Remove, Clear, History.", default_member_permissions=discord.Permissions(moderate_members=True))
    lockdownSubCommands = discord.SlashCommandGroup("lockdown", "Category, Channel.", default_member_permissions=discord.Permissions(manage_roles=True))

    @commands.message_command(name="Kick Member", description="Kick a member from the server.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @discord.default_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @commands.has_guild_permissions(moderate_members=True)
    async def kick_user(self, ctx: discord.ApplicationContext, message: discord.Message):

        member = message.author

        invoker_top_role_position = ctx.author.top_role.position
        user_top_role_position = member.top_role.position

        if member == ctx.guild.me:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The bot can not kick itself.")
            return await ctx.respond(embed=embed, ephemeral=True)
        
        elif user_top_role_position >= ctx.guild.me.top_role.position:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The bot can not kick members with the {member.top_role.mention} role.")
            return await ctx.respond(embed=embed, ephemeral=True)

        elif invoker_top_role_position <= user_top_role_position and not ctx.author.guild.owner:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"You can not kick members with the {member.top_role.mention} role.")
            return await ctx.respond(embed=embed, ephemeral=True)

        elif member == ctx.author:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You can not kick yourself.")
            return await ctx.respond(embed=embed, ephemeral=True)
        
        elif member == ctx.guild.owner:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The bot can not kick the server owner.")
            return await ctx.respond(embed=embed, ephemeral=True)
        
        try:
            embed = await db.build_embed(ctx.author.guild, title="{warning_emoji} Server Notice", description=f"You were kicked from {ctx.guild.name}!")
            embed.add_field(name="Reason", value="Kicked via context menu.", inline=False)
            embed.set_footer(text=f"Kicked by {ctx.author.display_name}")
            embed.timestamp = datetime.now()
            await member.send(embed=embed)
        except:
            pass
        
        await member.kick(reason=None)

        embed = await db.build_embed(ctx.author.guild, title="<a:Moderation:1247220777627942974> Member Kicked", description=f"{member.mention} has been kicked.")
        embed.add_field(name="Reason", value="Kicked via context menu.", inline=False)
        await ctx.respond(embed=embed)


    @lockdownSubCommands.command(name="channel", description="Lock or unlock a channel.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    async def lock_channel(self, ctx: discord.ApplicationContext, channel: Option(discord.TextChannel | discord.VoiceChannel, "The channel to lock."), toggle: Option(bool, "Lock or unlock the channel"), reason: Option(str, "The reason for locking/unlocking the channel", default="No Reason Provided.", required=False)):
        
        embed = await db.build_embed(ctx.author.guild, title="<a:loading:1247220769511964673> Locking Channel", description=f"The bot is currently locking {channel.mention}...")
        await ctx.respond(embed=embed)

        if toggle:
            state = "locked"
        else:
            state = "unlocked"

        default_role = ctx.guild.default_role
        if toggle:
            if isinstance(channel, discord.TextChannel):
                perms = channel.overwrites_for(default_role)
                perms.send_messages = False
                await channel.set_permissions(default_role, overwrite=perms, reason=reason)
            elif isinstance(channel, discord.VoiceChannel):
                perms = channel.overwrites_for(default_role)
                perms.connect = False
                await channel.set_permissions(default_role, overwrite=perms, reason=reason)
        else:
            if isinstance(channel, discord.TextChannel):
                perms = channel.overwrites_for(default_role)
                perms.send_messages = None
                await channel.set_permissions(default_role, overwrite=perms, reason=reason)
            elif isinstance(channel, discord.VoiceChannel):
                perms = channel.overwrites_for(default_role)
                perms.connect = None
                await channel.set_permissions(default_role, overwrite=perms, reason=reason)

        embed = await db.build_embed(ctx.author.guild, title=f"<a:Moderation:1247220777627942974> Channel {state.capitalize()}", description=f"{channel.mention} has been **{state}**.")
        if reason != "No Reason Provided.":
            embed.add_field(name="Reason", value=reason, inline=False)
        await ctx.edit(embed=embed)


    @lockdownSubCommands.command(name="category", description="Lock or unlock a category.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    async def lock_category(self, ctx: discord.ApplicationContext, category: Option(discord.CategoryChannel, "The category to lock."), toggle: Option(bool, "Lock or unlock the category"), reason: Option(str, "The reason for locking/unlocking the category", default="No Reason Provided.", required=False)):
        
        embed = await db.build_embed(ctx.author.guild, title="<a:loading:1247220769511964673> Locking Category", description=f"The bot is currently locking **{category.name}**...")
        await ctx.respond(embed=embed)

        if toggle:
            state = "locked"
        else:
            state = "unlocked"

        default_role = ctx.guild.default_role
        if all([channel.permissions_synced for channel in category.channels]):
            if toggle:
                if isinstance(category, discord.CategoryChannel):
                    perms = category.overwrites_for(default_role)
                    perms.send_messages = False
                    await category.set_permissions(default_role, overwrite=perms, reason=reason)
            else:
                if isinstance(category, discord.CategoryChannel):
                    perms = category.overwrites_for(default_role)
                    perms.send_messages = None
                    await category.set_permissions(default_role, overwrite=perms, reason=reason)
        else:
            if toggle:
                for channel in category.channels:
                    if isinstance(channel, discord.TextChannel):
                        perms = channel.overwrites_for(default_role)
                        perms.send_messages = False
                        await channel.set_permissions(default_role, overwrite=perms, reason=reason)
                    elif isinstance(channel, discord.VoiceChannel):
                        perms = channel.overwrites_for(default_role)
                        perms.connect = False
                        await channel.set_permissions(default_role, overwrite=perms, reason=reason)
            else:
                for channel in category.channels:
                    if isinstance(channel, discord.TextChannel):
                        perms = channel.overwrites_for(default_role)
                        perms.send_messages = None
                        await channel.set_permissions(default_role, overwrite=perms, reason=reason)
                    elif isinstance(channel, discord.VoiceChannel):
                        perms = channel.overwrites_for(default_role)
                        perms.connect = None
                        await channel.set_permissions(default_role, overwrite=perms, reason=reason)

        embed = await db.build_embed(ctx.author.guild, title=f"<a:Moderation:1247220777627942974> Category {state.capitalize()}", description=f"**{category.name}** has been **{state}**.")
        if reason != "No Reason Provided.":
            embed.add_field(name="Reason", value=reason, inline=False)
        await ctx.edit(embed=embed)


    @commands.slash_command(name="mute", description="Mute a member in the server.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @discord.default_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def mute(self, ctx: discord.ApplicationContext, 
                   member: Option(discord.Member, "The member to mute."), 
                   duration: Option(str, "The duration of the mute.", choices=["60 Seconds", "5 Minutes", "10 Minutes", "1 Hour", "1 Day", "3 Days", "1 Week", "2 Weeks"]), 
                   reason: Option(str, "The reason for the mute.", default="No Reason Provided.", required=False)):
        
        embed = await db.build_embed(ctx.guild, title="<a:loading:1247220769511964673> Muting Member", description=f"The bot is currently mutting {member.mention}...")
        await ctx.respond(embed=embed)
        
        invoker_top_role_position = ctx.author.top_role.position
        user_top_role_position = member.top_role.position

        if invoker_top_role_position <= user_top_role_position and not ctx.author.guild.owner:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"You can not mute members with the {member.top_role.mention} role.")
            return await ctx.edit(embed=embed)
        
        elif user_top_role_position >= ctx.guild.me.top_role.position:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The bot can not mute members with the {member.top_role.mention} role.")
            return await ctx.edit(embed=embed)
        
        elif member == ctx.guild.me:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The bot can not mute itself.")
            return await ctx.edit(embed=embed)
        
        elif member == ctx.author:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You can not mute yourself.")
            return await ctx.edit(embed=embed)
        
        elif member == member.bot:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You can not mute bots.")
            return await ctx.edit(embed=embed)
        
        elif member == ctx.guild.owner:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The bot can not mute the owner of the server.")
            return await ctx.edit(embed=embed)

        time_intervals = {
            "60 Seconds": 60,
            "5 Minutes": 300,
            "10 Minutes": 600,
            "1 Hour": 3600,
            "1 Day": 86400,
            "3 Days": 86400*3,
            "1 Week": 604800,
            "2 Weeks": 604800*2,
        }

        time_interval = time_intervals.get(duration)

        mute_duration = timedelta(seconds=time_interval)

        await member.timeout_for(mute_duration, reason=reason)

        try:
            embed = await db.build_embed(ctx.author.guild, title=f"{warning_emoji} Server Notice", description=f"You were muted in **{ctx.guild.name}** for **{duration}**.")
            if reason != "No Reason Provided.":
                embed.add_field(name="Reason", value=reason, inline=False)
            embed.timestamp = datetime.now()
            await member.send(embed=embed)
        except:
            pass

        embed = await db.build_embed(ctx.author.guild, title="<a:Mute:1208725651474092082> Member Muted", description=f"{member.mention} has been muted.")
        embed.add_field(name="Duration", value=duration, inline=True)
        if reason != "No Reason Provided.":
            embed.add_field(name="Reason", value=reason, inline=True)
        await ctx.edit(embed=embed)


    @commands.slash_command(name="unmute", description="Unute a member in the server.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @discord.default_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def unmute(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to umute."), reason: Option(str, "The reason for the unmute.", default="No Reason Provided.", required=False)):
        
        await member.remove_timeout(reason=reason)
        embed = await db.build_embed(ctx.author.guild, title="<a:Mute:1208725651474092082> User Unmuted", description=f"{member.mention} has been unmuted.")
        if reason != "No Reason Provided.":
            embed.add_field(name="Reason", value=reason, inline=False)
        await ctx.respond(embed=embed)


    @warningSubCommands.command(name="add", description="Warn a member.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def add_warning(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to warn."), reason: Option(str, "The reason for the warning.")):

        if not member in ctx.guild.members:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="This user is no longer in the server.")
            await ctx.respond(embed=embed, ephemeral=True)
            return 
        
        invoker_top_role_position = ctx.author.top_role.position
        user_top_role_position = member.top_role.position

        if member == ctx.guild.me:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The bot can not warn itself.")
            await ctx.respond(embed=embed, ephemeral=True)
            return 
        
        elif member == ctx.author:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You can not warn yourself.")
            await ctx.respond(embed=embed, ephemeral=True)
            return 
        
        elif user_top_role_position >= ctx.guild.me.top_role.position:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The bot can not warn members with the {member.top_role.mention} role.")
            await ctx.respond(embed=embed, ephemeral=True)
            return 

        elif invoker_top_role_position <= user_top_role_position and not ctx.author.guild.owner:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"You can not warn members with the {member.top_role.mention} role.")
            await ctx.respond(embed=embed, ephemeral=True)
            return 
        
        elif member == ctx.guild.owner:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The bot can not warn the server owner.")
            await ctx.respond(embed=embed, ephemeral=True)
            return 

        else:
            await db.update_warnings_in_table(ctx.guild.id, str(member.id), ctx.author.id, reason)
            embed = await db.build_embed(ctx.author.guild, title=f"{warning_emoji} Member Warned", description=f"{member.mention} has been warned by {ctx.author.mention}.")
            embed.add_field(name="Reason", value=reason, inline=False)
            await ctx.respond(embed=embed)


    @warningSubCommands.command(name="remove", description="Remove a warning entry by its ID.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def remove_warning(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to remove the warning from."), warning: Option(str, "The warning to remove.", autocomplete=basic_autocomplete(Utils.get_member_warnings))):
        
        try:
            warnings = await db.get_warnings_for_user(ctx.guild.id, str(member.id))

            if not warnings:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"{member.mention} has no warnings.")
                return await ctx.respond(embed=embed, ephemeral=True)
            
            id = re.search(r'\d+', warning)
            id = int(id.group())

            warning_to_remove = None
            for warning in warnings:
                if warning["id"] == id:
                    warning_to_remove = warning
                    break

            if warning_to_remove is None:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"No warning found with ID **{warning}** for {member.mention}.")
                return await ctx.respond(embed=embed, ephemeral=True)

            warnings.remove(warning_to_remove)

            await db.remove_warning_in_table(ctx.guild.id, str(member.id), id)

            embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Warning Removed", description=f"Removed warning with ID **{id}** for {member.mention}.")
            await ctx.respond(embed=embed)

        except Exception as e:
            print("[remove_warning]: ", e)


    @warningSubCommands.command(name="clear", description="Clear all warnings from a member.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def remove_all_warnings(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to clear all warnings from.")):
        
        try:
            warnings = await db.get_warnings_for_user(ctx.guild.id, str(member.id))

            if not warnings:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"{member.mention} has no warnings.")
                return await ctx.respond(embed=embed, ephemeral=True)

            await db.remove_all_warnings_in_table(ctx.guild.id, str(member.id))

            embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} All Warnings Cleared", description=f"Cleared all warnings for {member.mention}.")
            await ctx.respond(embed=embed)

        except Exception as e:
            print("[remove_all_warnings]: ", e)


    @warningSubCommands.command(name="history", description="Get the warning history of a member.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def warning_history(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to get the warning history from.")):

        try:
            warnings = await db.get_warnings_for_user(ctx.guild.id, str(member.id))
            max_warnings_per_page = 10

            if warnings:
                warnings = [
                    f"**ID** ➭ {warning['id']}\n**Warned By** ➭ <@{warning['warned_by']}>\n**Reason** ➭ {warning['reason']}\n**Date** ➭ <t:{round(warning['timestamp'])}:d> (<t:{round(warning['timestamp'])}:R>)\n\n" 
                    for warning in warnings]

                if len(warnings) <= max_warnings_per_page:
                    warning_embed = await db.build_embed(ctx.guild, title=f"{warning_emoji} Warning History | {member.display_name}", description="".join(warnings))
                    await ctx.respond(embed=warning_embed)
                
                else:
                    warning_pages = [warnings[i : i + max_warnings_per_page] for i in range(0, len(warnings), max_warnings_per_page)]
                    warning_embeds = []

                    for page_index, page_data in enumerate(warning_pages, start=1):
                        warning_embed = await db.build_embed(ctx.guild, title=f"{warning_emoji} Warning History | {member.display_name}")
                        warning_embed.set_thumbnail(url=ctx.guild.icon.url)

                        description = ""

                        for position, warning in enumerate(page_data, start=(page_index - 1) * max_warnings_per_page + 1):
                            description += warning

                        warning_embed.description = description
                        warning_embeds.append(warning_embed)

                    paginator = pages.Paginator(pages=warning_embeds, disable_on_timeout=True, use_default_buttons=False, show_indicator=True, loop_pages=True, timeout=60)
                    paginator.add_button(pages.PaginatorButton("prev", label="Back", emoji="⬅", style=discord.ButtonStyle.grey))
                    paginator.add_button(pages.PaginatorButton("page_indicator", style=discord.ButtonStyle.gray, disabled=True))
                    paginator.add_button(pages.PaginatorButton("next", label="Forward", emoji="➡", style=discord.ButtonStyle.grey))
                    await paginator.respond(ctx.interaction)
            else:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"{member.mention} has no warnings.")
                await ctx.respond(embed=embed, ephemeral=True)

        except Exception as e:
            print("[warning_history]: ", e)


    @commands.slash_command(name="kick", description="Kick a member from the server.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @discord.default_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def kick(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to kick."), reason: Option(str, "The reason for the kick.", default="No Reason Provided.", required=False)):
        
        invoker_top_role_position = ctx.author.top_role.position
        user_top_role_position = member.top_role.position

        if member == ctx.guild.me:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The bot can not kick itself.")
            return await ctx.respond(embed=embed, ephemeral=True)
        
        elif user_top_role_position >= ctx.guild.me.top_role.position:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The bot can not kick members with the {member.top_role.mention} role.")
            return await ctx.respond(embed=embed, ephemeral=True)

        elif invoker_top_role_position <= user_top_role_position and not ctx.author.guild.owner:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"You can not kick members with the {member.top_role.mention} role.")
            return await ctx.respond(embed=embed, ephemeral=True)

        elif member == ctx.author:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You can not kick yourself.")
            return await ctx.respond(embed=embed, ephemeral=True)
        
        elif member == ctx.guild.owner:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The bot can not kick the server owner.")
            return await ctx.respond(embed=embed, ephemeral=True)
        
        try:
            embed = await db.build_embed(ctx.author.guild, title=f"{warning_emoji} Server Notice", description=f"You were kicked from **{ctx.guild.name}**.")
            if reason != "No Reason Provided.":
                embed.add_field(name="Reason", value=reason, inline=False)
            embed.timestamp = datetime.now()
            await member.send(embed=embed)
        except:
            pass
        
        await member.kick(reason=reason)

        embed = await db.build_embed(ctx.author.guild, title="<a:Moderation:1247220777627942974> Member Kicked", description=f"{member.mention} has been kicked.")
        if reason != "No Reason Provided.":
            embed.add_field(name="Reason", value=reason, inline=False)
        await ctx.respond(embed=embed)


    @banSubCommands.command(name="id", description="Ban a user by their id.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    async def id(self, ctx: discord.ApplicationContext, id: Option(str, "The id of the user to ban."), 
                 clear_messages: Option(str, "How much of their recent message history to delete.", 
                                        choices=["None", "Previous Hour", "Previous 6 Hours", "Previous 12 Hours", "Previous 24 Hours", "Previous 3 Days", "Previous 7 Days"], default="None", required=False), 
                reason: Option(str, "The reason for the ban.", default="No Reason Provided.", required=False)):

        try:
            user = await self.client.get_or_fetch_user(int(id))
        except:
            embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="The user id you provided is invalid.")
            await ctx.respond(embed=embed, ephemeral=True)
            return 

        if ctx.guild.me.id == user.id:
            embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description=f"The bot can not ban itself.")
            await ctx.respond(embed=embed, ephemeral=True)
            return 

        ban_list = ctx.guild.bans()
        ban_list_data = []

        async for banned in ban_list:
            ban_list_data.append(banned.user.id)
        
        if user.id in ban_list_data:
            embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="The user id you provided is already banned.")
            await ctx.respond(embed=embed, ephemeral=True)
            return 

        embed = await db.build_embed(ctx.guild, title="<a:loading:1247220769511964673> Banning User", description=f"The bot is currently banning {user.mention}...")
        await ctx.respond(embed=embed)

        if user in ctx.guild.members:
            member = ctx.guild.get_member(user.id)
            invoker_top_role_position = ctx.author.top_role.position
            user_top_role_position = member.top_role.position

            if member == ctx.guild.me:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The bot can not ban itself.")
                await ctx.respond(embed=embed, ephemeral=True)
                return 
            
            elif user_top_role_position >= ctx.guild.me.top_role.position:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The bot can not ban members with the {member.top_role.mention} role.")
                await ctx.respond(embed=embed, ephemeral=True)
                return 

            elif invoker_top_role_position <= user_top_role_position and not ctx.author.guild.owner:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"You can not ban members with the {member.top_role.mention} role.")
                await ctx.respond(embed=embed, ephemeral=True)
                return 

            elif member == ctx.author:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You can not ban yourself.")
                await ctx.respond(embed=embed, ephemeral=True)
                return 
            
            elif member == ctx.guild.owner:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The bot can not ban the server owner.")
                await ctx.respond(embed=embed, ephemeral=True)
                return 

            try:
                embed = await db.build_embed(ctx.guild, title=f"{warning_emoji} Server Notice", description=f"You were banned from **{ctx.guild.name}**.")
                if reason != "No Reason Provided.":
                    embed.add_field(name="Reason", value=reason, inline=False)
                embed.timestamp = datetime.now()
                await user.send(embed=embed)
            except:
                pass

        time_intervals = {
            "None": None,
            "Previous Hour": 3600,
            "Previous 6 Hours": 21600,
            "Previous 12 Hours": 43200,
            "Previous 24 Hours": 86400,
            "Previous 3 Days": 259200,
            "Previous 7 Days": 604800
        }

        time_interval = time_intervals.get(clear_messages, None)
        await ctx.guild.ban(user, delete_message_seconds=time_interval, reason=reason + f"\n(Banned By {ctx.author.display_name})")

        embed = await db.build_embed(ctx.guild, title="<a:Moderation:1247220777627942974> Member Banned", description=f"{user.mention} (``{user.id}``) has been banned.")
        embed.add_field(name="Reason", value=reason + f"\n(``Banned By {ctx.author.display_name}``)", inline=False)
        await ctx.edit(embed=embed)

        channels = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")

        if channels:
            channels = json.loads(channels)
            moderation_log_channel = channels.get("moderation_log_channel")

            if moderation_log_channel:
                channel = discord.utils.get(ctx.guild.channels, id=moderation_log_channel)
                
                if channel is None:
                    await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "moderation_log_channel", None)
                    return
                
                embed = await db.build_embed(ctx.guild, title="<a:Moderation:1247220777627942974> Member Banned", description=f"{user.mention} (``{user.id}``) has been banned.")
                embed.set_thumbnail(url="")
                embed.add_field(name="Reason", value=reason + f"\n(``Banned By {ctx.author.display_name}``)", inline=False)
                await channel.send(embed=embed)


    @banSubCommands.command(name="member", description="Ban a member from the server.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    async def member(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to ban."), 
                     clear_messages: Option(str, "How much of their recent message history to delete.", 
                                            choices=["None", "Previous Hour", "Previous 6 Hours", "Previous 12 Hours", "Previous 24 Hours", "Previous 3 Days", "Previous 7 Days"], default="None", required=False), 
                    reason: Option(str, "The reason for the ban.", default="No Reason Provided.", required=False)):
        
        if member == ctx.guild.me:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The bot can not ban itself.")
            return await ctx.respond(embed=embed, ephemeral=True)
        
        invoker_top_role_position = ctx.author.top_role.position
        user_top_role_position = member.top_role.position

        if member == ctx.guild.me:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The bot can not ban itself.")
            return await ctx.respond(embed=embed, ephemeral=True)
        
        elif user_top_role_position >= ctx.guild.me.top_role.position:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The bot can not ban members with the {member.top_role.mention} role.")
            return await ctx.respond(embed=embed, ephemeral=True)

        elif invoker_top_role_position <= user_top_role_position and not ctx.author.guild.owner:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"You can not ban members with the {member.top_role.mention} role.")
            return await ctx.respond(embed=embed, ephemeral=True)

        elif member == ctx.author:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You can not ban yourself.")
            return await ctx.respond(embed=embed, ephemeral=True)
        
        elif member == ctx.guild.owner:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The bot can not ban the server owner.")
            return await ctx.respond(embed=embed, ephemeral=True)
        
        embed = await db.build_embed(ctx.author.guild, title="<a:loading:1247220769511964673> Banning Member", description=f"The bot is currently banning {member.mention}...")
        await ctx.respond(embed=embed)
        
        try:
            embed = await db.build_embed(ctx.author.guild, title=f"{warning_emoji} Server Notice", description=f"You were banned from **{ctx.guild.name}**.")
            if reason != "No Reason Provided.":
                embed.add_field(name="Reason", value=reason, inline=False)
            embed.timestamp = datetime.now()
            await member.send(embed=embed)
        except:
            pass
        
        time_intervals = {
            "None": None,
            "Previous Hour": 3600,
            "Previous 6 Hours": 21600,
            "Previous 12 Hours": 43200,
            "Previous 24 Hours": 86400,
            "Previous 3 Days": 259200,
            "Previous 7 Days": 604800
        }
        
        time_interval = time_intervals.get(clear_messages, None)
        await member.ban(delete_message_seconds=time_interval, reason=reason + f"\n(Banned By {ctx.author.display_name})")

        embed = await db.build_embed(ctx.author.guild, title="<a:Moderation:1247220777627942974> Member Banned", description=f"{member.mention} (``{member.id}``) has been banned.")
        embed.add_field(name="Reason", value=reason + f"\n(``Banned By {ctx.author.display_name}``)", inline=False)
        await ctx.edit(embed=embed)

        channels = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")

        if channels:
            channels = json.loads(channels)
            moderation_log_channel = channels.get("moderation_log_channel")

            if moderation_log_channel:
                channel = discord.utils.get(ctx.guild.channels, id=moderation_log_channel)
                
                if channel is None:
                    await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "moderation_log_channel", None)
                    return
                
                embed = await db.build_embed(ctx.guild, title="<a:Moderation:1247220777627942974> Member Banned", description=f"{member.mention} (``{member.id}``) has been banned.")
                embed.set_thumbnail(url="")
                embed.add_field(name="Reason", value=reason + f"\n(``Banned By {ctx.author.display_name}``)", inline=False)
                await channel.send(embed=embed)


    @banSubCommands.command(name="remove", description="Remove a ban from a user.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: discord.ApplicationContext, user: Option(str, "The user to remove the ban from.", autocomplete=basic_autocomplete(Utils.get_banned_users)), 
                    reason: Option(str, "The reason for the ban being removed.", default="No Reason Provided.", required=False)):
        
        await ctx.defer()
        guild = self.client.get_guild(ctx.guild.id)
        opening_parenthesis = user.find("(")
        closing_parenthesis = user.find(")")

        if opening_parenthesis != -1 and closing_parenthesis != -1:
            user_name = user[:opening_parenthesis].strip()
            extracted_value = int(user[opening_parenthesis + 1 : closing_parenthesis])
        
        userid = int(extracted_value)

        checkUser = await self.client.get_or_fetch_user(userid)

        await guild.unban(discord.Object(id=userid), reason=reason + f"\n(Removed By {ctx.author.display_name})")
        embed = await db.build_embed(ctx.author.guild, title="<a:Moderation:1247220777627942974> Ban Removed", description=f"{checkUser.mention} (``{checkUser.id}``) has had their ban removed.")
        embed.add_field(name="Reason", value=reason + f"\n(``Removed By {ctx.author.display_name}``)", inline=False)
        await ctx.respond(embed=embed)

        channels = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")

        if channels:
            channels = json.loads(channels)
            moderation_log_channel = channels.get("moderation_log_channel")

            if moderation_log_channel:
                channel = discord.utils.get(ctx.guild.channels, id=moderation_log_channel)
                
                if channel is None:
                    await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "moderation_log_channel", None)
                    return
                
                embed = await db.build_embed(ctx.guild, title="<a:Moderation:1247220777627942974> Ban Removed", description=f"{checkUser.mention} (``{checkUser.id}``) has had their ban removed.")
                embed.set_thumbnail(url="")
                embed.add_field(name="Reason", value=reason + f"\n(``Removed By {ctx.author.display_name}``)", inline=False)
                await channel.send(embed=embed)


    @banSubCommands.command(name="remove-all", description="Remove all bans from the server.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @discord.default_permissions(administrator=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def unban_all(self, ctx: discord.ApplicationContext):
        
        await ctx.defer()
        guild = self.client.get_guild(ctx.guild.id)

        embed = await db.build_embed(ctx.author.guild, title="<a:Loading:1247220769511964673> Removing All Bans", description="The bot is currently removing all bans from the server...")
        await ctx.respond(embed=embed)

        try:
            count = 0
            ban_list = ctx.guild.bans()
            ban_list_data = []

            async for banned in ban_list:
                ban_list_data.append(banned)

            for banned in ban_list_data:
                await guild.unban(discord.Object(id=banned.user.id), reason=f"Remove All Bans\n(``Removed By {ctx.author.display_name}``)")
                count += 1

            embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} All Bans Removed", description=f"The bot has removed the ban from a total of **{count}** users.")
            await ctx.edit(embed=embed)
        except Exception as e:
            print("[remove_all]: ", e)


    @banSubCommands.command(name="list", description="List all banned users.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def list(self, ctx: discord.ApplicationContext):
        
        ban_list = ctx.guild.bans()
        ban_list_data = []

        async for banned in ban_list:
            ban_list_data.append(banned)

        if not ban_list_data:
            embed = await db.build_embed(ctx.author.guild, title=f"<a:Banned:1209256463743328316> Banned Users | {ctx.author.guild.name}", description="This server has no banned users.")
            return await ctx.respond(embed=embed)

        max_users_per_page = 5

        if len(ban_list_data) <= max_users_per_page:
            
            desc = ""
            for banned in ban_list_data:
                desc += f"**{banned.user.name}**\n**ID** ➭ `{banned.user.id}`\n**Reason** ➭ `{banned.reason}`\n\n"
            
            embed = await db.build_embed(ctx.author.guild, title=f"<a:Banned:1209256463743328316> Banned Users | {ctx.author.guild.name}", description=desc)
            return await ctx.respond(embed=embed)

        ban_pages = [
            ban_list_data[i : i + max_users_per_page]
            for i in range(0, len(ban_list_data), max_users_per_page)]

        if not ban_pages:
            embed = await db.build_embed(ctx.author.guild, title=f"<a:Banned:1209256463743328316> Banned Users | {ctx.author.guild.name}", description="This server has no banned users.")
            return await ctx.respond(embed=embed)

        embed_pages = []
        for page in ban_pages:
            desc = "" 
            for banned in page:
                desc += f"**{banned.user.name}**\n**ID** ➭ `{banned.user.id}`\n**Reason** ➭ `{banned.reason}`\n\n"
            
            ban_page = await db.build_embed(ctx.author.guild, title=f"<a:Banned:1209256463743328316> Banned Users | {ctx.author.guild.name}", description=desc)
            embed_pages.append(ban_page)

        paginator = pages.Paginator(pages=embed_pages, disable_on_timeout=True, use_default_buttons=False, show_indicator=True, loop_pages=True, timeout=60)
        if len(embed_pages) > 10:
            paginator.add_button(pages.PaginatorButton("first", label="", emoji="<a:First:1182373753498370069>", style=discord.ButtonStyle.grey))
        paginator.add_button(pages.PaginatorButton("prev", label="", emoji="<a:LeftArrow:1156039371624026112>", style=discord.ButtonStyle.grey))
        paginator.add_button(pages.PaginatorButton("page_indicator", style=discord.ButtonStyle.gray, disabled=True))
        paginator.add_button(pages.PaginatorButton("next", label="", emoji="<a:RightArrow:1156039369875001385>", style=discord.ButtonStyle.grey))
        if len(embed_pages) > 10:
            paginator.add_button(pages.PaginatorButton("last", label="", emoji="<a:Last:1182374111306063902>", style=discord.ButtonStyle.grey))
        await paginator.respond(ctx.interaction)


    @commands.slash_command(name="snipe", description="Get the last deleted message from the channel.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @discord.default_permissions(manage_messages=True)
    @commands.has_guild_permissions(manage_messages=True)
    async def snipe_message(self, ctx: discord.ApplicationContext):
        
        try:
            message = sniped[ctx.channel.id]["message"]
            author = sniped[ctx.channel.id]["author"]

            embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} {author}'s Deleted Message", description=message)
            await ctx.respond(embed=embed)
        except:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="There are no deleted messages to snipe from this channel.")
            return await ctx.respond(embed=embed, ephemeral=True)


    @clearSubCommands.command(name="messages", description="Clear a specified amount of messages.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_permissions(manage_messages=True)
    @commands.cooldown(2, 20, commands.BucketType.channel)
    async def clsdefault(self, ctx: discord.ApplicationContext, check: Option(str, "Delete messages based on author/message content.", choices=["All", "Member", "Bots", "Humans", "Attachments", "Links", "Invites"]),
                        amount: Option(int, "The amount of messages to clear.", min_value=1, max_value=500), member: Option(discord.Member, "The member to filter the messages from.", required=False)):
        
        embed = await db.build_embed(ctx.author.guild, title="<a:Loading:1247220769511964673> Deleting Messages", description=f"The bot is attempting to delete **{amount}** {'messages.' if amount > 1 else 'message.'}")
        await ctx.respond(embed=embed, ephemeral=True)
        
        if check == "All":
            deleted = await ctx.channel.purge(limit=amount)
            embed = await db.build_embed(ctx.author.guild, title="🗑 Messages Deleted", description=f"Deleted **{len(deleted)}/{amount}** messages.")
            await ctx.edit(embed=embed)

        elif check == "Member":
            if member is None:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You need to specify the member.")
                return await ctx.edit(embed=embed)

            def userCheck(m):
                return m.author.id == member.id
            
            deleted = await ctx.channel.purge(limit=amount, check=userCheck)
            embed = await db.build_embed(ctx.author.guild, title="🗑 Messages Deleted", description=f"Deleted **{len(deleted)}/{amount}** messages.")
            await ctx.edit(embed=embed)

        elif check == "Bots":
            def botCheck(m):
                return m.author.bot
            
            deleted = await ctx.channel.purge(limit=amount, check=botCheck)
            embed = await db.build_embed(ctx.author.guild, title="🗑 Messages Deleted", description=f"Deleted **{len(deleted)}/{amount}** messages.")
            await ctx.edit(embed=embed)
        
        elif check == "Humans":
            def humanCheck(m):
                return not m.author.bot

            deleted = await ctx.channel.purge(limit=amount, check=humanCheck)
            embed = await db.build_embed( ctx.author.guild, title="🗑 Messages Deleted", description=f"Deleted **{len(deleted)}/{amount}** messages.")
            await ctx.edit(embed=embed)
        
        elif check == "Attachments":
            def attachmentCheck(m):
                return m.attachments

            deleted = await ctx.channel.purge(limit=amount, check=attachmentCheck)
            embed = await db.build_embed(ctx.author.guild, title="🗑 Messages Deleted", description=f"Deleted **{len(deleted)}/{amount}** messages.")
            await ctx.edit(embed=embed)

        elif check == "Links":
            def linkCheck(m):
                return "https://" in m.content or "http://" in m.content

            deleted = await ctx.channel.purge(limit=amount, check=linkCheck)
            embed = await db.build_embed(ctx.author.guild, title="🗑 Messages Deleted", description=f"Deleted **{len(deleted)}/{amount}** messages.")
            await ctx.edit(embed=embed)

        elif check == "Invites":
            def inviteCheck(m):
                invite_pattern = (r"(https?://)?(discord\.gg\/|discord\.com\/invite\/)([a-zA-Z0-9]+)")
                return re.search(invite_pattern, m.content)

            deleted = await ctx.channel.purge(limit=amount, check=inviteCheck)
            embed = await db.build_embed(ctx.author.guild, title="🗑 Messages Deleted", description=f"Deleted **{len(deleted)}/{amount}** messages.")
            await ctx.edit(embed=embed)


    @commands.slash_command(name="nuke", description="Nukes a channel.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @discord.default_permissions(administrator=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def nuke(self, ctx: discord.ApplicationContext, channel: Option(discord.TextChannel, "The channel to nuke."), reason: Option(str, "The reason for the nuke.", default="No Reason Provided.", required=False)):
        
        embed = await db.build_embed(ctx.author.guild, title="<a:Nuke:1247220783730655252> Nuking Channel", description=f"Nuking {channel.mention}...")
        await ctx.respond(embed=embed, ephemeral=True)

        position = channel.position
        new_channel = await channel.clone()
        await channel.delete(reason=reason + f"\n(Nuked by: {ctx.author.display_name})")
        embed = await db.build_embed(ctx.author.guild, title="<a:Nuke:1247220783730655252> Channel Nuked", description=f"{new_channel.mention} has been nuked!")
        if ctx.channel != channel:
            await ctx.edit(embed=embed)

        embed = await db.build_embed(ctx.author.guild, title="<a:Nuke:1247220783730655252> Channel Nuked")
        embed.set_image(url="https://media.tenor.com/2L8cGGO6_MIAAAAd/operation-teapot-nuke.gif")
        await new_channel.send(embed=embed)
        await new_channel.edit(position=position)

        channels = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")

        if channels:
            channels = json.loads(channels)
            moderation_log_channel = channels.get("moderation_log_channel")

            if moderation_log_channel:
                logChannel = discord.utils.get(ctx.guild.channels, id=moderation_log_channel)

                if logChannel is None:
                    await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "audit_log_channel", None)
                    await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "audit_logs", False)
                    return
                
                embed = await db.build_embed(ctx.guild, title="<a:Moderation:1247220777627942974> Channel Nuked", description=f"{ctx.author.mention} nuked {new_channel.mention}.")
                if reason != "No Reason Provided.":
                    embed.add_field(name="Reason", value=reason, inline=False)
                await logChannel.send(embed=embed)


    @commands.slash_command(name="sanitize", description="Sanitize a members name.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @discord.default_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def sanitize(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to sanitize.")):
        
        name = member.nick if member.nick else member.global_name
        #sanitized_name = re.sub(r'^[^\w]+', '', name)
        sanitized_name = re.sub(r'^[^a-zA-Z0-9_]+', '', name)
        if not sanitized_name.strip():
            sanitized_name = "John Doe"

        try:
            await member.edit(nick=sanitized_name)
            embed = await db.build_embed(ctx.author.guild, title="<a:Moderation:1247220777627942974> Member Sanitized", description=f"Any symbols placed before {member.mention}'s name were removed.")
            await ctx.respond(embed=embed)
        except discord.errors.Forbidden:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The bot can not sanitize this member.")
            return await ctx.respond(embed=embed, ephemeral=True)
        

def setup(client):
    client.add_cog(moderation(client))