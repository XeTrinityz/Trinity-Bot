# Discord Imports
from discord.ext import commands
from discord import Option
import discord

# Standard / Third-Party Library Imports
import json

# Local Module Imports
from utils.views import verificationButton, verificationCaptcha
from utils.database import Database
from Bot import is_blocked
from utils.lists import *
from EmbedBuilder.embedTool import EmbedToolView

db = Database()
    
# COG CLASS
# ---------
class verification(commands.Cog):
    def __init__(self, client):
        self.client = client

    verify = discord.SlashCommandGroup("verify", "Math, CAPTCHA.", default_member_permissions=discord.Permissions(manage_channels=True))

    # COMMANDS
    # --------
    @verify.command(name="math", description="Sends a math based verification system.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @discord.default_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_guild_permissions(manage_roles=True)
    async def start_verification(self, ctx: discord.ApplicationContext, channel: Option(discord.TextChannel, "The channel to send the verification panel to.", required=True)):

        roles = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "ROLES")

        if roles:
            roles = json.loads(roles)
            role = roles.get("verified_role")

        if role is None:
            embed = await db.build_embed( ctx.author.guild, title=f"{error_emoji} Request Failed", description="You need to configure a verification role first.")
            await ctx.respond(embed=embed, ephemeral=True)
        else:
            user_embed = await db.build_embed(ctx.author.guild, title=f"Embed Builder", description=f"Click the buttons below to build your verification embed.")
            embed_tool = EmbedToolView(channel_or_message=channel, is_new_embed=True, custom=None, view=verificationButton(), ctx=ctx)
            await ctx.respond(embed=user_embed, view=embed_tool, ephemeral=True)


    @verify.command(name="captcha", description="Sends a captcha based verification system.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @discord.default_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_guild_permissions(manage_roles=True)
    async def start_capthca_verification(self, ctx: discord.ApplicationContext, channel: Option(discord.TextChannel, "The channel to send the verification panel to.", required=True)):

        roles = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "ROLES")

        if roles:
            roles = json.loads(roles)
            role = roles.get("verified_role")

        if role is None:
            embed = await db.build_embed( ctx.author.guild, title=f"{error_emoji} Request Failed", description="You need to configure a verification role first.")
            await ctx.respond(embed=embed, ephemeral=True)
        else:
            user_embed = await db.build_embed(ctx.author.guild, title=f"Embed Builder", description=f"Click the buttons below to build your verification embed.")
            embed_tool = EmbedToolView(channel_or_message=channel, is_new_embed=True, custom=None, view=verificationCaptcha(), ctx=ctx)
            await ctx.respond(embed=user_embed, view=embed_tool, ephemeral=True)


# LOAD COG
# --------
def setup(client):
    client.add_cog(verification(client))