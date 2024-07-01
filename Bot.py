# -----------------------------------------------------------
# ---------------- Trinity Bot by XeTrinityz ----------------
# ------------------------ Py-Cord --------------------------
# -----------------------------------------------------------

# Discord Imports
from discord.ext import commands
import discord

# Third-Party Library Imports
import json
import os

# Local Module Imports
from utils.database import Database
from utils.views import Views
from utils.lists import *

with open("./config.json", "r") as cjson:
    config = json.load(cjson)

intents = discord.Intents.all()
intents.presences = False

client = discord.AutoShardedBot(intents=intents, owner_ids=set(config["ownerIDS"]))

db = Database()
views = Views(client)

# Restrict Access
async def is_blocked(ctx: discord.ApplicationContext):
    if ctx.author.id in blacklist:
        bot_logs = discord.utils.get(client.get_all_channels(), id=1158538017208807465)
        embed = await db.build_embed(ctx.author.guild, title="")
        embed.add_field(name="<a:Banned:1247220734233804831> Blocked User", value=f"**Command** ➭ {ctx.command}\n**User** ➭ {ctx.author.mention}\n**Server** ➭ {ctx.guild.name}\n**Channel** ➭ {ctx.channel.name}", inline=False)
        await bot_logs.send(embed=embed)

        blocked_embed = await db.build_embed(ctx.author.guild, title="<a:Banned:1247220734233804831> Blocked", description="Your access to the bot has been permanently suspended due to a violation of our terms of service.")
        view = discord.ui.View()
        appeal_url = discord.ui.Button(label="Appeal", url=f"https://discord.gg/X", style=discord.ButtonStyle.link)
        view.add_item(appeal_url)
        await ctx.respond(embed=blocked_embed, view=view, ephemeral=True)
        return
    else:
        return ctx.command
    

@client.slash_command(name="help", description="Lists commands from each category.")
@commands.check(is_blocked)
@commands.guild_only()
async def help(ctx: discord.ApplicationContext):

    embed = await db.build_embed(ctx.author.guild, title="<a:Folder:1247220756547502160> Help Command", description=
                                f"> Use the dropdown menu below to pick a command category!\n\n"

                                +f"<a:Information:1247223152367636541> **Quick Tips**\n"
                                +f"- You can use </configure embed:1174737712473985123> to customize the bot embeds to your liking.\n"
                                +f"- You can use </reportbug:1174737712834674724> to report any bugs you find.\n"
                                +f"- You can use </ping:1174737712834674725> to check the bot's latency and uptime.\n"
                                +f"- You can join the support server to suggest new features and commands.\n\n"
                            
                                +">>> <:Trinity:1247267782375116982> Website ➭ https://xetrinityz.com\n"
                                +"<:Trinity:1247267782375116982> Documentation ➭ https://docs.xetrinityz.com\n"
                                +"<:Trinity:1247267782375116982> Privacy Policy ➭ https://xetrinityz.com/PrivacyPolicy\n"
                                +"<:Trinity:1247267782375116982> Terms of Service ➭ https://xetrinityz.com/TOS\n"
                                +"<:Trinity:1247267782375116982> Support Server ➭ https://discord.gg/X\n"
                                +"<:Trinity:1247267782375116982> Invite ➭ [Click Here](https://discord.com/api/oauth2/authorize?client_id=1167583910931206276&permissions=10017947774206&scope=applications.commands%20bot)\n"
                                 )
    
    embed.set_thumbnail(url="")
    await ctx.respond(embed=embed, view=views.HelpCommand())


# LOAD cogs
# ---------
for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        client.load_extension(f"cogs.{filename[:-3]}")

# RUN
# ---
client.run(config["token"])