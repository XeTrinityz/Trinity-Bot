# Discord Imports
from discord.utils import basic_autocomplete
from discord.ext import commands, pages
from datetime import datetime
from discord import Option
import discord

# Third-Party Library Imports
import aiohttp

# Local Module Imports
from utils.database import Database
from utils.lists import *
from utils.functions import Utils
from Bot import is_blocked, config

db = Database()
start_time = datetime.now()

class information(commands.Cog):
    def __init__(self, client):
        self.client = client

    class URLButton(discord.ui.View):
        def __init__(self, text, query: str):
            super().__init__()
            url = query
            self.add_item(discord.ui.Button(label=text, emoji="🔗", url=url))

    serverSubCommands = discord.SlashCommandGroup("server", "Info, Emotes, Members, Server Icon, Server Banner.")
    memberSubCommands = discord.SlashCommandGroup("member", "Info, Avatar.")

    @commands.user_command(name="Member Information", description="Shows detailed information about a member.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def member_info(self, ctx: discord.ApplicationContext, member: discord.Member):

        embed = await db.build_embed(ctx.author.guild, title="<a:Loading:1247220769511964673> Retrieving Information", description=f"Retrieving information on {member.mention}...")
        await ctx.respond(embed=embed)

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

        badges_list = [
            badge_names[badge.name]
            for badge in member.public_flags.all()
            if badge.name in badge_names]

        badges = ", ".join(badges_list) + "." if badges_list else "None"
        avatar_url = member.display_avatar.url

        roles_list = [role.mention for role in member.roles if role.name != member.guild.default_role.name]

        roles = ", ".join(reversed(roles_list)) + "." if roles_list else "None"
        nickname = member.nick
        highest_role = member.top_role.mention

        permissions_list = [user_permission_names[perm] for perm, value in member.guild_permissions if value and perm in user_permission_names]

        if "Administrator" in permissions_list:
            permissions_list = ["Administrator"]

        permissions = ", ".join(permissions_list) + "." if permissions_list else "None"
        is_boosting = "Yes" if member.premium_since else "No"

        messages = await db.get_leaderboard_data(member, "messages")
        invites = await db.get_leaderboard_data(member, "invited_users")
        cash = await db.get_leaderboard_data(member, "cash")
        rep = await db.get_leaderboard_data(member, "reputation")

        embed = await db.build_embed(ctx.author.guild, title=f"<a:Folder:1247220756547502160> User Information | {member.display_name}")
        embed.set_thumbnail(url=avatar_url)
        embed.set_image(url=banner_url)

        embed.add_field(
            name="**__Main Details__**",
            value=
            f"**Profile** ➭ {member.mention}\n"
            + f"**Username** ➭ {member.name}\n"
            + f"**ID** ➭ {member.id}\n"
            + f"**Badges** ➭ {badges}\n"
            + f"**Creation Date** ➭ <t:{int(member.created_at.timestamp())}:d> (<t:{int(member.created_at.timestamp())}:R>)",
            inline=False)

        embed.add_field(
            name="**__Server Specific__**",
            value=
            f"**Joined** ➭ <t:{int(member.joined_at.timestamp())}:R>\n"
            + f"**Booster** ➭ {is_boosting}\n"
            + f"**Nickname** ➭ {nickname}\n"
            + f"**Highest Role** ➭ {highest_role}",
            inline=False)

        if not member.bot:
            embed.add_field(
                name="**__Server Stats__**",
                value=
                f"**Message Count** ➭ {messages}\n"
                + f"**Reputation** ➭ {rep}\n"
                + f"**Balance** ➭ ${cash}\n"
                + f"**Invites** ➭ {len(invites) if invites != 0 else '0'}",
                inline=False)

        embed.add_field(name="**__Roles__**", value=roles, inline=False)
        embed.add_field(name="**__Permissions__**", value=permissions, inline=False)

        view = discord.ui.View()
        avatar = discord.ui.Button(label="Avatar", url=avatar_url, style=discord.ButtonStyle.link)
        user_url = discord.ui.Button(label="Member URL", url=f"https://discord.com/users/{member.id}", style=discord.ButtonStyle.link)
        view.add_item(avatar)
        view.add_item(user_url)

        await ctx.edit(embed=embed, view=view)


    @commands.slash_command(name="reportbug", description="Report a bug to the developer.")
    @commands.check(is_blocked)
    @commands.cooldown(1, 600, commands.BucketType.user)
    async def report_bug(self, ctx: discord.ApplicationContext, bug: Option(str, "The bug you want to report.", required=True)):

        bug_channel = discord.utils.get(self.client.get_all_channels(), id=1157694479143288852)
        embed = await db.build_embed(ctx.author.guild, title=f"<a:Information:1247223152367636541> Bug Reported", description="Thank you for reporting a bug! The developer will look into it as soon as possible.")
        await ctx.respond(embed=embed)

        embed = await db.build_embed(ctx.author.guild, title=f"<a:Information:1247223152367636541> Bug Report", description=f"{ctx.author.mention} reported a bug from the **{ctx.guild.name}** server.")
        embed.set_author(name=f"{ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.add_field(name="**Bug**", value=bug, inline=False)
        await bug_channel.send(embed=embed)


    @commands.slash_command(name="ping", description="Check the bot's latency and uptime.")
    @commands.check(is_blocked)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def ping(self, ctx: discord.ApplicationContext):

        embed = await db.build_embed(ctx.author.guild, title="<a:Loading:1247220769511964673> Retrieving Information", description="Retrieving latency information...")
        await ctx.respond(embed=embed)

        thresholds = [
            (60, "🟢"),
            (110, "🟡"),
            (210, "🔴"),
        ]

        shard = self.client.get_shard(ctx.guild.shard_id)
        shard_latency = shard.latency * 1000

        calc_database_latency = datetime.now()
        await db.get_leaderboard_data(ctx.author, "messages")
        database_latency = (datetime.now() - calc_database_latency).total_seconds() * 1000
        latency_emoji = "❓"

        for threshold_ms, emoji in thresholds:
            if shard_latency <= threshold_ms:
                latency_emoji = emoji
                break

        for threshold_ms, emoji in thresholds:
            if database_latency <= threshold_ms:
                latency_db_emoji = emoji
                break

        uptime_seconds = (datetime.now() - start_time).total_seconds()
        days, seconds = divmod(uptime_seconds, 86400)
        hours, seconds = divmod(seconds, 3600)  # Calculate hours based on remaining seconds
        minutes, seconds = divmod(seconds, 60)   # Calculate minutes based on remaining seconds
        uptime = f"**{int(days)}** Days, **{int(hours)}** Hours, **{int(minutes)}** Minutes and **{int(seconds)}** Seconds."

        embed = await db.build_embed(ctx.author.guild, title=f"<a:Information:1247223152367636541> Bot Latency and Uptime")
        embed.add_field(name=f"{latency_emoji} **Shard #{ctx.guild.shard_id}**", value=f"{shard_latency:.2f}ms", inline=True)
        embed.add_field(name=f"{latency_db_emoji} **Database**", value=f"{database_latency:.2f}ms", inline=True)
        
        #for shard in self.client.shards:
        #    shard = self.client.get_shard(shard)
        #    shard_latency = shard.latency * 1000

        #    for threshold_ms, emoji in thresholds:
        #        if shard_latency <= threshold_ms:
        #            shard_latency_emoji = emoji
        #            break

        #    embed.add_field(name=f"{shard_latency_emoji} **Shard #{shard.id}**", value=f"{shard_latency:.2f}ms", inline=True)

        embed.add_field(name="⏰ **Uptime**", value=uptime, inline=False)
        await ctx.edit(embed=embed)


    @memberSubCommands.command(name="avatar", description="Shows a members avatar.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def memberavatar(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to show the avatar for.", required=False)):

        user = member or ctx.author

        embed = await db.build_embed(ctx.author.guild, title="<a:Loading:1247220769511964673> Retrieving Avatar", description=f"Retrieving {user.mention}'s avatar...")
        await ctx.respond(embed=embed)

        headers = {
            "Accept": "application/json",
            "content-type": "application/json",
            "Authorization": "Bot " + config["token"]}

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://discord.com/api/users/{user.id}", headers=headers) as a:
                data = await a.json(content_type="application/json")

        is_animated = data["avatar"].startswith("a_")

        gif_url = f"https://cdn.discordapp.com/avatars/{user.id}/{data['avatar']}.gif?size=1024" if is_animated else ""
        png_url = f"https://cdn.discordapp.com/avatars/{user.id}/{data['avatar']}.png?size=1024"

        view = discord.ui.View()
        view_png = discord.ui.Button(label="PNG", url=png_url, style=discord.ButtonStyle.link)
        view.add_item(view_png)
        
        if is_animated:
            view_gif = discord.ui.Button(label="GIF", url=gif_url, style=discord.ButtonStyle.link)
            view.add_item(view_gif)
        
        embed = await db.build_embed(ctx.author.guild, title=f"<a:Folder:1247220756547502160> {user.display_name}'s Avatar")
        embed.set_image(url=user.display_avatar.url)
        await ctx.edit(embed=embed, view=view)


    @commands.slash_command(name="inviteinfo", description="Shows detailed information about an invite.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_permissions(manage_guild=True)
    async def invite_info(self, ctx: discord.ApplicationContext, invite: Option(str, "The invite to retreive information from.", autocomplete=basic_autocomplete(Utils.get_invite_codes))):
        
        try:
            invite = invite.split(" | ")[1]
        except:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"There is no invite with the code **{invite}**.")
            return await ctx.respond(embed=embed, ephemeral=True)
        
        invite_list = await ctx.guild.invites()
        
        for invites in invite_list:
            if invites.code == invite:
                invite = invites
                break

        creation_timestamp = int(invite.created_at.timestamp())
        max_age_timestamp = f"<t:{creation_timestamp + invite.max_age}:d> (<t:{creation_timestamp + invite.max_age}:R>)" if invite.max_age else "Never"
        max_uses = invite.max_uses if invite.max_uses else "No Limit"
        inviter = invite.inviter

        view = discord.ui.View()
        invite_link = discord.ui.Button(label="Link", url=f"https://discord.gg/{invite.code}", style=discord.ButtonStyle.link)
        view.add_item(invite_link)

        embed = await db.build_embed(invite.guild, title="<a:Information:1247223152367636541> Invite Information")
        embed.set_thumbnail(url="")
        embed.add_field(name="Created By", value=inviter.name if inviter else "Unknown", inline=True)
        embed.add_field(name="Code", value=invite.code, inline=True)
        embed.add_field(name="Creation Date", value=f"<t:{creation_timestamp}:d> (<t:{creation_timestamp}:R>)", inline=True)
        embed.add_field(name="Max Uses", value=str(max_uses), inline=True)
        embed.add_field(name="Temporary", value=str(invite.temporary), inline=True)
        embed.add_field(name="Expiration", value=max_age_timestamp, inline=True) 
        await ctx.respond(embed=embed, view=view)


    @commands.slash_command(name="emojiinfo", description="Shows information about an emoji.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def emojiinfo(self, ctx: discord.ApplicationContext, emoji: Option(discord.Emoji, "The emoji to show information about.", required=True)):

        embed = await db.build_embed(ctx.author.guild, title="<a:Loading:1247220769511964673> Retrieving Information", description=f"Retrieving information on **{emoji.name}**...")
        await ctx.respond(embed=embed)

        emoji_values = [
            int(entry["value"].split(":")[2][:-1])
            for entry in ctx.selected_options
            if entry["name"] == "emoji"]
        
        emoji_list = await ctx.guild.fetch_emojis()
        id_in_list = any(emoji.id == emoji_values[0] for emoji in emoji_list)

        if id_in_list:
            embed = await db.build_embed(ctx.author.guild, title="<a:Folder:1247220756547502160> Emoji Information",
                description=f"**Name** ➭ {emoji.name}\n**ID** ➭ {emoji.id}\n**Animated** ➭ {'Yes' if emoji.animated else 'No'}\n"
                + f"**Creation Date** ➭ <t:{int(emoji.created_at.timestamp())}:d> (<t:{int(emoji.created_at.timestamp())}:R>)",)
            
            embed.set_thumbnail(url=emoji.url)
            await ctx.edit(embed=embed)
        else:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="This emoji is not from this server.")
            return await ctx.edit(embed=embed, ephemeral=True)


    @memberSubCommands.command(name="info", description="Shows detailed information about a member.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def memberinfo(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to show information about.", required=False)):
        
        member = member or ctx.author

        embed = await db.build_embed(ctx.author.guild, title="<a:Loading:1247220769511964673> Retrieving Information", description=f"Retrieving information on {member.mention}...")
        await ctx.respond(embed=embed)

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

        badges_list = [
            badge_names[badge.name]
            for badge in member.public_flags.all()
            if badge.name in badge_names]

        badges = ", ".join(badges_list) + "." if badges_list else "None"
        avatar_url = member.display_avatar.url

        roles_list = [role.mention for role in member.roles if role.name != member.guild.default_role.name]

        roles = ", ".join(reversed(roles_list)) + "." if roles_list else "None"
        nickname = member.nick
        highest_role = member.top_role.mention

        permissions_list = [user_permission_names[perm] for perm, value in member.guild_permissions if value and perm in user_permission_names]

        if "Administrator" in permissions_list:
            permissions_list = ["Administrator"]

        permissions = ", ".join(permissions_list) + "." if permissions_list else "None"
        is_boosting = "Yes" if member.premium_since else "No"

        messages = await db.get_leaderboard_data(member, "messages")
        invites = await db.get_leaderboard_data(member, "invited_users")
        cash = await db.get_leaderboard_data(member, "cash")
        rep = await db.get_leaderboard_data(member, "reputation")

        embed = await db.build_embed(ctx.author.guild, title=f"<a:Folder:1247220756547502160> User Information | {member.display_name}")
        embed.set_thumbnail(url=avatar_url)
        embed.set_image(url=banner_url)

        embed.add_field(
            name="**__Main Details__**",
            value=
            f"**Profile** ➭ {member.mention}\n"
            + f"**Username** ➭ {member.name}\n"
            + f"**ID** ➭ {member.id}\n"
            + f"**Badges** ➭ {badges}\n"
            + f"**Creation Date** ➭ <t:{int(member.created_at.timestamp())}:d> (<t:{int(member.created_at.timestamp())}:R>)",
            inline=False)

        embed.add_field(
            name="**__Server Specific__**",
            value=
            f"**Joined** ➭ <t:{int(member.joined_at.timestamp())}:R>\n"
            + f"**Booster** ➭ {is_boosting}\n"
            + f"**Nickname** ➭ {nickname}\n"
            + f"**Highest Role** ➭ {highest_role}",
            inline=False)

        if not member.bot:
            embed.add_field(
                name="**__Server Stats__**",
                value=
                f"**Message Count** ➭ {messages}\n"
                + f"**Reputation** ➭ {rep}\n"
                + f"**Balance** ➭ ${cash}\n"
                + f"**Invites** ➭ {len(invites) if invites != 0 else '0'}",
                inline=False)

        embed.add_field(name="**__Roles__**", value=roles, inline=False)
        embed.add_field(name="**__Permissions__**", value=permissions, inline=False)

        view = discord.ui.View()
        avatar = discord.ui.Button(label="Avatar", url=avatar_url, style=discord.ButtonStyle.link)
        user_url = discord.ui.Button(label="Member URL", url=f"https://discord.com/users/{member.id}", style=discord.ButtonStyle.link)
        view.add_item(avatar)
        view.add_item(user_url)

        await ctx.edit(embed=embed, view=view)


    @commands.slash_command(name="channelinfo", description="Shows detailed information about a channel.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def channelinfo(self, ctx: discord.ApplicationContext, channel: Option(discord.abc.GuildChannel, "The channel to show information about.", required=False)):

        channel = channel or ctx.channel

        try:
            embed = await db.build_embed(ctx.author.guild, title="<a:Loading:1247220769511964673> Retrieving Information", description=f"Retrieving information on the {channel.type} channel {channel.mention}...")
            await ctx.respond(embed=embed)

            permissions_list = []

            for role, overwrite in channel.overwrites.items():
                if isinstance(role, discord.Role):
                    role_permissions = [f"{channel_permission_names.get(perm, perm)}" for perm, value in overwrite if value]
                    
                    if role_permissions:
                        permissions_entry = f"{role.mention}\n{', '.join(role_permissions)}."
                        permissions_list.append(permissions_entry)

            permissions = "\n\n".join(permissions_list) if permissions_list else "None."

            if isinstance(channel, discord.CategoryChannel):
                channel_list = [channel.mention for channel in channel.channels]
                channels = ", ".join(channel_list) + "." if channel_list else "None"

                embed = await db.build_embed(ctx.author.guild, title="<a:Folder:1247220756547502160> Channel Information | Cetegory Channel")
                embed.add_field(name="**__Main Details__**", value=f"**Name** ➭ {channel.name}\n**ID** ➭ {channel.id}\n**NSFW** ➭ {channel.is_nsfw()}\n"
                                                            + f"**Creation Date** ➭ <t:{int(channel.created_at.timestamp())}:d> (<t:{int(channel.created_at.timestamp())}:R>)", inline=False)
                
                embed.add_field(name="**__Channels__**", value=channels, inline=False)
                embed.add_field(name="**__Permissions__**", value=permissions, inline=False)
                    
            
            elif isinstance(channel, discord.TextChannel):
                embed = await db.build_embed(ctx.author.guild, title="<a:Loading:1247220769511964673> Retrieving Information", description=f"Retrieving the message count of the channel {channel.mention}...")
                await ctx.edit(embed=embed)
                messages = await channel.history(limit=None).flatten()
                embed = await db.build_embed(ctx.author.guild, title="<a:Folder:1247220756547502160> Channel Information | Text Channel")
                embed.add_field(name="**__Main Details__**", value=f"**Name** ➭ {channel.name}\n**ID** ➭ {channel.id}\n**NSFW** ➭ {channel.is_nsfw()}\n**Message Count** ➭ {len(messages)}\n"
                    + f"**Description** ➭ {channel.topic if channel.topic else 'None'}\n**Creation Date** ➭ <t:{int(channel.created_at.timestamp())}:d> (<t:{int(channel.created_at.timestamp())}:R>)", inline=False)

                embed.add_field(name="**__Permissions__**", value=permissions, inline=False)


            elif isinstance(channel, discord.VoiceChannel):
                embed = await db.build_embed(ctx.author.guild, title="<a:Folder:1247220756547502160> Channel Information | Voice Channel")
                embed.add_field(name="**__Main Details__**", value=f"**Name** ➭ {channel.name}\n**ID** ➭ {channel.id}\n**Bitrate** ➭ {channel.bitrate}\n"
                    + f"**User Limit** ➭ {channel.user_limit}\n**Creation Date** ➭ <t:{int(channel.created_at.timestamp())}:d> (<t:{int(channel.created_at.timestamp())}:R>)", inline=False)

                embed.add_field(name="**__Permissions__**", value=permissions, inline=False)

            embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else "")
            await ctx.edit(embed=embed)
        except Exception as e:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"An error occured: {e}")
            await ctx.edit(embed=embed)


    @serverSubCommands.command(name="info", description="Shows detailed information about the server.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def serverinfo(self, ctx: discord.ApplicationContext):

        guild = ctx.guild

        embed = await db.build_embed(ctx.author.guild, title="<a:Loading:1247220769511964673> Retrieving Information", description=f"Retrieving information on **{ctx.guild.name}**...")
        await ctx.respond(embed=embed)

        headers = {
            "Accept": "application/json",
            "content-type": "application/json",
            "Authorization": "Bot " + config["token"],
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://discord.com/api/guilds/{guild.id}", headers=headers) as a:
                data = await a.json(content_type="application/json")

        if data["banner"] == None:
            banner_url = ""
        elif data["banner"].startswith("a_"):
            banner_url = f"https://cdn.discordapp.com/banners/{guild.id}/{data['banner']}.gif?size=4096"
        elif data["banner"] != None:
            banner_url = f"https://cdn.discordapp.com/banners/{guild.id}/{data['banner']}.png?size=4096"

        embed = await db.build_embed(ctx.author.guild, title="<a:Folder:1247220756547502160> Server Information")
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else "")
        embed.set_image(url=banner_url)

        embed.add_field(
            name="**__Main Details__**",
            value=f"**Owner** ➭ {guild.owner.mention}\n**Name** ➭ {guild.name}\n**ID** ➭ {guild.id}\n**Verification Level** ➭ {str(guild.verification_level).capitalize()}\n"
            + f"**Description** ➭ {guild.description}\n**Creation Date** ➭ <t:{int(guild.created_at.timestamp())}:d> (<t:{int(guild.created_at.timestamp())}:R>)",
            inline=False)

        embed.add_field(
            name="**__Boost Status__**",
            value=f"**Boost Level** ➭ {guild.premium_tier}\n**Server Boosters** ➭ {len(guild.premium_subscribers)}\n**Server Boosts** ➭ {guild.premium_subscription_count}",
            inline=False)

        embed.add_field(
            name="**__Server Stats__**",
            value=f"**Members** ➭ {guild.member_count}\n**Channels** ➭ {len(guild.channels)}\n"
            + f"**Roles** ➭ {len(guild.roles)}\n**Emojis** ➭ {len(guild.emojis)}\n**Stickers** ➭ {len(guild.stickers)}\n**Bots** ➭ {sum(1 for member in guild.members if member.bot)}",
            inline=False)

        await ctx.edit(embed=embed)


    @serverSubCommands.command(name="icon", description="Retieve the server icon.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def servericon(self, ctx: discord.ApplicationContext):

        guild = ctx.guild

        if not guild.icon:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="This server does not have an icon set.")
            return await ctx.respond(embed=embed, ephemeral=True)

        embed = await db.build_embed(ctx.author.guild, title="<a:Loading:1247220769511964673> Retrieving Server Icon", description=f"Retrieving **{ctx.guild.name}**'s icon...")
        await ctx.respond(embed=embed)

        embed = await db.build_embed(ctx.author.guild, title=f"<a:Folder:1247220756547502160> Server Icon | {guild.name}")
        embed.set_image(url=guild.icon.url)
        await ctx.edit(embed=embed)


    @serverSubCommands.command(name="banner", description="Retieve the server banner.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def serverbanner(self, ctx: discord.ApplicationContext):

        guild = ctx.guild

        if not guild.banner:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="This server does not have a banner set.")
            return await ctx.respond(embed=embed, ephemeral=True)

        embed = await db.build_embed(ctx.author.guild, title="<a:Loading:1247220769511964673> Retrieving Server Banner", description=f"Retrieving **{ctx.guild.name}**'s banner...")
        await ctx.respond(embed=embed)

        embed = await db.build_embed(ctx.author.guild, title=f"<a:Folder:1247220756547502160> Server Banner | {guild.name}")
        embed.set_image(url=guild.banner.url)
        await ctx.edit(embed=embed)


    @serverSubCommands.command(name="members", description="Retrieve the server member count.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def servermembers(self, ctx: discord.ApplicationContext):

        guild = ctx.guild

        embed = await db.build_embed(ctx.author.guild, title="<a:Folder:1247220756547502160> Member Count", description=f"**{guild.name}** has a total of **{guild.member_count}** members!")
        embed.set_thumbnail(url=guild.icon.url if guild.icon else "")
        await ctx.respond(embed=embed)


    @serverSubCommands.command(name="emojis", description="Retrieve all the server's emojis.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def serveremotes(self, ctx: discord.ApplicationContext):

        guild = ctx.guild

        emoji_list = [f"{emote} | `{emote}`" for emote in guild.emojis]

        max_emotes_per_page = 10

        if len(emoji_list) <= max_emotes_per_page:
            embed = await db.build_embed(ctx.author.guild, title=f"<a:Folder:1247220756547502160> Emoji List | {guild.name}", description="\n".join(emoji_list))
            embed.set_thumbnail(url=guild.icon.url if guild.icon else "")
            return await ctx.respond(embed=embed)
        else:
            emoji_pages = [emoji_list[i : i + max_emotes_per_page] for i in range(0, len(emoji_list), max_emotes_per_page)]

            emoji_embeds = []

            for page_index, page_data in enumerate(emoji_pages, start=1):
                embed = await db.build_embed(ctx.guild, title=f"<a:Folder:1247220756547502160> Emoji List | {guild.name}", description="\n".join(page_data))
                embed.set_thumbnail(url=guild.icon.url if guild.icon else "")
                emoji_embeds.append(embed)

            paginator = pages.Paginator(pages=emoji_embeds, disable_on_timeout=True, use_default_buttons=False, show_indicator=True, loop_pages=True, timeout=60)
            if len(emoji_embeds) > 10:
                paginator.add_button(pages.PaginatorButton("first", label="", emoji="<a:First:1182373753498370069>", style=discord.ButtonStyle.grey))
            paginator.add_button(pages.PaginatorButton("prev", label="", emoji="<a:LeftArrow:1156039371624026112>", style=discord.ButtonStyle.grey))
            paginator.add_button(pages.PaginatorButton("page_indicator", style=discord.ButtonStyle.gray, disabled=True))
            paginator.add_button(pages.PaginatorButton("next", label="", emoji="<a:RightArrow:1156039369875001385>", style=discord.ButtonStyle.grey))
            if len(emoji_embeds) > 10:
                paginator.add_button(pages.PaginatorButton("last", label="", emoji="<a:Last:1182374111306063902>", style=discord.ButtonStyle.grey))
            await paginator.respond(ctx.interaction)


def setup(client):
    client.add_cog(information(client))