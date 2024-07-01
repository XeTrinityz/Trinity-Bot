# Discord Imports
from discord.ext import commands
from discord import Option
import discord

# Standard / Third-Party Library Imports
from datetime import datetime
import asyncio
import re

# Local Module Imports
from utils.database import Database
from utils.views import RoleMembers
from EmbedBuilder import embedTool
from utils.lists import role_permission_names
from Bot import is_blocked
from utils.lists import *

db = Database()

class roles(commands.Cog):
    def __init__(self, client):
        self.client = client

    roleSubCommands = discord.SlashCommandGroup("role", "Add Member, Add All, Remove Member, Remove All.", default_member_permissions=discord.Permissions(manage_roles=True))
    selfroleSubCommands = discord.SlashCommandGroup("selfroles", "Setup, Add, Remove.", default_member_permissions=discord.Permissions(manage_roles=True))
    roleaddSubCommands = roleSubCommands.create_subgroup("add", "Add")
    roleremoveSubCommands = roleSubCommands.create_subgroup("remove", "Remove")

    @commands.slash_command(name="roleinfo", description="Shows detailed information about a role.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def roleinfo(self, ctx: discord.ApplicationContext, role: Option(discord.Role, "The role to retreive the info from.")):

        try:
            embed = await db.build_embed(ctx.author.guild, title="<a:Loading:1247220769511964673> Retrieving Information", description=f"Retrieving information on the {role.mention} role...")
            await ctx.respond(embed=embed)

            permissions_list = [
                role_permission_names[perm]
                for perm, value in role.permissions
                if value and perm in role_permission_names
            ]

            permissions = ", ".join(permissions_list) + "." if permissions_list else "None"
            members_with_role = len(role.members)
            role_mentionable = "Yes" if role.mentionable else "No"
            role_hoisted = "Yes" if role.hoist else "No"

            role_position = role.position
            max_roles = len(ctx.author.guild.roles) - 1

            role_color = str(role.color).upper()

            embed = discord.Embed(title=f"<a:Folder:1247220756547502160> Role Information | {role.name}", color=role.color)
            
            role_managed = "Yes" if role.managed else "No"

            embed.add_field(
                name="**__Main Details__**",
                value=f"**Name** ➭ {role.mention}\n**ID** ➭ {role.id}\n**Color** ➭ {role_color}\n"
                + f"**Creation Date** ➭ <t:{int(role.created_at.timestamp())}:D> (<t:{int(role.created_at.timestamp())}:R>)\n"
                + f"**Role Member Count** ➭ {members_with_role}\n**Mentionable** ➭ {role_mentionable}\n**Hoisted** ➭ {role_hoisted}\n"
                + f"**Hierarchy Position** ➭ {role_position}/{max_roles}\n"
                + f"**Managed** ➭ {role_managed}",
                inline=False)

            role_emoji = str(role.icon) if role.icon else "None"

            if role_emoji != "None":
                embed.set_thumbnail(url=role_emoji)

            embed.add_field(name="**__Permissions__**", value=permissions, inline=False)
            await ctx.edit(embed=embed, view=RoleMembers(role))
        except Exception as e:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"There was an error getting information on this role.")
            await ctx.edit(embed=embed)


    @roleaddSubCommands.command(name="member", description="Add a role to a member.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def add_role(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to give the role to.", required=True), role: Option(discord.Role, "The role to give to the member.", required=True)):
        
        invoker_top_role_position = ctx.author.top_role.position
        user_top_role_position = member.top_role.position

        if member == ctx.guild.owner:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The bot is unable to modify the roles of the server owner.")
            return await ctx.respond(embed=embed, ephemeral=True)
    
        elif invoker_top_role_position <= user_top_role_position and not ctx.author.guild.owner:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"You can not alter the roles of a member with the {member.top_role.mention} role.")
            return await ctx.respond(embed=embed, ephemeral=True)

        elif role.position >= ctx.guild.me.top_role.position:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The bot can not give members the {role.mention} role.")
            return await ctx.respond(embed=embed, ephemeral=True)
        
        elif invoker_top_role_position <= role.position and not ctx.author.guild.owner:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"You can not give members the {role.mention} role.")
            return await ctx.respond(embed=embed, ephemeral=True)
        
        elif role in member.roles:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"{member.mention} already has the {role.mention} role.")
            return await ctx.respond(embed=embed, ephemeral=True)
        else:
            await member.add_roles(role)
            embed = await db.build_embed(ctx.author.guild, title="<a:Moderation:1247220777627942974> Role Added", description=f"{member.mention} has received the {role.mention} role.")
            await ctx.respond(embed=embed)


    @roleremoveSubCommands.command(name="member", description="Remove a role from a member.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def remove_role(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to remove the role from.", required=True), role: Option(discord.Role, "The role to remove from the member.", required=True)):
        
        invoker_top_role_position = ctx.author.top_role.position
        user_top_role_position = member.top_role.position

        if member == ctx.guild.owner:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The bot is unable to modify the roles of the server owner.")
            return await ctx.respond(embed=embed, ephemeral=True)
    
        elif invoker_top_role_position <= user_top_role_position and not ctx.author.guild.owner:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"You can not alter the roles of a member with the {member.top_role.mention} role.")
            return await ctx.respond(embed=embed, ephemeral=True)
        
        elif role.position >= ctx.guild.me.top_role.position:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The bot can not remove the {role.mention} role from members.")
            return await ctx.respond(embed=embed, ephemeral=True)
        
        elif invoker_top_role_position <= role.position and not ctx.author.guild.owner:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"You can not remove roles from members the {role.mention} role.")
            return await ctx.respond(embed=embed, ephemeral=True)
        
        elif role not in member.roles:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"{member.mention} does not have the {role.mention} role.")
            return await ctx.respond(embed=embed, ephemeral=True)
        else:
            await member.remove_roles(role)
            embed = await db.build_embed(ctx.author.guild, title="<a:Moderation:1247220777627942974> Role Removed", description=f"{member.mention} has been removed from the {role.mention} role.")
            await ctx.respond(embed=embed)


    @roleaddSubCommands.command(name="all", description="Adds the specified role to all members who do not have it.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @discord.default_permissions(administrator=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def addroleall(self, ctx: discord.ApplicationContext, role: Option(discord.Role, "The role to give to all members.")):
        
        try:
            bot_top_role = ctx.guild.me.top_role.position
            role_position = role.position

            if bot_top_role < role_position:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Please make sure the bots role is above the selected role.")
                return await ctx.respond(embed=embed, ephemeral=True)
            
            addedUsers = 0
            failed = 0
            logs = []
            timestamp = datetime.now()
            currentMember = None

            await ctx.respond("Starting...")

            async def add_role_to_member(member, role):
                try:
                    await member.add_roles(role)
                    return True
                except discord.Forbidden:
                    return False

            members_without_role = [member for member in ctx.guild.members if role not in member.roles]

            for member in members_without_role:
                if member.bot or member.id == ctx.author.id:
                    continue

                currentMember = member.mention
                if await add_role_to_member(member, role):
                    addedUsers += 1
                else:
                    failed += 1

                logs.append(f"+ {member.display_name} | {role.name} Role Added")

                if len(logs) > 15:
                    logs.pop(0)

                embed = await db.build_embed(
                    ctx.author.guild,
                    title=f"**{success_emoji} Add Role To All Members**",
                    description=f"**Role: {role.mention}**\n\n"
                                + f"**Total Members:** {len(members_without_role)}\n"
                                + f"**Successfully Added:** {addedUsers}\n"
                                + f"**Failed:** {failed}\n\n"
                                + f"**Current Member:** {currentMember}\n\n"
                                + "**Status:** Active"
                )
                embed.add_field(name="**📋 Console**", value="```diff\n" + "\n".join(map(str, logs)) + "```", inline=False)
                embed.set_thumbnail(url="")
                embed.set_footer(text="Started")
                embed.timestamp = timestamp

                await ctx.edit(content="", embed=embed)
                await asyncio.sleep(1)

                if addedUsers + failed >= 500:
                    logs.append("\n====== [ LIMIT REACHED ] =======")
                    break

            logs.append("\n================= [ END ] =================")
            embed = await db.build_embed(
                ctx.author.guild,
                title=f"**{success_emoji} Add Role To All Members**",
                description=f"**Role: {role.mention}**\n\n"
                            + f"**Total Members:** {len(members_without_role)}\n"
                            + f"**Successfully Added:** {addedUsers}\n"
                            + f"**Failed:** {failed}\n\n"
                            + "**Status:** Complete"
            )
            embed.add_field(name="**📋 Console**", value="```diff\n" + "\n".join(map(str, logs)) + "```", inline=False)
            embed.set_thumbnail(url="")
            embed.set_footer(text="Complete")
            embed.timestamp = datetime.now()

            await ctx.edit(content="", embed=embed)

        except Exception as e:
            print("[addroleall]: ", e)


    @roleremoveSubCommands.command(name="all", description="Removes the specified role from all members who have it.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @discord.default_permissions(administrator=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def remove_role_all(self, ctx: discord.ApplicationContext, role: Option(discord.Role, "The role to remove from all members.")):
        try:

            bot_top_role = ctx.guild.me.top_role.position
            role_position = role.position

            if bot_top_role < role_position:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Please make sure the bots role is above the selected role.")
                return await ctx.respond(embed=embed, ephemeral=True)
            
            removedUsers = 0
            failed = 0
            logs = []
            timestamp = datetime.now()
            currentMember = None

            await ctx.respond("Starting...")

            async def remove_role_from_member(member, role):
                try:
                    await member.remove_roles(role)
                    return True
                except discord.Forbidden:
                    return False

            members_with_role = [member for member in ctx.guild.members if role in member.roles]

            for member in members_with_role:
                if member.bot or member.id == ctx.author.id:
                    continue

                currentMember = member.mention
                if await remove_role_from_member(member, role):
                    removedUsers += 1
                else:
                    failed += 1

                logs.append(f"+ {member.display_name} | {role.name} Role Removed")

                if len(logs) > 15:
                    logs.pop(0)

                embed = await db.build_embed(
                    ctx.author.guild,
                    title=f"**{success_emoji} Remove Role From All Members**",
                    description=f"**Role: {role.mention}**\n\n"
                                + f"**Total Members:** {len(members_with_role)}\n"
                                + f"**Successfully Removed:** {removedUsers}\n"
                                + f"**Failed:** {failed}\n\n"
                                + f"**Current Member:** {currentMember}\n\n"
                                + "**Status:** Active"
                )
                embed.add_field(name="**📋 Console**", value="```diff\n" + "\n".join(map(str, logs)) + "```", inline=False)
                embed.set_thumbnail(url="")
                embed.set_footer(text="Started")
                embed.timestamp = timestamp

                try:
                    await ctx.edit(content="", embed=embed)
                except:
                    break
                await asyncio.sleep(1)

                if removedUsers + failed >= 500:
                    logs.append("\n====== [ LIMIT REACHED ] =======")
                    break

            logs.append("\n================= [ END ] =================")
            embed = await db.build_embed(
                ctx.author.guild,
                title=f"**{success_emoji} Remove Role From All Members**",
                description=f"**Role: {role.mention}**\n\n"
                            + f"**Total Members:** {len(members_with_role)}\n"
                            + f"**Successfully Removed:** {removedUsers}\n"
                            + f"**Failed:** {failed}\n\n"
                            + "**Status:** Complete"
            )
            embed.add_field(name="**📋 Console**", value="```diff\n" + "\n".join(map(str, logs)) + "```", inline=False)
            embed.set_thumbnail(url="")
            embed.set_footer(text="Complete")
            embed.timestamp = datetime.now()

            await ctx.edit(content="", embed=embed)

        except Exception as e:
            print("[remove_role_all]: ", e)


    @selfroleSubCommands.command(name="setup", description="Setup the self-role dropdown menu.")
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    async def self_menu(self, ctx: discord.ApplicationContext, channel: Option(discord.TextChannel, "The channel to send the self-role menu to."), role: Option(discord.Role, "The role to provide from the menu."), label: Option(str, "The label of the option."), emoji: Option(str, "The emoji of the option.")):
        try:

            invoker_top_role_position = ctx.author.top_role.position
            bot_top_role = ctx.guild.me.top_role.position
            role_position = role.position

            if role.managed:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You can not add managed roles.")
                await ctx.respond(embed=embed, ephemeral=True)
                return 
            
            if invoker_top_role_position <= role_position and not ctx.author.id == ctx.author.guild.owner.id:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"You can not add the {role.mention} role.")
                await ctx.respond(embed=embed, ephemeral=True)
                return 

            if bot_top_role < role_position:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Please make sure the bots role is above the selected role.")
                return await ctx.respond(embed=embed, ephemeral=True)

            view = discord.ui.View()
            select_options = []
            select_options.append(discord.SelectOption(label=label, value=f"selfmenu|{role.id}", emoji=emoji))

            view.add_item(discord.ui.Select(placeholder="Select a role...", options=select_options, min_values=1, max_values=1, custom_id="self_menu"))

            user_embed = await db.build_embed(ctx.author.guild, title=f"Embed Builder", description=f"Use the buttons below to configure your self-role embed.")
            embed_tool = embedTool.EmbedToolView(channel_or_message=channel, is_new_embed=True, custom=None, view=view, ctx=ctx)
            await ctx.respond(embed=user_embed, view=embed_tool, ephemeral=True)

        except discord.HTTPException as e:
            if e.code == 50035:
                await ctx.respond(embed=await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The emoji you provided was invalid."), ephemeral=True)
            else:
                await ctx.respond(embed=await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Unknown HTTP error occured."), ephemeral=True)

        except Exception as e:
            print("[self_menu]: ", e)
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"An error occurred while processing your request.")
            await ctx.respond(embed=embed, ephemeral=True)

    
    @selfroleSubCommands.command(name="add", description="Add an option to the self-role menu.")
    @commands.guild_only()
    async def self_menu_add(self, ctx: discord.ApplicationContext, message_link: Option(str, "The link of the message with the menu. (Right click the message and select 'Copy Message Link')"), role: Option(discord.Role, "The role to provide from the menu."), label: Option(str, "The label of the option."), emoji: Option(str, "The emoji of the option.")):
        
        invoker_top_role_position = ctx.author.top_role.position
        bot_top_role = ctx.guild.me.top_role.position
        role_position = role.position

        if role.managed:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You can not add managed roles.")
            await ctx.respond(embed=embed, ephemeral=True)
            return 
        
        if invoker_top_role_position <= role_position and not ctx.author.id == ctx.author.guild.owner.id:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"You can not add the {role.mention} role.")
            await ctx.respond(embed=embed, ephemeral=True)
            return 

        if bot_top_role < role_position:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Please make sure the bots role is above the selected role.")
            return await ctx.respond(embed=embed, ephemeral=True)
            
        pattern = r"https://(?:canary\.|ptb\.|)discord(?:app)?\.com/channels/(\d+)/(\d+)/(\d+)"
        match = re.search(pattern, message_link)
        if not match:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The message link you provided was incorrect. Make sure to right click the message and select 'Copy Message Link'.")
            await ctx.respond(embed=embed, ephemeral=True)
            return

        message_link_parts = message_link.split('/')
        channel_id = int(message_link_parts[-2])
        message_id = int(message_link_parts[-1])

        try:
            channel = ctx.guild.get_channel(channel_id)
            message = await channel.fetch_message(message_id)

            if not message.author.id == ctx.guild.me.id:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="I can not edit a message that was not sent by me.")
                await ctx.respond(embed=embed, ephemeral=True)
                return
            
            view = discord.ui.View.from_message(message)

            select_menu = None
            for item in view.children:
                if isinstance(item, discord.ui.Select):
                    select_menu = item
                    break

            if select_menu:
                # Check if the select menu has reached its maximum number of options (25)
                if select_menu.max_values >= 25:
                    embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The select menu already has the maximum number of options (25). You cannot add more options.")
                    await ctx.respond(embed=embed, ephemeral=True)
                else:
                    # Check if the role is already in the select menu options
                    role_option_exists = any(option.value == f"selfmenu|{role.id}" for option in select_menu.options)
                    if role_option_exists:
                        embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The role {role.mention} is already in the select menu options.")
                        await ctx.respond(embed=embed, ephemeral=True)
                    else:
                        select_menu.max_values += 1
                        select_menu.add_option(label=label, value=f"selfmenu|{role.id}", emoji=emoji)

                        await message.edit(view=view)

                        embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Self-Role Menu Updated", description=f"The **{label}** option has been added to the self-role menu.")
                        await ctx.respond(embed=embed, ephemeral=True)
            else:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"No select menu found in the message.")
                await ctx.respond(embed=embed, ephemeral=True)

        except discord.NotFound:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The specified message was not found.")
            await ctx.respond(embed=embed, ephemeral=True)

        except discord.Forbidden:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="I do not have the necessary permissions to edit this message.")
            await ctx.respond(embed=embed, ephemeral=True)

        except discord.HTTPException:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="An unexpected HTTP error occurred.")
            await ctx.respond(embed=embed, ephemeral=True)

            
    @selfroleSubCommands.command(name="remove", description="Remove an option from the self-role menu.")
    @commands.guild_only()
    async def self_menu_remove(self, ctx: discord.ApplicationContext, message_link: Option(str, "The link of the message with the menu. (Right click the message and select 'Copy Message Link')"), label: Option(str, "The label of the option to remove.")):
        
        pattern = r"https://(?:canary\.|ptb\.|)discord(?:app)?\.com/channels/(\d+)/(\d+)/(\d+)"
        match = re.search(pattern, message_link)
        if not match:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The message link you provided was incorrect. Make sure to right click the message and select 'Copy Message Link'.")
            await ctx.respond(embed=embed, ephemeral=True)
            return

        message_link_parts = message_link.split('/')
        channel_id = int(message_link_parts[-2])
        message_id = int(message_link_parts[-1])

        try:
            channel = ctx.guild.get_channel(channel_id)
            message = await channel.fetch_message(message_id)

            if not message.author.id == ctx.guild.me.id:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="I can not edit a message that was not sent by me.")
                await ctx.respond(embed=embed, ephemeral=True)
                return

            view = discord.ui.View.from_message(message)

            select_menu = None
            for item in view.children:
                if isinstance(item, discord.ui.Select):
                    select_menu = item
                    break

            if select_menu:
                removed_option = None
                for option in select_menu.options:
                    if option.label == label:
                        removed_option = option
                        break

                if removed_option:
                    select_menu.max_values -= 1
                    select_menu.options.remove(removed_option)

                    await message.edit(view=view)

                    embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Self-Role Menu Updated", description=f"The **{label}** option has been removed from the self-role menu.")
                    await ctx.respond(embed=embed, ephemeral=True)
                else:
                    embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"No option with the label **{label}** found in the select menu.")
                    await ctx.respond(embed=embed, ephemeral=True)
            else:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"No select menu found in the message.")
                await ctx.respond(embed=embed, ephemeral=True)

        except discord.NotFound:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The specified message was not found.")
            await ctx.respond(embed=embed, ephemeral=True)

        except discord.Forbidden:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="I do not have the necessary permissions to edit this message.")
            await ctx.respond(embed=embed, ephemeral=True)

        except discord.HTTPException:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="An unexpected HTTP error occurred.")
            await ctx.respond(embed=embed, ephemeral=True)


def setup(client):
    client.add_cog(roles(client))
