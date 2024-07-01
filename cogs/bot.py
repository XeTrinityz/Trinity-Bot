# Discord Imports
from discord.utils import basic_autocomplete
from discord.ext import commands, pages
from discord import Option
import discord

# Standard / Third-Party Library Imports
import aiohttp
import os

# Local Module Imports
from EmbedBuilder.embedTool import EmbedToolView
from utils.database import Database
from utils.lists import *
from Bot import config, is_blocked

db = Database()

class bot(commands.Cog):
    def __init__(self, client):
        self.client = client

    class URLButton(discord.ui.View):
        def __init__(self, text, query: str):
            super().__init__()
            url = query
            self.add_item(discord.ui.Button(label=text, emoji="🔗", url=url))

    adminSubCommands = discord.SlashCommandGroup("admin", "Leave, Restart, Invite, List", default_member_permissions=discord.Permissions(administrator=True), guild_ids=[1245718097164374036])
    botSubCommands = discord.SlashCommandGroup("bot", "Info, Invite.")


    @adminSubCommands.command(name="reload", description="Reloads a cog.")
    @commands.check(is_blocked)
    @commands.is_owner()
    @discord.default_permissions(administrator=True)
    async def reload(self, ctx: discord.ApplicationContext, cog: Option(str, "The cog to reload.", choices=["automod", "bot", "configuration", "economy", "fun", "giveaways", "images", "information", "leaderboard", "listener", "moderation", "music", "roles", "tickets", "utility", "verification", "woocommerce"], required=True)):

        embed = await db.build_embed(ctx.author.guild, title="<a:Loading:1247220769511964673> Reloading Cog", description=f"Reloading the **{cog}** cog...")
        await ctx.respond(embed=embed)

        try:
            self.client.reload_extension(f"cogs.{cog}")
        except Exception as e:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Cog Reload Failed", description=f"An error occured: {e}")
            await ctx.edit(embed=embed)
        else:
            embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Cog Reloaded", description=f"The **{cog}** cog has been reloaded.")
            await ctx.edit(embed=embed)


    @adminSubCommands.command(name="status", description="Set the bots status.")
    @discord.default_permissions(administrator=True)
    @commands.is_owner()
    async def status(self, ctx, appearance: Option(str, "The bots online appearance.", choices=["Online", "Do Not Disturb", "Idle", "Invisible", "Offline"]), activity: Option(str, "The status activity.", choices=["Playing", "Watching", "Listening", "None"]), status: Option(str, "The status for the bot to change to")):
        
        await ctx.defer()
        try:
            appearance_map = {
                "Online": discord.Status.online,
                "Do Not Disturb": discord.Status.dnd,
                "Idle": discord.Status.idle,
                "Invisible": discord.Status.invisible,
                "Offline": discord.Status.offline,
            }

            if activity == "Playing":
                await self.client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=status), status=appearance_map[appearance])
            elif activity == "Watching":
                await self.client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=status), status=appearance_map[appearance])
            elif activity == "Listening":
                await self.client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=status), status=appearance_map[appearance])
            elif activity == "None":
                await self.client.change_presence(activity=discord.CustomActivity(name=status), status=appearance_map[appearance])

            await db.update_single_value_in_table("global_settings", "ARG1", "Feature", "STATUS", appearance)
            await db.update_single_value_in_table("global_settings", "ARG2", "Feature", "STATUS", activity)
            await db.update_single_value_in_table("global_settings", "ARG3", "Feature", "STATUS", status)
            
            embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Bot Status Updated", description=f"The bots status has been set to `{appearance} > {activity} > {status}`.")
            await ctx.respond(embed=embed)
        
        except Exception as a:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=a)
            return await ctx.respond(embed=embed)


    @adminSubCommands.command(name="leaveserver", description="Leaves a server the bot is in.")
    @discord.default_permissions(administrator=True)
    @commands.is_owner()
    async def leaveserver(self, ctx: discord.ApplicationContext, server_name: Option(str, "The server to leave.", autocomplete=basic_autocomplete(bot_servers))):

        opening_parenthesis = server_name.find("(")
        closing_parenthesis = server_name.find(")")

        if opening_parenthesis != -1 and closing_parenthesis != -1:
            extracted_server_name = server_name[:opening_parenthesis].strip()
            extracted_value = int(server_name[opening_parenthesis + 1 : closing_parenthesis])

            guild_to_leave = discord.utils.get(self.client.guilds, id=extracted_value)

            if guild_to_leave:
                await guild_to_leave.leave()
                embed = await db.build_embed(ctx.author.guild, title=f"🚪 {extracted_server_name}", description=f"{self.client.user.name} has left {extracted_server_name}.")
                await ctx.respond(embed=embed)


    @botSubCommands.command(name="invite", description="Generates an invite link for the bot.")
    @commands.check(is_blocked)
    async def botnvite(self, ctx: discord.ApplicationContext):

        embed = await db.build_embed(ctx.author.guild, title="📩 Bot Invite", description="Click the button below to invite the bot to your server.")
        await ctx.respond(embed=embed,
            view=self.URLButton("Invite", f"https://discord.com/api/oauth2/authorize?client_id={self.client.user.id}&permissions=8&scope=bot"))


    @adminSubCommands.command(name="serverlist", description="Lists all servers the bot is in.")
    @discord.default_permissions(administrator=True)
    @commands.is_owner()
    async def serverlist(self, ctx: discord.ApplicationContext):

        servers = self.client.guilds
        serverList = [f"**Guild** ➭ {server.name}\n**ID** ➭ {server.id}\n**Owner** ➭ {server.owner.name} ``({server.owner.id})``\n**Members** ➭ {server.member_count}\n" for server in servers]

        max_users_per_page = 10

        if len(serverList) <= max_users_per_page:
            embed = await db.build_embed(ctx.author.guild, title="📋 Server List", description="\n".join(map(str, serverList)))
            return await ctx.respond(embed=embed)

        server_pages = [serverList[i : i + max_users_per_page] for i in range(0, len(serverList), max_users_per_page)]

        embed_pages = []

        for page in server_pages:
            server_page = await db.build_embed(ctx.author.guild, title="📋 Server List", description="\n".join(map(str, page)))
            embed_pages.append(server_page)

        paginator = pages.Paginator(pages=embed_pages, disable_on_timeout=True, use_default_buttons=False, show_indicator=True, loop_pages=True, timeout=60)
        if len(embed_pages) > 10:
            paginator.add_button(pages.PaginatorButton("first", label="", emoji="<a:First:1182373753498370069>", style=discord.ButtonStyle.grey))
        paginator.add_button(pages.PaginatorButton("prev", label="", emoji="<a:LeftArrow:1156039371624026112>", style=discord.ButtonStyle.grey))
        paginator.add_button(pages.PaginatorButton("page_indicator", style=discord.ButtonStyle.gray, disabled=True))
        paginator.add_button(pages.PaginatorButton("next", label="", emoji="<a:RightArrow:1156039369875001385>", style=discord.ButtonStyle.grey))
        if len(embed_pages) > 10:
            paginator.add_button(pages.PaginatorButton("last", label="", emoji="<a:Last:1182374111306063902>", style=discord.ButtonStyle.grey))
        await paginator.respond(ctx.interaction)


    @adminSubCommands.command(name="username", description="Set the bots username.")
    @discord.default_permissions(administrator=True)
    @commands.is_owner()
    async def username(self, ctx, username: Option(str, "The username for the bot to change to")):
        await ctx.defer()
        try:
            await self.client.user.edit(username=username)
        
        except Exception as a:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=a)
            return await ctx.respond(embed=embed)

        embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Bot Username Updated", description=f"The bots username has been set to `{username}`.")
        await ctx.respond(embed=embed)


    @adminSubCommands.command(name="serverinfo", description="Get information from a server the bot is in.")
    @discord.default_permissions(administrator=True)
    @commands.is_owner()
    async def a_serverinfo(self, ctx: discord.ApplicationContext, guild: Option(str, "The guild ID to retreive information on.")):
      
        try:
            guild = self.client.get_guild(int(guild))
        except discord.NotFound:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="This guild ID either does not exist or the bot is not in the server.")
            return await ctx.respond(embed=embed)

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
        embed.set_thumbnail(url=guild.icon.url if guild.icon else "")
        embed.set_image(url=banner_url)

        try:
            try:
                vanity = await guild.vanity_invite()
                if vanity is not None:
                    invite = vanity.code
            except:
                invite = await guild.invites()
                invite = invite[0].code
        except:
            invite= None

        embed.add_field(
            name="**__Main Details__**",
            value=f"**Owner** ➭ {guild.owner.mention}\n**Name** ➭ [{guild.name}](https://discord.gg/{invite})\n**ID** ➭ {guild.id}\n**Verification Level** ➭ {str(guild.verification_level).capitalize()}\n"
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


    @adminSubCommands.command(name="avatar", description="Set the bots avatar.")
    @discord.default_permissions(administrator=True)
    @commands.is_owner()
    async def botavatar(self, ctx, image: Option(discord.Attachment, "The avatar for the bot to change to")):

        try:
            await image.save(image.filename)
            with open(f"./{image.filename}", "rb") as i:
                await self.client.user.edit(avatar=i.read())
            os.remove(f"./{image.filename}")
        
        except Exception as a:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=a)
            return await ctx.respond(embed=embed)

        embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Bot Avatar Updated", description=f"The bots avatar has been set to")
        embed.set_image(url=image.url)
        await ctx.respond(embed=embed)


    @adminSubCommands.command(name="clean", description="Clean the database of all guilds the bot is not in.")
    @discord.default_permissions(administrator=True)
    @commands.is_owner()
    async def clean_db(self, ctx: discord.ApplicationContext):

        try:
            embed = await db.build_embed(ctx.author.guild, title="<a:Loading:1247220769511964673> Cleaning Database", description="Removing all unused server IDs...")
            await ctx.respond(embed=embed)
            
            guilds = [guild.id for guild in self.client.guilds]
            
            result = await db.clean_unused_servers(guilds)

            deleted_configurations = result['deleted_configurations']
            deleted_leaderboard_stats = result['deleted_leaderboard_stats']

            embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Database Cleaned", description=f"The bot removed **{deleted_configurations}** guild IDs from the ServerConfigurations table and **{deleted_leaderboard_stats}** guild IDs from the LeaderboardStats table.")
            await ctx.edit(embed=embed)

        except Exception as a:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=str(a))
            return await ctx.edit(embed=embed)


    @adminSubCommands.command(name="reset", description="Reset all values of the specified feature.")
    @discord.default_permissions(administrator=True)
    @commands.is_owner()
    async def reset_db(self, ctx: discord.ApplicationContext, feature: Option(str, "The feature to reset.")):

        try:
            embed = await db.build_embed(ctx.author.guild, title="<a:Loading:1247220769511964673> Resetting Feature", description=f"Resetting all **{feature}** settings to default...")
            await ctx.respond(embed=embed)

            guilds = []
            for guild in self.client.guilds:
                guilds.append(guild.id)
                
            reset = await db.set_default_values(feature)
            if reset:
                embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} {feature} Reset", description=f"The bot successfully set all {feature} features to default.")
                await ctx.edit(embed=embed)
            else:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Failed")
                return await ctx.edit(embed=embed)

        except Exception as a:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=a)
            return await ctx.edit(embed=embed)


    @adminSubCommands.command(name="block", description="Block a user or guild for using the bot.")
    @discord.default_permissions(administrator=True)
    @commands.is_owner()
    async def block(self, ctx: discord.ApplicationContext, user_guild: Option(str, "Block a user or guild.", choices=["User", "Guild"]), id: Option(str, "The user/guild ID to block."), bool: Option(bool, "Block or unblock.")):

        try:
            embed = await db.build_embed(ctx.author.guild, title=f"<a:Loading:1247220769511964673> Blocking {user_guild}", description=f"Blocking the {user_guild} ID from the bot...")
            await ctx.respond(embed=embed)
                
            if bool:
                if user_guild == "User":
                    blacklist.append(int(id))
                else:
                    blacklist_guilds.append(int(id))
            else:
                if user_guild == "User":
                    blacklist.remove(int(id))
                else:
                    blacklist_guilds.remove(int(id))
                
            await db.append_ids_to_lists("global_settings", user_guild.lower()+"s", "FEATURE", "BLOCKED")
                    
            embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} {user_guild} Blocked", description=f"The {user_guild} has been blocked from using the bot.")
            await ctx.edit(embed=embed)

        except Exception as a:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=str(a))
            return await ctx.edit(embed=embed)


    @adminSubCommands.command(name="announce", description="Make an announcement to all server owners.")
    @discord.default_permissions(administrator=True)
    @commands.is_owner()
    async def admin_announce(self, ctx: discord.ApplicationContext):

        user_embed = await db.build_embed(ctx.author.guild, title=f"Embed Builder", description=f"Click the buttons below to build your embed.")
        embed_tool = EmbedToolView(channel_or_message=None, is_new_embed=True, custom=f"admin_announcement", view=None, ctx=ctx)
        await ctx.respond(embed=user_embed, view=embed_tool, ephemeral=True)


    @adminSubCommands.command(name="restart", description="Restart the bot.")
    @discord.default_permissions(administrator=True)
    @commands.is_owner()
    async def restart(self, ctx):

        apikey = "ptlc_7NdW3jZVZiGkGwNfL5wRzaIJatQ7qBdn8DLL8HfmsT5"

        req_data = {"signal": "restart"}

        headers = {
            "Accept": "application/json",
            "content-type": "application/json",
            "Authorization": "Bearer " + apikey}

        embed = await db.build_embed(ctx.author.guild, title=f"🔄 Bot Restarting", description="The bot is restarting and will be back up soon.")
        await ctx.respond(embed=embed)

        activity = discord.Activity(type=discord.ActivityType.playing, name="Restarting...")
        await self.client.change_presence(status=discord.Status.idle, activity=activity)

        async with aiohttp.ClientSession() as session:
            async with session.post(f"https://control.sparkedhost.us/api/client/servers/089c524f/power", json=req_data, headers=headers) as a:
                pass


    @botSubCommands.command(name="info", description="Information about the bot.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def botinfo(self, ctx):
        
        await ctx.defer()

        apikey = "ptlc_gXzlr1bE0aSFYIQFIcroH2tLmdhwubA5LvDI5gdaLA6"

        headers = {
            "Accept": "application/json",
            "content-type": "application/json",
            "Authorization": "Bearer " + apikey,}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://control.sparkedhost.us/api/client/servers/089c524f", headers=headers) as a:
                data = await a.json(content_type="application/json")

        cpu_usage = data.get("attributes", {}).get("limits", {}).get("cpu", "N/A")
        disk_usage = data.get("attributes", {}).get("limits", {}).get("disk", "N/A")
        memory_usage = (data.get("attributes", {}).get("limits", {}).get("memory", "N/A"))

        command_list = []
        for command in self.client.walk_application_commands():
            command_list.append(command.name)
        
        commands = len(command_list)
        guilds = len(self.client.guilds)
        total_members = sum([guild.member_count for guild in self.client.guilds])

        bot_user = self.client.user

        discord_py_version = discord.__version__

        system_info = (
            f"Server Location          :: Buffalo, New York\n"
            f"Server OS                :: Linux\n\n"
            f"System CPU Limit         :: {cpu_usage}%\n"
            f"System RAM Limit         :: {memory_usage}\n"
            f"System Disk Limit        :: {disk_usage}\n\n"
            
            f"Total Commands           :: {commands}\n"
            f"Background Tasks         :: 3\n\n"

            f"Total Servers            :: {guilds}\n"
            f"Total Members            :: {total_members}\n"
            )

        embed = await db.build_embed(ctx.author.guild, title="🤖 Bot Information",
            description=f"{self.client.user.mention} is an All-Purpose Discord Bot and is your go-to solution for a wide range of server management needs. From creating and managing support tickets to handling moderation tasks, this bot offers a seamless and user-friendly experience.\n\n"
            + "**Developer** ➭ [XeTrinityz](https://discord.com/users/1077671579187675197)\n**Language** ➭ [Python](https://www.python.org/)\n**Library** ➭ [Pycord](https://pycord.dev/)\n**Database** ➭ [MySQL](https://www.mysql.com/)\n")
        embed.set_thumbnail(url=bot_user.display_avatar.url)

        view = discord.ui.View()
        website = discord.ui.Button(label="Website", url="https://xetrinityz.com/", style=discord.ButtonStyle.link)
        docs = discord.ui.Button(label="Documentation", url="https://docs.xetrinityz.com/", style=discord.ButtonStyle.link)
        discord_ = discord.ui.Button(label="Support Server", url="https://discord.gg/X", style=discord.ButtonStyle.link)
        invite = discord.ui.Button(label="Bot Invite", url=f"https://discord.com/api/oauth2/authorize?client_id=1167583910931206276&permissions={self.client.user.id}&scope=applications.commands%20bot", style=discord.ButtonStyle.link)
        view.add_item(website)
        view.add_item(docs)
        view.add_item(discord_)
        view.add_item(invite)

        embed.add_field(name="Bot Name", value=bot_user.name, inline=True)
        embed.add_field(name="Bot ID", value=bot_user.id, inline=True)
        embed.add_field(name="Library Version", value=f"Py-Cord {discord_py_version}", inline=True)
        embed.add_field(name="", value=f"```asciidoc\n{system_info}\n```", inline=False)

        await ctx.respond(embed=embed, view=view)

def setup(client):
    client.add_cog(bot(client))
