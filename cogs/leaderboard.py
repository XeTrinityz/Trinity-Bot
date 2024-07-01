# Discord Imports
from discord.ext import commands, pages
from discord import Option
import discord

# Local Module Imports
from utils.database import Database
from Bot import is_blocked
from utils.lists import *

db = Database()

class leaderboard(commands.Cog):
    def __init__(self, client):
        self.client = client

    leaderboardSubCommands = discord.SlashCommandGroup("leaderboard", "Messages, Balance, Level, Invites, Stars, Repuation, Tickets.")

    @commands.user_command(name="Member Messages", description="Shows a members message count.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def message_count_user(self, ctx: discord.ApplicationContext, member: discord.Member):

        messages = await db.get_leaderboard_data(member, "messages")

        if messages:
            embed = await db.build_embed(ctx.author.guild, title=f"<a:Message:1247220773265870898> Message Count", description=f"{member.mention} has sent a total of **{messages}** messages in **{ctx.guild.name}**.")
            embed.set_thumbnail(url=member.avatar.url)
            await ctx.respond(embed=embed)
        else:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Message Count", description="This member has not sent any messages in this server.")
            await ctx.respond(embed=embed)

    
    @commands.user_command(name="Member Level", description="Shows a members level and XP.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def level_user(self, ctx: discord.ApplicationContext, member: discord.Member):

        level = await db.get_leaderboard_data(member, "level")
        xp = await db.get_leaderboard_data(member, "xp")
        next_level = await db.get_leaderboard_data(member, "next_level")

        embed = await db.build_embed(ctx.author.guild, title="<a:Level:1247223153839702106> Level & XP", description=f"{member.mention} is level **{level}** with **{xp}/{int(next_level)}** XP.")
        embed.set_thumbnail(url=member.avatar.url)
        await ctx.respond(embed=embed)

    
    @commands.user_command(name="Member Invites", description="Shows how many members they have invited.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def invites_user(self, ctx: discord.ApplicationContext, member: discord.Member):
            
        invites = await db.get_leaderboard_data(member, "invited_users")
        if invites == 0:
            embed = await db.build_embed(ctx.author.guild, title="<a:Folder:1247220756547502160> Total Invites", description=f"{member.mention} has invited a total of **0** members to **{ctx.guild.name}**!")
        else:
            invites = len(invites)
            embed = await db.build_embed(ctx.author.guild, title="<a:Folder:1247220756547502160> Total Invites", description=f"{member.mention} has invited a total of **{invites}** members to **{ctx.guild.name}**!")

        embed.set_thumbnail(url=member.avatar.url)
        await ctx.respond(embed=embed)

    
    @commands.user_command(name="Member Balance", description="Shows a members balance.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def balance_user(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to get the balance from.")):

        cash = await db.get_leaderboard_data(member, "cash")

        embed = await db.build_embed(ctx.author.guild, title="<a:Cash:1247220739220701184> Balance", description=f"{member.mention} has **${cash}** in their wallet.")
        embed.set_thumbnail(url=member.avatar.url)
        await ctx.respond(embed=embed)


    @commands.slash_command(name="messages", description="Shows a members message count.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def message_count(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to get the message count from.")):
        
        messages = await db.get_leaderboard_data(member, "messages")

        if messages:
            embed = await db.build_embed(ctx.author.guild, title=f"<a:Message:1247220773265870898> Message Count", description=f"{member.mention} has sent a total of **{messages}** messages in **{ctx.guild.name}**.")
            embed.set_thumbnail(url=member.avatar.url)
            await ctx.respond(embed=embed)
        else:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Message Count", description="This member has not sent any messages in this server.")
            await ctx.respond(embed=embed)


    @commands.slash_command(name="reputation", description="Shows a members reputation points.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def rep_count(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to get the reputation points from.")):
        
        rep = await db.get_leaderboard_data(member, "reputation")

        if rep:
            embed = await db.build_embed(ctx.author.guild, title=f"<a:Level:1247223153839702106> Reputation Points", description=f"{member.mention} has a total of **{rep}** reputation points in **{ctx.guild.name}**.")
            embed.set_thumbnail(url=member.avatar.url)
            await ctx.respond(embed=embed)
        else:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Reputation Points", description="This member has not received any reputation points in this server.")
            await ctx.respond(embed=embed)


    @commands.slash_command(name="stars", description="Shows a members star count from the starboard.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def star_count(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to get the star count from.")):
        
        stars = await db.get_leaderboard_data(member, "stars")

        if stars:
            embed = await db.build_embed(ctx.author.guild, title="⭐ Star Count", description=f"{member.mention} has received a total of **{stars}** stars in **{ctx.guild.name}**.")
            embed.set_thumbnail(url=member.avatar.url)
            await ctx.respond(embed=embed)
        else:
            embed = await db.build_embed(ctx.author.guild, title="⭐ Star Count", description="This member has not received any stars in this server.")
            await ctx.respond(embed=embed, ephemeral=True)


    @commands.slash_command(name="level", description="Shows a user's level and XP.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def level(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The user to get the level/XP from.")):

        level = await db.get_leaderboard_data(member, "level")
        xp = await db.get_leaderboard_data(member, "xp")
        next_level = await db.get_leaderboard_data(member, "next_level")

        embed = await db.build_embed(ctx.author.guild, title="<a:Level:1247223153839702106> Level & XP", description=f"{member.mention} is level **{level}** with **{xp}/{int(next_level)}** XP.")
        embed.set_thumbnail(url=member.avatar.url)
        await ctx.respond(embed=embed)


    @commands.slash_command(name="invites", description="Shows how many members they have invited.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def invites(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The user to get the invites from.")):

        invited_users = await db.get_leaderboard_data(member, "invited_users")

        if not invited_users:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Invited Users", description=f"{member.mention} has not invited any users to **{ctx.guild.name}**.")
            embed.set_thumbnail(url=member.avatar.url)
            await ctx.respond(embed=embed, ephemeral=True)
        else:
            formatted_invited_users = []
            for invited_user in invited_users:
                guild_member = ctx.guild.get_member(invited_user)
                if guild_member is not None:
                    global_name = guild_member.global_name if guild_member.global_name else "Unknown Name"
                    formatted_invited_users.append(f"{global_name} `({invited_user})`")
                else:
                    formatted_invited_users.append(f"Unknown User `({invited_user})`")

            pages_content = [formatted_invited_users[i:i + 10] for i in range(0, len(formatted_invited_users), 10)]

            embeds = []
            for page in pages_content:
                embed = await db.build_embed(
                    ctx.author.guild,
                    title="<a:Folder:1247220756547502160> Invited Users",
                    description=f"{member.mention} has invited a total of **{len(invited_users)}** users to **{ctx.guild.name}**.\n\n" + "\n".join(page)
                )
                embed.set_thumbnail(url=member.avatar.url)
                embeds.append(embed)

            paginator = pages.Paginator(pages=embeds, disable_on_timeout=True, use_default_buttons=False, show_indicator=True, loop_pages=True, timeout=60)
            if len(embeds) > 1:
                if len(embeds) > 10:
                    paginator.add_button(pages.PaginatorButton("first", label="", emoji="<a:First:1182373753498370069>", style=discord.ButtonStyle.grey))
                paginator.add_button(pages.PaginatorButton("prev", label="", emoji="<a:LeftArrow:1156039371624026112>", style=discord.ButtonStyle.grey))
                paginator.add_button(pages.PaginatorButton("page_indicator", style=discord.ButtonStyle.gray, disabled=True))
                paginator.add_button(pages.PaginatorButton("next", label="", emoji="<a:RightArrow:1156039369875001385>", style=discord.ButtonStyle.grey))
                if len(embeds) > 10:
                    paginator.add_button(pages.PaginatorButton("last", label="", emoji="<a:Last:1182374111306063902>", style=discord.ButtonStyle.grey))
            await paginator.respond(ctx.interaction)


    @leaderboardSubCommands.command(name="remove", description="Remove a member from all leaderboards.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def leaderboard_remove(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to remove from the leaderboard.")):

        try:
            await db.remove_value_from_table(ctx.guild.id, "LeaderboardStats", "Value", "ServerID", ctx.guild.id, str(member.id))
            embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Member Removed", description=f"{member.mention} was removed from your leaderboards.")
            await ctx.respond(embed=embed)
        except:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="This member has no entries on your leaderboards.")
            return await ctx.respond(embed=embed)


    @leaderboardSubCommands.command(name="reputation", description="Shows the leaderboard based on member reputation.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def leaderboard_rep(self, ctx: discord.ApplicationContext):

        await ctx.defer()

        leaderboard_data = await db.get_all_leaderboard_data(ctx.guild.id, "reputation")

        if not leaderboard_data:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Reputation Leaderboard", description="There are no entries on the leaderboard.")
            return await ctx.respond(embed=embed)
        
        max_users_per_page = 10

        if len(leaderboard_data) <= max_users_per_page:
            leaderboard_embed = await db.build_embed(ctx.guild, title="<a:Trophy:1247220827955527693> Reputation Leaderboard")

            description = ""

            for position, (user_id, reputation_points) in enumerate(leaderboard_data, start=1):
                member = ctx.guild.get_member(int(user_id))
                if member and reputation_points != 0:
                    description += f"**{position}.** {member.mention} ➭ **{reputation_points}** Points\n"
                else:
                    await db.remove_value_from_table(ctx.guild.id, "LeaderboardStats", "Value", "ServerID", ctx.guild.id, str(user_id))

            leaderboard_embed.description = description
            await ctx.edit(embed=leaderboard_embed)
        else:
            leaderboard_pages = [leaderboard_data[i : i + max_users_per_page] for i in range(0, len(leaderboard_data), max_users_per_page)]

            leaderboard_embeds = []

            for page_index, page_data in enumerate(leaderboard_pages, start=1):
                leaderboard_embed = await db.build_embed(ctx.guild, title="<a:Trophy:1247220827955527693> Reputation Leaderboard")

                description = ""

                for position, (user_id, reputation_points) in enumerate(page_data, start=(page_index - 1) * max_users_per_page + 1):
                    member = ctx.guild.get_member(int(user_id))
                    if member and reputation_points != 0:
                        description += f"**{position}.** {member.mention} ➭ **{reputation_points}** Points\n"
                    else:
                        await db.remove_value_from_table(ctx.guild.id, "LeaderboardStats", "Value", "ServerID", ctx.guild.id, str(user_id))

                leaderboard_embed.description = description
                leaderboard_embeds.append(leaderboard_embed)

            paginator = pages.Paginator(pages=leaderboard_embeds, disable_on_timeout=True, use_default_buttons=False, show_indicator=True, loop_pages=True, timeout=60)
            if len(leaderboard_embeds) > 10:
                paginator.add_button(pages.PaginatorButton("first", label="", emoji="<a:First:1182373753498370069>", style=discord.ButtonStyle.grey))
            paginator.add_button(pages.PaginatorButton("prev", label="", emoji="<a:LeftArrow:1156039371624026112>", style=discord.ButtonStyle.grey))
            paginator.add_button(pages.PaginatorButton("page_indicator", style=discord.ButtonStyle.gray, disabled=True))
            paginator.add_button(pages.PaginatorButton("next", label="", emoji="<a:RightArrow:1156039369875001385>", style=discord.ButtonStyle.grey))
            if len(leaderboard_embeds) > 10:
                paginator.add_button(pages.PaginatorButton("last", label="", emoji="<a:Last:1182374111306063902>", style=discord.ButtonStyle.grey))

            await paginator.respond(ctx.interaction)


    @leaderboardSubCommands.command(name="messages", description="Shows the leaderboard based on member messages.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def leaderboard_messages(self, ctx: discord.ApplicationContext):

        await ctx.defer()

        leaderboard_data = await db.get_all_leaderboard_data(ctx.guild.id, "messages")
        if not leaderboard_data:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Message Leaderboard", description="There are no entries on the leaderboard.")
            return await ctx.respond(embed=embed)
        
        max_users_per_page = 10

        if len(leaderboard_data) <= max_users_per_page:
            leaderboard_embed = await db.build_embed(ctx.guild, title="<a:Trophy:1247220827955527693> Message Leaderboard")

            description = ""

            for position, (user_id, message_count) in enumerate(leaderboard_data, start=1):
                member = ctx.guild.get_member(int(user_id))
                if member and message_count != 0:
                    description += f"**{position}.** {member.mention} ➭ **{message_count}** Messages\n"
                else:
                    await db.remove_value_from_table(ctx.guild.id, "LeaderboardStats", "Value", "ServerID", ctx.guild.id, str(user_id))

            leaderboard_embed.description = description
            await ctx.edit(embed=leaderboard_embed)
        else:
            leaderboard_pages = [leaderboard_data[i : i + max_users_per_page] for i in range(0, len(leaderboard_data), max_users_per_page)]

            leaderboard_embeds = []

            for page_index, page_data in enumerate(leaderboard_pages, start=1):
                leaderboard_embed = await db.build_embed(ctx.guild, title="<a:Trophy:1247220827955527693> Message Leaderboard")

                description = ""

                for position, (user_id, message_count) in enumerate(page_data, start=(page_index - 1) * max_users_per_page + 1):
                    member = ctx.guild.get_member(int(user_id))
                    if member and message_count != 0:
                        description += f"**{position}.** {member.mention} ➭ **{message_count}** Messages\n"
                    else:
                        await db.remove_value_from_table(ctx.guild.id, "LeaderboardStats", "Value", "ServerID", ctx.guild.id, str(user_id))

                leaderboard_embed.description = description
                leaderboard_embeds.append(leaderboard_embed)

            paginator = pages.Paginator(pages=leaderboard_embeds, disable_on_timeout=True, use_default_buttons=False, show_indicator=True, loop_pages=True, timeout=60)
            if len(leaderboard_embeds) > 10:
                paginator.add_button(pages.PaginatorButton("first", label="", emoji="<a:First:1182373753498370069>", style=discord.ButtonStyle.grey))
            paginator.add_button(pages.PaginatorButton("prev", label="", emoji="<a:LeftArrow:1156039371624026112>", style=discord.ButtonStyle.grey))
            paginator.add_button(pages.PaginatorButton("page_indicator", style=discord.ButtonStyle.gray, disabled=True))
            paginator.add_button(pages.PaginatorButton("next", label="", emoji="<a:RightArrow:1156039369875001385>", style=discord.ButtonStyle.grey))
            if len(leaderboard_embeds) > 10:
                paginator.add_button(pages.PaginatorButton("last", label="", emoji="<a:Last:1182374111306063902>", style=discord.ButtonStyle.grey))

            await paginator.respond(ctx.interaction)


    @leaderboardSubCommands.command(name="invites", description="Shows the leaderboard based on user invites.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def leaderboard_invites(self, ctx: discord.ApplicationContext):

        await ctx.defer()

        leaderboard_data = await db.get_all_leaderboard_data(ctx.guild.id, "invited_users")

        if not leaderboard_data:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Invite Leaderboard", description="There are no entries on the leaderboard.")
            return await ctx.respond(embed=embed)
        
        leaderboard_data.sort(key=lambda x: len(x[1]), reverse=True)  # Sort the data based on the number of invites

        max_users_per_page = 10

        if len(leaderboard_data) <= max_users_per_page:
            leaderboard_embed = await db.build_embed(ctx.guild, title="<a:Trophy:1247220827955527693> Invite Leaderboard")

            description = ""

            for position, (user_id, invite_count) in enumerate(leaderboard_data, start=1):
                member = ctx.guild.get_member(int(user_id))
                if member and invite_count != 0:
                    description += f"**{position}.** {member.mention} ➭ **{len(invite_count)}** Invites\n"
                else:
                    await db.remove_value_from_table(ctx.guild.id, "LeaderboardStats", "Value", "ServerID", ctx.guild.id, str(user_id))

            leaderboard_embed.description = description
            await ctx.edit(embed=leaderboard_embed)
        else:
            leaderboard_pages = [leaderboard_data[i : i + max_users_per_page] for i in range(0, len(leaderboard_data), max_users_per_page)]

            leaderboard_embeds = []

            for page_index, page_data in enumerate(leaderboard_pages, start=1):
                leaderboard_embed = await db.build_embed(ctx.guild, title="<a:Trophy:1247220827955527693> Invite Leaderboard")

                description = ""

                for position, (user_id, invite_count) in enumerate(page_data, start=(page_index - 1) * max_users_per_page + 1):
                    member = ctx.guild.get_member(int(user_id))
                    if member and invite_count != 0:
                        description += f"**{position}.** {member.mention} ➭ **{len(invite_count)}** Invites\n"
                    else:
                        await db.remove_value_from_table(ctx.guild.id, "LeaderboardStats", "Value", "ServerID", ctx.guild.id, str(user_id))

                leaderboard_embed.description = description
                leaderboard_embeds.append(leaderboard_embed)

            paginator = pages.Paginator(pages=leaderboard_embeds, disable_on_timeout=True, use_default_buttons=False, show_indicator=True, loop_pages=True, timeout=60)
            if len(leaderboard_embeds) > 10:
                paginator.add_button(pages.PaginatorButton("first", label="", emoji="<a:First:1182373753498370069>", style=discord.ButtonStyle.grey))
            paginator.add_button(pages.PaginatorButton("prev", label="", emoji="<a:LeftArrow:1156039371624026112>", style=discord.ButtonStyle.grey))
            paginator.add_button(pages.PaginatorButton("page_indicator", style=discord.ButtonStyle.gray, disabled=True))
            paginator.add_button(pages.PaginatorButton("next", label="", emoji="<a:RightArrow:1156039369875001385>", style=discord.ButtonStyle.grey))
            if len(leaderboard_embeds) > 10:
                paginator.add_button(pages.PaginatorButton("last", label="", emoji="<a:Last:1182374111306063902>", style=discord.ButtonStyle.grey))

            await paginator.respond(ctx.interaction)


    @leaderboardSubCommands.command(name="tickets", description="Shows the leaderboard based on tickets and ticket messages.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.has_guild_permissions(view_audit_log=True)
    async def leaderboard_tickets(self, ctx: discord.ApplicationContext):

        await ctx.defer()

        leaderboard_tickets_claimed = await db.get_all_leaderboard_data(ctx.guild.id, "tickets_claimed")
        leaderboard_ticket_messages = await db.get_all_leaderboard_data(ctx.guild.id, "ticket_messages")

        leaderboard_data = {}

        for (user_id_claimed, ticket_count) in leaderboard_tickets_claimed:
            leaderboard_data[user_id_claimed] = {"tickets_claimed": ticket_count}

        for (user_id_messages, ticket_messages_count) in leaderboard_ticket_messages:
            if user_id_messages in leaderboard_data:
                leaderboard_data[user_id_messages]["ticket_messages"] = ticket_messages_count
            else:
                leaderboard_data[user_id_messages] = {"ticket_messages": ticket_messages_count}

        filtered_leaderboard_data = {
            user_id: data for user_id, data in leaderboard_data.items()
            if data.get("tickets_claimed", 0) > 0 or data.get("ticket_messages", 0) > 0}

        if not filtered_leaderboard_data:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Ticket Leaderboard", description="There are no entries on the leaderboard.")
            return await ctx.respond(embed=embed, ephemeral=True)

        # Calculate the total for each user (tickets claimed + ticket messages)
        for user_id, data in filtered_leaderboard_data.items():
            total = data.get("tickets_claimed", 0) + data.get("ticket_messages", 0)
            data["total"] = total

        # Sort the leaderboard based on the total
        sorted_leaderboard_data = dict(sorted(filtered_leaderboard_data.items(), key=lambda x: x[1]["total"], reverse=True))

        max_users_per_page = 10

        if len(sorted_leaderboard_data) <= max_users_per_page:
            leaderboard_embed = await db.build_embed(ctx.guild, title="<a:Trophy:1247220827955527693> Ticket Leaderboard")

            for position, (user_id, data) in enumerate(sorted_leaderboard_data.items(), start=1):
                ticket_claimed_count = data.get("tickets_claimed", 0)
                ticket_messages_count = data.get("ticket_messages", 0)
                member = ctx.guild.get_member(int(user_id))
                if member:
                    leaderboard_embed.add_field(name=f"{position}. {member.global_name}", value=f"**{ticket_claimed_count}** Tickets Claimed | **{ticket_messages_count}** Messages Sent", inline=False)
                else:
                    await db.remove_value_from_table(ctx.guild.id, "LeaderboardStats", "Value", "ServerID", ctx.guild.id, str(user_id))

            await ctx.edit(embed=leaderboard_embed)
        else:
            leaderboard_pages = [list(sorted_leaderboard_data.items())[i : i + max_users_per_page] for i in range(0, len(sorted_leaderboard_data), max_users_per_page)]
            leaderboard_embeds = []

            for page_index, page_data in enumerate(leaderboard_pages, start=1):
                leaderboard_embed = await db.build_embed(ctx.guild, title="<a:Trophy:1247220827955527693> Ticket Leaderboard")

                for position, (user_id, data) in enumerate(page_data, start=(page_index - 1) * max_users_per_page + 1):
                    ticket_claimed_count = data.get("tickets_claimed", 0)
                    ticket_messages_count = data.get("ticket_messages", 0)
                    member = ctx.guild.get_member(int(user_id))
                    if member:
                        leaderboard_embed.add_field(name=f"{position}. {member.global_name}", value=f"**Tickets Claimed** ➭ **{ticket_claimed_count}** Tickets\n**Ticket Messages Sent** ➭ **{ticket_messages_count}** Messages", inline=False)
                    else:
                        await db.remove_value_from_table(ctx.guild.id, "LeaderboardStats", "Value", "ServerID", ctx.guild.id, str(user_id))

                leaderboard_embeds.append(leaderboard_embed)

            paginator = pages.Paginator(pages=leaderboard_embeds, disable_on_timeout=True, use_default_buttons=False, show_indicator=True, loop_pages=True, timeout=60)
            if len(leaderboard_embeds) > 10:
                paginator.add_button(pages.PaginatorButton("first", label="", emoji="<a:First:1182373753498370069>", style=discord.ButtonStyle.grey))
            paginator.add_button(pages.PaginatorButton("prev", label="", emoji="<a:LeftArrow:1156039371624026112>", style=discord.ButtonStyle.grey))
            paginator.add_button(pages.PaginatorButton("page_indicator", style=discord.ButtonStyle.gray, disabled=True))
            paginator.add_button(pages.PaginatorButton("next", label="", emoji="<a:RightArrow:1156039369875001385>", style=discord.ButtonStyle.grey))
            if len(leaderboard_embeds) > 10:
                paginator.add_button(pages.PaginatorButton("last", label="", emoji="<a:Last:1182374111306063902>", style=discord.ButtonStyle.grey))

            await paginator.respond(ctx.interaction)


    @leaderboardSubCommands.command(name="level", description="Shows the leaderboard based on user levels.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def leaderboard_level(self, ctx: discord.ApplicationContext):

        await ctx.defer()

        leaderboard_data = await db.get_all_leaderboard_data(ctx.guild.id, "level")

        if not leaderboard_data:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Level Leaderboard", description="There are no entries on the leaderboard.")
            return await ctx.respond(embed=embed, ephemeral=True)
        
        max_users_per_page = 10

        if len(leaderboard_data) <= max_users_per_page:
            leaderboard_embed = await db.build_embed(ctx.guild, title="<a:Trophy:1247220827955527693> Level Leaderboard")

            description = ""

            for position, (user_id, level) in enumerate(leaderboard_data, start=1):
                member = ctx.guild.get_member(int(user_id))
                if member and level != 0:
                    description += (f"**{position}.** {member.mention} ➭ Level **{level}**\n")
                else:
                    await db.remove_value_from_table(ctx.guild.id, "LeaderboardStats", "Value", "ServerID", ctx.guild.id, str(user_id))

            leaderboard_embed.description = description
            await ctx.edit(embed=leaderboard_embed)
        else:
            leaderboard_pages = [leaderboard_data[i : i + max_users_per_page] for i in range(0, len(leaderboard_data), max_users_per_page)]

            leaderboard_embeds = []

            for page_index, page_data in enumerate(leaderboard_pages, start=1):
                leaderboard_embed = await db.build_embed(ctx.guild, title="<a:Trophy:1247220827955527693> Level Leaderboard")
                
                description = ""

                for position, (user_id, level) in enumerate(page_data, start=(page_index - 1) * max_users_per_page + 1):
                    member = ctx.guild.get_member(int(user_id))
                    if member and level != 0:
                        description += f"**{position}.** {member.mention} ➭ Level **{level}**\n"
                    else:
                        await db.remove_value_from_table(ctx.guild.id, "LeaderboardStats", "Value", "ServerID", ctx.guild.id, str(user_id))

                leaderboard_embed.description = description
                leaderboard_embeds.append(leaderboard_embed)

            paginator = pages.Paginator(pages=leaderboard_embeds, disable_on_timeout=True, use_default_buttons=False, show_indicator=True, loop_pages=True, timeout=60)
            if len(leaderboard_embeds) > 10:
                paginator.add_button(pages.PaginatorButton("first", label="", emoji="<a:First:1182373753498370069>", style=discord.ButtonStyle.grey))
            paginator.add_button(pages.PaginatorButton("prev", label="", emoji="<a:LeftArrow:1156039371624026112>", style=discord.ButtonStyle.grey))
            paginator.add_button(pages.PaginatorButton("page_indicator", style=discord.ButtonStyle.gray, disabled=True))
            paginator.add_button(pages.PaginatorButton("next", label="", emoji="<a:RightArrow:1156039369875001385>", style=discord.ButtonStyle.grey))
            if len(leaderboard_embeds) > 10:
                paginator.add_button(pages.PaginatorButton("last", label="", emoji="<a:Last:1182374111306063902>", style=discord.ButtonStyle.grey))

            await paginator.respond(ctx.interaction)


    @leaderboardSubCommands.command(name="balance", description="Shows the leaderboard based on user balance.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def leaderboard_balance(self, ctx: discord.ApplicationContext):

        await ctx.defer()

        leaderboard_data = await db.get_all_leaderboard_data(ctx.guild.id, "cash")

        if not leaderboard_data:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Cash Leaderboard", description="There are no entries on the leaderboard.")
            return await ctx.respond(embed=embed, ephemeral=True)
        
        max_users_per_page = 10

        if len(leaderboard_data) <= max_users_per_page:
            leaderboard_embed = await db.build_embed(ctx.guild, title="<a:Trophy:1247220827955527693> Cash Leaderboard")

            description = ""

            for position, (user_id, cash) in enumerate(leaderboard_data, start=1):
                member = ctx.guild.get_member(int(user_id))
                if member and cash != 0:
                    description += (f"**{position}.** {member.mention} ➭ **${cash}**\n")
                else:
                    await db.remove_value_from_table(ctx.guild.id, "LeaderboardStats", "Value", "ServerID", ctx.guild.id, str(user_id))

            leaderboard_embed.description = description
            return await ctx.edit(embed=leaderboard_embed)
        else:
            leaderboard_pages = [leaderboard_data[i : i + max_users_per_page] for i in range(0, len(leaderboard_data), max_users_per_page)]

            leaderboard_embeds = []

            for page_index, page_data in enumerate(leaderboard_pages, start=1):
                leaderboard_embed = await db.build_embed(ctx.guild, title="<a:Trophy:1247220827955527693> Cash Leaderboard")
                
                description = ""

                for position, (user_id, cash) in enumerate(page_data, start=(page_index - 1) * max_users_per_page + 1):
                    member = ctx.guild.get_member(int(user_id))
                    if member and cash != 0:
                        description += (f"**{position}.** {member.mention} ➭ **${cash}**\n")
                    else:
                        await db.remove_value_from_table(ctx.guild.id, "LeaderboardStats", "Value", "ServerID", ctx.guild.id, str(user_id))

                leaderboard_embed.description = description
                leaderboard_embeds.append(leaderboard_embed)

            paginator = pages.Paginator(pages=leaderboard_embeds, disable_on_timeout=True, use_default_buttons=False, show_indicator=True, loop_pages=True, timeout=60)
            if len(leaderboard_embeds) > 10:
                paginator.add_button(pages.PaginatorButton("first", label="", emoji="<a:First:1182373753498370069>", style=discord.ButtonStyle.grey))
            paginator.add_button(pages.PaginatorButton("prev", label="", emoji="<a:LeftArrow:1156039371624026112>", style=discord.ButtonStyle.grey))
            paginator.add_button(pages.PaginatorButton("page_indicator", style=discord.ButtonStyle.gray, disabled=True))
            paginator.add_button(pages.PaginatorButton("next", label="", emoji="<a:RightArrow:1156039369875001385>", style=discord.ButtonStyle.grey))
            if len(leaderboard_embeds) > 10:
                paginator.add_button(pages.PaginatorButton("last", label="", emoji="<a:Last:1182374111306063902>", style=discord.ButtonStyle.grey))

            await paginator.respond(ctx.interaction)


    @leaderboardSubCommands.command(name="stars", description="Shows the leaderboard based on member stars.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def leaderboard_stars(self, ctx: discord.ApplicationContext):

        await ctx.defer()

        leaderboard_data = await db.get_all_leaderboard_data(ctx.guild.id, "stars")

        if not leaderboard_data:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Star Leaderboard", description="There are no entries on the leaderboard.")
            return await ctx.respond(embed=embed, ephemeral=True)
        
        max_users_per_page = 10

        if len(leaderboard_data) <= max_users_per_page:
            leaderboard_embed = await db.build_embed(ctx.guild, title="<a:Trophy:1247220827955527693> Star Leaderboard")

            description = ""

            for position, (user_id, stars) in enumerate(leaderboard_data, start=1):
                member = ctx.guild.get_member(int(user_id))
                if member and stars != 0:
                    description += (f"**{position}.** {member.mention} ➭ ⭐ **{stars}**\n")
                else:
                    await db.remove_value_from_table(ctx.guild.id, "LeaderboardStats", "Value", "ServerID", ctx.guild.id, str(user_id))

            leaderboard_embed.description = description
            return await ctx.edit(embed=leaderboard_embed)
        else:
            leaderboard_pages = [leaderboard_data[i : i + max_users_per_page] for i in range(0, len(leaderboard_data), max_users_per_page)]

            leaderboard_embeds = []

            for page_index, page_data in enumerate(leaderboard_pages, start=1):
                leaderboard_embed = await db.build_embed(ctx.guild, title="<a:Trophy:1247220827955527693> Star Leaderboard")
                
                description = ""

                for position, (user_id, stars) in enumerate(page_data, start=(page_index - 1) * max_users_per_page + 1):
                    member = ctx.guild.get_member(int(user_id))
                    if member and stars != 0:
                        description += (f"**{position}.** {member.mention} ➭ ⭐ **{stars}**\n")
                    else:
                        await db.remove_value_from_table(ctx.guild.id, "LeaderboardStats", "Value", "ServerID", ctx.guild.id, str(user_id))

                leaderboard_embed.description = description
                leaderboard_embeds.append(leaderboard_embed)

            paginator = pages.Paginator(pages=leaderboard_embeds, disable_on_timeout=True, use_default_buttons=False, show_indicator=True, loop_pages=True, timeout=60)
            if len(leaderboard_embeds) > 10:
                paginator.add_button(pages.PaginatorButton("first", label="", emoji="<a:First:1182373753498370069>", style=discord.ButtonStyle.grey))
            paginator.add_button(pages.PaginatorButton("prev", label="", emoji="<a:LeftArrow:1156039371624026112>", style=discord.ButtonStyle.grey))
            paginator.add_button(pages.PaginatorButton("page_indicator", style=discord.ButtonStyle.gray, disabled=True))
            paginator.add_button(pages.PaginatorButton("next", label="", emoji="<a:RightArrow:1156039369875001385>", style=discord.ButtonStyle.grey))
            if len(leaderboard_embeds) > 10:
                paginator.add_button(pages.PaginatorButton("last", label="", emoji="<a:Last:1182374111306063902>", style=discord.ButtonStyle.grey))

            await paginator.respond(ctx.interaction)

def setup(client):
    client.add_cog(leaderboard(client))