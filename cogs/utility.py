# Discord Imports
from discord.utils import basic_autocomplete
from discord_webhook import DiscordWebhook
from discord.ext import commands
from discord import Option
import discord

# Third-Party Library Imports
from googletrans import Translator, LANGUAGES
from datetime import datetime, timedelta
from urllib.parse import quote
from PIL import Image
import validators
import aiohttp
import random
import string
import json
import io
import re
import os

# Local Module Imports
from EmbedBuilder.embedTool import EmbedToolView
from EmbedBuilder.general import ContentModal
from utils.database import Database
from utils.functions import Utils
from utils.views import Views
from Bot import is_blocked, config
from utils.lists import *

db = Database()

# COG CLASS
# ---------
class say(commands.Cog):
    def __init__(self, client):
        self.client = client

    buttonSubCommands = discord.SlashCommandGroup("button", "Add Links, Add Role, Remove", default_member_permissions=discord.Permissions(administrator=True))
    buttonAddSubCommands = buttonSubCommands.create_subgroup("add", "Role, URL")
    triggerSubCommands = discord.SlashCommandGroup("autoresponse", "Add, Remove, Edit, Clear, List.", default_member_permissions=discord.Permissions(manage_messages=True))
    reminderSubCommands = discord.SlashCommandGroup("reminder", "Create, Remove, Clear, List.")
    searchSubCommands = discord.SlashCommandGroup("search", "Google, Lyrics, IMBD, iTunes, Urban.")
    saySubCommands = discord.SlashCommandGroup("say", "Embed Builder, Normal, Reply, Edit, Sticky, Webhook Embed, Webhook Edit, Webhook Impersonate.", default_member_permissions=discord.Permissions(administrator=True))
    saywebhook = saySubCommands.create_subgroup("webhook", "Normal, Edit, Embed, impersonate.")
    webhookSubCommands = discord.SlashCommandGroup("webhook", "Create, Delete.", default_member_permissions=discord.Permissions(manage_webhooks=True))
    addSubCommands = discord.SlashCommandGroup("add", "Emoji, Sticker.", default_member_permissions=discord.Permissions(manage_emojis=True))
    channelSubCommands = discord.SlashCommandGroup("channel", "Clone, Delete, Rename, Slowmode, NSFW.", default_member_permissions=discord.Permissions(manage_channels=True))
    inviteSubCommands = discord.SlashCommandGroup("invite", "Create, Delete.", default_member_permissions=discord.Permissions(manage_guild=True))

    @commands.message_command(name="Translate Message", description="Translate a members message.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def translate_message(self, ctx: discord.ApplicationContext, message: discord.Message):

        if message.embeds:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Embeds cannot be translated.")
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        try:
            translator = Translator()

            # Attempt language detection
            detected_language = None
            try:
                detected_language = translator.detect(message.content).lang
            except:
                detected_language = "en"

            # Check if the detected language is supported
            if detected_language not in LANGUAGES:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Unsupported language.")
                await ctx.edit(embed=embed)
                return

            translated_message = translator.translate(message.content, src=detected_language, dest="en")

            embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Translating", description=f"Translating to English...")
            await ctx.respond(embed=embed)

            embed = await db.build_embed(ctx.author.guild, title=f"🌐 Text Translated | English", description=translated_message.text)
            await ctx.edit(embed=embed)
        except:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The message could not be translated.")
            await ctx.edit(embed=embed)


    @commands.message_command(name="Add Emoji", description="Save an emoji to the server.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @discord.default_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def emoji_message(self, ctx: discord.ApplicationContext, message: discord.Message):

        embed = await db.build_embed(ctx.author.guild, title="<a:Loading:1247220769511964673> Adding Emoji", description="Adding emoji(s) to the server...")
        await ctx.respond(embed=embed)

        try:
            emojis = re.findall(r'<a?(:\w+:\d+)>', message.content)
            if not emojis:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="There are no emojis in the provided message.")
                return await ctx.edit(embed=embed)

            emoji_count = 0
            for emoji in emojis:
                emoji_id = int(emoji.split(":")[2])
                emoji_name = emoji.split(":")[1]

                emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(emoji_url) as response:
                        if response.status == 200:
                            emoji_bytes = await response.read()
                        else:
                            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Failed to get emoji bytes.")
                            return await ctx.edit(embed=embed)

                if emoji_count <= 5:
                    new_emoji = await ctx.guild.create_custom_emoji(name=emoji_name, image=emoji_bytes)
                    emoji_count += 1
                else:
                    embed = await db.build_embed(ctx.author.guild, title=":ninja: Emoji Added", description=f"The emoji **{emoji_name}** has been added to the server.")
                    embed.set_thumbnail(url=new_emoji.url)
                    return await ctx.edit(embed=embed)

                embed = await db.build_embed(ctx.author.guild, title=":ninja: Emoji Added", description=f"The emoji **{emoji_name}** has been added to the server.")
                embed.set_thumbnail(url=new_emoji.url)
                await ctx.edit(embed=embed)

        except:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The emoji could not be added to the server.")
            await ctx.edit(embed=embed)


    @commands.message_command(name="Add Sticker", description="Save a sticker to the server.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @discord.default_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def sticker_message(self, ctx: discord.ApplicationContext, message: discord.Message):

        try:
            if message.stickers:
                sticker_data = message.stickers[0]
                sticker_id = sticker_data.id
                sticker_name = sticker_data.name
                
                embed = await db.build_embed(ctx.author.guild, title="<a:Loading:1247220769511964673> Adding Sticker", description=f"Adding **{sticker_name}** to the server...")
                await ctx.respond(embed=embed)

                sticker_url = f"https://cdn.discordapp.com/stickers/{sticker_id}.png"
                async with aiohttp.ClientSession() as session:
                    async with session.get(sticker_url) as response:
                        if response.status == 200:
                            sticker_bytes = await response.read()
                        else:
                            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The sticker could not be added to the server.")
                            await ctx.edit(embed=embed)
                            return

                sticker_file = discord.File(io.BytesIO(sticker_bytes), filename=f"{sticker_name}.png")

                await ctx.guild.create_sticker(name=sticker_name, description="Added with Trinity Bot", emoji="🐱‍👤", file=sticker_file)

                embed = await db.build_embed(ctx.author.guild, title=":ninja: Sticker Added", description=f"The sticker **{sticker_name}** has been added to the server.")
                embed.set_thumbnail(url=sticker_url)
                await ctx.edit(embed=embed)
            else:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="There is no sticker in the provided message.")
                await ctx.respond(embed=embed, ephemeral=True)

        except discord.HTTPException as e:
            if e.status == 400 and e.code == 30039:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The maximum number of stickers has been reached.")
            else:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The sticker could not be added to the server.")
            await ctx.edit(embed=embed)

        except Exception as e:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The sticker could not be added to the server.")
            await ctx.edit(embed=embed)


    @saySubCommands.command(name="embedbuilder", description="Sends an embed to the specified channel.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def embed_send(self, ctx: discord.ApplicationContext, channel: Option(discord.TextChannel, "The channel to send the embed to."), template: Option(str, "The link of the embed. (Right click the message and select 'Copy Message Link')", required=False)):

        try:
            message = None
            if template:
                pattern = r"https://(?:canary\.|ptb\.|)discord(?:app)?\.com/channels/(\d+)/(\d+)/(\d+)"
                match = re.search(pattern, template)

                if not match:
                    embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The message link you provided was incorrect. Make sure to right click the message and select 'Copy Message Link'.")
                    await ctx.respond(embed=embed, ephemeral=True)
                    return

                message_link_parts = template.split('/')
                channel_id = int(message_link_parts[-2])
                message_id = int(message_link_parts[-1])
                msg_channel = ctx.guild.get_channel(channel_id)
                message = await msg_channel.fetch_message(message_id)
                
                if not message.embeds:
                    embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The provided message did not contain an embed.")
                    await ctx.respond(embed=embed, ephemeral=True)
                    return

                user_embed = message.embeds[0]
            else:
                user_embed = await db.build_embed(ctx.author.guild, title=f"Embed Builder", description=f"Click the buttons below to build your embed.")

            embed_tool = EmbedToolView(channel_or_message=channel, is_new_embed=True, view=None, custom=None, ctx=ctx)
            await ctx.respond(content=message.content if message else None, embed=user_embed, view=embed_tool, ephemeral=True)

        except discord.NotFound:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The specified message could not be found.")
            await ctx.respond(embed=embed, ephemeral=True)

        except discord.Forbidden:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="I do not have the necessary permissions to edit this message.")
            await ctx.respond(embed=embed, ephemeral=True)

        except discord.HTTPException:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="An unexpected HTTP error occurred.")
            await ctx.respond(embed=embed, ephemeral=True)


    @channelSubCommands.command(name="clone", description="Clone a channel.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_guild_permissions(manage_channels=True)
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def clone_channel(self, ctx: discord.ApplicationContext, channel: Option(discord.TextChannel | discord.VoiceChannel, "The channel to clone.")):

        position = channel.position
        new_channel = await channel.clone()
        await new_channel.edit(position=position+1)
        embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Channel Cloned", description=f"The {new_channel.mention} was created successfully.")
        await ctx.respond(embed=embed)


    @channelSubCommands.command(name="delete", description="Delete a channel.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_guild_permissions(manage_channels=True)
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def delete_channel(self, ctx: discord.ApplicationContext, channel: Option(discord.abc.GuildChannel, "The channel to delete.")):

        await channel.delete()
        embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Channel Deleted", description=f"The **{channel.name}** was deleted successfully.")
        await ctx.respond(embed=embed)


    @channelSubCommands.command(name="rename", description="Rename a channel.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_guild_permissions(manage_channels=True)
    @commands.cooldown(2, 600, commands.BucketType.member)
    async def rename_channel(self, ctx: discord.ApplicationContext, channel: Option(discord.abc.GuildChannel, "The channel to delete."), name: Option(str, "The new name of the channel.")):
        
        original_name = channel.name
        await channel.edit(name=name)
        embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Channel Renamed", description=f"The **{original_name}** channel was renamed to **{name}** successfully.")
        await ctx.respond(embed=embed)


    @channelSubCommands.command(name="nsfw", description="Enable or disable a channel as nsfw.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_guild_permissions(manage_channels=True)
    @commands.cooldown(2, 600, commands.BucketType.member)
    async def nsfw_channel(self, ctx: discord.ApplicationContext, channel: Option(discord.TextChannel, "The channel to enable or disable the NSFW setting.")):
        
        if channel.is_nsfw():
            await channel.edit(nsfw=False)
            toggle = "disabled"
        else:
            await channel.edit(nsfw=True)
            toggle = "enabled"

        embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Channel Updated", description=f"The NSFW setting has been **{toggle}** for the {channel.mention} channel.")
        await ctx.respond(embed=embed)


    @channelSubCommands.command(name="slowmode", description="Set the slowmode of a channel.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_permissions(manage_channels=True)
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def slowmode(self, ctx: discord.ApplicationContext, channel: Option(discord.TextChannel, "The channel to set the slowmode for."), 
                       delay: Option(str, "The time to set the slowmode to.", 
                                     choices=["None", "5 Seconds", "10 Seconds", "15 Seconds", "30 Seconds", "1 Minute", "2 Minutes", "5 Minutes", "10 Minutes", "15 Minutes", "30 Minutes", "1 Hour", "2 Hours", "6 Hours"])):
        
        embed = await db.build_embed(ctx.author.guild, title="<a:loading:1247220769511964673> Setting Slowmode", description=f"The bot is currently setting the slowmode of {channel.mention} to **{delay}**...")
        await ctx.respond(embed=embed)

        time_intervals = {
            "None": 0,
            "5 Seconds": 5,
            "10 Seconds": 10,
            "15 Seconds": 15,
            "30 Seconds": 30,
            "1 Minute": 60,
            "2 Minutes": 120,
            "5 Minutes": 300,
            "10 Minutes": 600,
            "15 Minutes": 900,
            "30 Minutes": 1800,
            "1 Hour": 3600,
            "2 Hours": 7200,
            "6 Hours": 21600,
        }

        await channel.edit(slowmode_delay=time_intervals.get(delay))
        embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Slowmode Set", description=f"The slowmode of {channel.mention} has been set to **{delay}**.")
        await ctx.edit(embed=embed)


    @webhookSubCommands.command(name="create", description="Create a webhook for a channel.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    async def create_webhook(self, ctx: discord.ApplicationContext, channel: Option(discord.TextChannel, "The channel to create the webhook in."),
                             username: Option(str, "The username of the webhook.")):

        await channel.create_webhook(name=username)
        embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Webhook Created", description=f"The **{username}** webhook was successfully created for {channel.mention}")
        await ctx.respond(embed=embed)


    @webhookSubCommands.command(name="delete", description="Delete a webhook from a channel.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    async def delete_webhook(self, ctx: discord.ApplicationContext, webhook: Option(str, "The webhook to delete.", autocomplete=basic_autocomplete(Utils.get_webhooks))):

        deleted = False
        webhook_parts = webhook.split('|')
        if len(webhook_parts) > 1:
            result = webhook_parts[1].strip()
            channel = webhook_parts[0].strip()
            for webhooks in await ctx.guild.webhooks():
                if webhooks.name == result:
                    await webhooks.delete()
                    deleted = True
                    break

        if not deleted:
            embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="The webhook provided was invalid or no longer existing.")
            return await ctx.respond(embed=embed, ephemeral=True)
        
        channel = discord.utils.get(ctx.guild.channels, name=channel)
        embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Webhook Deleted", description=f"The **{result}** webhook was successfully deleted from {channel.mention}")
        await ctx.respond(embed=embed)


    @saywebhook.command(name="embed", description="Sends an embed using a webhook.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def webhook_embed(self, ctx: discord.ApplicationContext, username: Option(str, "The username of the profile."),
                            webhook: Option(str, "The Webhook link.", autocomplete=basic_autocomplete(Utils.get_webhooks))):
        
        webhook_url = None
        webhook_parts = webhook.split('|')
        if len(webhook_parts) > 1:
            result = webhook_parts[1].strip()
            for webhooks in await ctx.guild.webhooks():
                if webhooks.name == result:
                    webhook_url = webhooks.url
                    break

        if not webhook_url:
            embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="The webhook provided was invalid or no longer existing.")
            return await ctx.respond(embed=embed, ephemeral=True)

        user_embed = await db.build_embed(ctx.author.guild, title=f"Embed Builder", description=f"Click the buttons below to build your embed.")
        embed_tool = EmbedToolView(channel_or_message=None, is_new_embed=True, view=None, custom=f"webhook|{username}|{webhook_url}", ctx=ctx)
        await ctx.respond(embed=user_embed, view=embed_tool, ephemeral=True)


    @saywebhook.command(name="impersonate", description="Sends a webhook message using the members name and avatar.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def webhook_impersonate(self, ctx: discord.ApplicationContext, 
                            webhook: Option(str, "The Webhook to use.", autocomplete=basic_autocomplete(Utils.get_webhooks)),
                            member: Option(discord.Member, "The member to impersonate."),
                            message: Option(str, "The message to send.")):
        
        embed = await db.build_embed(ctx.author.guild, title="<a:Loading:1247220769511964673> Impersonating Member", description=f"Sending a message as {member.mention}...")
        await ctx.respond(embed=embed, ephemeral=True)
        
        webhook_url = None
        webhook_parts = webhook.split('|')
        if len(webhook_parts) > 1:
            result = webhook_parts[1].strip()
            for webhooks in await ctx.guild.webhooks():
                if webhooks.name == result:
                    webhook_url = webhooks.url
                    break

        if not webhook_url:
            embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="The webhook provided was invalid or no longer existing.")
            return await ctx.edit(embed=embed)
    
        async with aiohttp.ClientSession() as cs:
            webhook_ = DiscordWebhook(url=webhook_url, content=message, username=member.display_name, avatar_url=member.display_avatar.url)
            response = webhook_.execute()
            response_data = response.json()

        if response.status_code == 200:
            embed = await db.build_embed(ctx.guild, title=f"{success_emoji} Message Sent", description=f"Your message was sent to <#{response_data['channel_id']}>.")
            await ctx.edit(embed=embed)
        elif response.status_code == 404 or response.status_code == 401:
            embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="The webhook provided was invalid or no longer existing.")
            await ctx.edit(embed=embed)


    @saywebhook.command(name="normal", description="Sends a message using a webhook.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def webhook_normal(self, ctx: discord.ApplicationContext, 
                             webhook: Option(str, "The channel to send the webhook message.", autocomplete=basic_autocomplete(Utils.get_webhooks)), 
                             username: Option(str, "The username of the profile."), 
                             overwride_avatar: Option(bool, "Should the bot override the webhook avatar."),
                             message: Option(str, "The message to send.")):
        
        webhook_url = None
        webhook_parts = webhook.split('|')
        if len(webhook_parts) > 1:
            result = webhook_parts[1].strip()
            for webhooks in await ctx.guild.webhooks():
                if webhooks.name == result:
                    webhook_url = webhooks.url
                    break

        if not webhook_url:
            embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="The webhook provided was invalid or no longer existing.")
            await ctx.respond(embed=embed, ephemeral=True)
            return
    
        async with aiohttp.ClientSession() as cs:
            webhook_ = DiscordWebhook(url=webhook_url, content=message, username=username, avatar_url=ctx.author.display_avatar.url if overwride_avatar else None)
            response = webhook_.execute()
            response_data = response.json()
    
        if response.status_code == 200:
            embed = await db.build_embed(ctx.guild, title=f"{success_emoji} Message Sent", description=f"Your message was sent to <#{response_data['channel_id']}>.")
            await ctx.respond(embed=embed, ephemeral=True)
        elif response.status_code == 404 or response.status_code == 401:
            embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="The webhook provided was invalid or no longer existing.")
            await ctx.respond(embed=embed, ephemeral=True)
        

    @saywebhook.command(name="edit", description="Edit an embed sent from a webhook.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def webhook_edit(self, ctx: discord.ApplicationContext, 
                           webhook: Option(str, "The Webhook link.", autocomplete=basic_autocomplete(Utils.get_webhooks)), 
                           message_link: Option(str, "The link of the message. (Right click the message and select 'Copy Message Link')")):
        
        webhook_url = None
        webhook_parts = webhook.split('|')
        if len(webhook_parts) > 1:
            result = webhook_parts[1].strip()
            for webhooks in await ctx.guild.webhooks():
                if webhooks.name == result:
                    webhook_url = webhooks.url
                    break

        if not webhook_url:
            embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="The webhook provided was invalid or no longer existing.")
            return await ctx.respond(embed=embed, ephemeral=True)
        
        pattern = r"https://(?:canary\.|ptb\.|)discord(?:app)?\.com/channels/(\d+)/(\d+)/(\d+)"
        match = re.search(pattern, message_link)

        if not match:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The message link you provided was incorrect. Make sure to right click the message and select 'Copy Message Link'.")
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        try:
            message_link_parts = message_link.split('/')
            message_id = int(message_link_parts[-1])
            async with aiohttp.ClientSession() as session:
                response = await session.get(f"{webhook_url}/messages/{message_id}", headers={'Content-Type': 'application/json'})
                response_data = await response.json()

            user_embed = discord.Embed.from_dict(response_data["embeds"][0])
            embed_tool = EmbedToolView(channel_or_message=None, is_new_embed=True, view=None, custom=f"webhook|edit|{webhook_url}|{message_id}", ctx=ctx)
            await ctx.respond(embed=user_embed, view=embed_tool, ephemeral=True)
        except Exception as e:
            print(e)


    @saySubCommands.command(name="sticky", description="Sends a sticky message to the specified channel.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def sticky_send(self, ctx: discord.ApplicationContext, channel: Option(discord.TextChannel, "The channel to send the sticky message to.")):
            
        try:
            user_embed = await db.build_embed(ctx.author.guild, title=f"Embed Builder", description=f"Click the buttons below to build your embed.")
            embed_tool = EmbedToolView(channel_or_message=channel, is_new_embed=True, custom="sticky", view=None, ctx=ctx)
            await ctx.respond(embed=user_embed, view=embed_tool, ephemeral=True)
        except discord.Forbidden:
            embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="I do not have the necessary permissions to send messages in that channel.")
            await ctx.respond(embed=embed, ephemeral=True)


    @saySubCommands.command(name="normal", description="Sends a message to the specified channel.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def normal_send(self, ctx: discord.ApplicationContext, channel: Option(discord.TextChannel, "The channel to send the embed to."), text: Option(str, "The message to send.")):

        await channel.send(text)
        embed = await db.build_embed(ctx.author.guild, title=f"📨 Message Sent", description=f"Your message was sent to {channel.mention}.")
        await ctx.respond(embed=embed, ephemeral=True)


    @commands.slash_command(name="color", description="Get information on a hex color.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def color_info(self, ctx: discord.ApplicationContext, color: Option(str, "The hex color to get information on.")):
        
        def is_valid_hex_color(s):
            return len(s) == 6 and all(c in string.hexdigits for c in s)

        if not is_valid_hex_color(color):
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The color should use the following format - FFFFFF.")
            await ctx.respond(embed=embed, ephemeral=True)
            return

        image = Image.new("RGB", (500, 500), "#" + color)

        image_buffer = io.BytesIO()
        image.save(image_buffer, format="PNG")
        image_buffer.seek(0)

        r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))

        formatted_rgb = f"🟥 {r} 🟩 {g} 🟦 {b}"

        embed = discord.Embed(title=f"#{color} | {formatted_rgb}", color=int(color, 16))
        embed.set_image(url="attachment://color.png")

        image_file = discord.File(image_buffer, filename="color.png")

        await ctx.respond(embed=embed, file=image_file)


    @commands.slash_command(name="element", description="Get information on an element.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def element_info(self, ctx: discord.ApplicationContext, element: Option(str, "The element to get information on.", autocomplete=basic_autocomplete(elements))):

        if element not in elements:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"Invalid element.")
            await ctx.respond(embed=embed, ephemeral=True)   
            return
        
        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Element Data", description=f"Retrieving data on the element {element}...")
        await ctx.respond(embed=embed)

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.popcat.xyz/periodic-table?element={element}") as a:
                data = await a.json(content_type="application/json")
                if a.status == 200:

                    async with aiohttp.ClientSession() as session:
                        async with session.get(data["image"]) as response:
                                image_data = await response.read()
                                image_file = io.BytesIO(image_data)
                                image_attachment = discord.File(image_file, filename="image.png")

                                embed = await db.build_embed(ctx.guild, title=f"🧪 Element Information | {element}")
                                embed.add_field(name="__Main Details__", value=f"**Name** ➭ {data['name']}\n**Symbol** ➭ {data['symbol']}\n**Atomic Number** ➭ {data['atomic_number']}\n"
                                                + f"**Atomic Mass** ➭ {data['atomic_mass']}\n```{data['summary']}```", inline=False)
                                embed.set_thumbnail(url="attachment://image.png")
                                await ctx.edit(embed=embed, file=image_attachment)
                else:
                    embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The API is currently down.")
                    await ctx.edit(embed=embed, ephemeral=True)  


    @commands.slash_command(name="randomcolor", description="Get random HEX color.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def randomcolor(self, ctx: discord.ApplicationContext):

        random_color = '%06x' % random.randint(0, 0xFFFFFF)

        image = Image.new("RGB", (500, 500), f"#{random_color}")

        image_buffer = io.BytesIO()
        image.save(image_buffer, format="PNG")
        image_buffer.seek(0)

        color_int = int(random_color, 16)
        r, g, b = tuple(int(random_color[i:i+2], 16) for i in (0, 2, 4))
        formatted_rgb = f"🟥 {r} 🟩 {g} 🟦 {b}"

        embed = discord.Embed(title=f"#{random_color.upper()} | {formatted_rgb}", color=color_int)
        embed.set_image(url=f"attachment://{random_color.upper()}.png")

        image_file = discord.File(image_buffer, filename=f"{random_color.upper()}.png")

        await ctx.respond(embed=embed, file=image_file)


    @commands.slash_command(name="weather", description="Get the current weather data from a location.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def weather(self, ctx: discord.ApplicationContext, city: Option(str, "The city to gather the weather data from.", autocomplete=basic_autocomplete(major_cities))):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Retrieving Weather Data", description=f"Retrieving weather data for **{city}**...")
        await ctx.respond(embed=embed)

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.popcat.xyz/weather?q={city}") as a:
                data = await a.json(content_type="application/json")

            location = data[0]["location"]
            current_weather = data[0]["current"]
            tomorrow_weather = data[0]["forecast"]

            city_name = location['name'].split(",")

            embed = await db.build_embed(ctx.guild, title=f"⛅ Weather Information | {city_name[0]}")
            embed.add_field(name="__Today__", value=f"**Temperature** ➭ {current_weather['temperature']}°C\n**Sky** ➭ {current_weather['skytext']}\n**Humidity** ➭ {current_weather['humidity']}%\n"
                            + f"**Wind** ➭ {current_weather['winddisplay']}", inline=False)
            embed.add_field(name=f"{tomorrow_weather[-1]['day']}", value=f"**Lowest Temperature** ➭ {tomorrow_weather[-1]['low']}°C\n**Highest Temperature** ➭ {tomorrow_weather[0]['high']}°C\n**Sky** ➭ {tomorrow_weather[-1]['skytextday']}", inline=True)
            embed.add_field(name=f"{tomorrow_weather[0]['day']}", value=f"**Lowest Temperature** ➭ {tomorrow_weather[0]['low']}°C\n**Highest Temperature** ➭ {tomorrow_weather[1]['high']}°C\n**Sky** ➭ {tomorrow_weather[0]['skytextday']}", inline=True)
            embed.add_field(name="", value="", inline=False)
            embed.add_field(name=f"{tomorrow_weather[1]['day']}", value=f"**Lowest Temperature** ➭ {tomorrow_weather[1]['low']}°C\n**Highest Temperature** ➭ {tomorrow_weather[2]['high']}°C\n**Sky** ➭ {tomorrow_weather[1]['skytextday']}", inline=True)
            embed.add_field(name=f"{tomorrow_weather[2]['day']}", value=f"**Lowest Temperature** ➭ {tomorrow_weather[2]['low']}°C\n**Highest Temperature** ➭ {tomorrow_weather[3]['high']}°C\n**Sky** ➭ {tomorrow_weather[2]['skytextday']}", inline=True)
            embed.set_thumbnail(url=current_weather["imageUrl"])
            await ctx.edit(embed=embed)


    @saySubCommands.command(name="reply", description="Reply to a message using the bot.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def reply_send(self, ctx: discord.ApplicationContext,
                        message_link: discord.Option(str, "The link of the message. (Right click the message and select 'Copy Message Link')"), 
                        text: Option(str, "The message to send.")):

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

            if not channel:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The channel the message was in could not be found.")
                await ctx.respond(embed=embed, ephemeral=True)
                return

            message = await channel.fetch_message(message_id)
            await message.reply(text)

            embed = await db.build_embed(ctx.author.guild, title=f"📨 Message Replied", description=f"The bot has replied to {message.author.mention}'s message.")
            await ctx.respond(embed=embed, ephemeral=True)

        except discord.NotFound:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The specified message could not be found.")
            await ctx.respond(embed=embed, ephemeral=True)

        except discord.Forbidden:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="I do not have the necessary permissions to reply to this message.")
            await ctx.respond(embed=embed, ephemeral=True)

        except discord.HTTPException:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="An unexpected HTTP error occurred.")
            await ctx.respond(embed=embed, ephemeral=True)


    @commands.slash_command(name="poll", description="Create a poll.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @discord.default_permissions(manage_messages=True)
    async def poll_send(self, ctx: discord.ApplicationContext,
                         channel: Option(discord.TextChannel, "The channel to send the poll."), title: Option(str, "The title of the poll."), question: Option(str, "The question to ask."), option_1: Option(str, "The first poll option."), option_2: Option(str, "The second poll option.")):

        poll = await db.build_embed(ctx.author.guild, title=f"<:poll:1209072968420823050> {title}", description=question)
        poll.add_field(name=option_1, value="", inline=True)
        poll.add_field(name=option_2, value="", inline=True)
        poll.set_thumbnail(url="https://i.imgur.com/zTLElVM.png")
        await channel.send(embed=poll, view=Views.Polls(option_1, option_2))

        embed = await db.build_embed(ctx.author.guild, title=f"<:poll:1209072968420823050> Poll Sent", description=f"Your poll was sent to {channel.mention}.")
        await ctx.respond(embed=embed, ephemeral=True)


    @saySubCommands.command(name="edit", description="Edits a message sent by the bot.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def msg_edit(self, ctx: discord.ApplicationContext,
                        message_link: discord.Option(str, "The link of the message. (Right click the message and select 'Copy Message Link')")):

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

            if message.author != ctx.guild.me:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="I cannot edit a message that was not sent by me.")
                await ctx.respond(embed=embed, ephemeral=True)
                return
            
            elif not message.embeds:
                await ctx.response.send_modal(ContentModal(title="Content", initial_content=message.content, message=message))
                return

            user_embed = message.embeds[0]
            embed_tool = EmbedToolView(channel_or_message=message, is_new_embed=False, custom=None, view=None, ctx=ctx)
            await ctx.respond(content=message.content, embed=user_embed, view=embed_tool, ephemeral=True)

        except discord.NotFound:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The specified message could not be found.")
            await ctx.respond(embed=embed, ephemeral=True)

        except discord.Forbidden:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="I do not have the necessary permissions to edit this message.")
            await ctx.respond(embed=embed, ephemeral=True)

        except discord.HTTPException:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="An unexpected HTTP error occurred.")
            await ctx.respond(embed=embed, ephemeral=True)
        
        except Exception as e:
            print(e)


    @commands.slash_command(name="translate", description="Translate text to any language.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def translate(self, ctx: discord.ApplicationContext, text: Option(str, "The text to translate."), language: Option(str, "The language to translate to.", autocomplete=basic_autocomplete(languages))):

        translator = Translator()
        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Translating", description=f"The text is being translated to {language}...")
        await ctx.respond(embed=embed)

        source_language = translator.detect(text).lang

        if source_language not in LANGUAGES:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Unsupported language.")
            await ctx.edit(embed=embed)
            return
        
        translated_message = translator.translate(text, src=source_language, dest=language)

        embed = await db.build_embed(ctx.author.guild, title=f"🌐 Text Translated | {language}", description=translated_message.text)
        await ctx.edit(embed=embed)


    @commands.slash_command(name="ghostping", description="Ghost ping a member or role.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @discord.default_permissions(manage_messages=True)
    async def ghost_ping(self, ctx: discord.ApplicationContext, ping: Option(discord.Member | discord.Role, "The member or role to ghost ping."), channel: Option(discord.TextChannel, "The channel to ghost ping the member or role in.")):

        if ping == ctx.guild.default_role:
            ping = "@everyone"
        else:
            ping = ping.mention
        
        await channel.send(f"{ping}", delete_after=0.1)
        await ctx.respond(embed=await db.build_embed(ctx.guild, title=f"👻 Ghost Ping", description=f"{ping} has been ghost pinged."), ephemeral=True)


    @commands.slash_command(name="ipinfo", description="Get data from an IP address.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def ip_info(self, ctx: discord.ApplicationContext, ip: Option(str, "The IP address to retrieve data on")):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Retrieving Data", description=f"Retrieving data on {ip}...")
        await ctx.respond(embed=embed)

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://ipapi.co/{ip}/json/") as a:
                data = await a.json(content_type="application/json")

        embed = await db.build_embed(ctx.author.guild, title=f"<a:Information:1247223152367636541> IP Information | {ip}")
        embed.add_field(name="__Main Details__", value=f"**IP** ➭ {data['ip']}\n**City** ➭ {data['city']}\n**Region** ➭ {data['region']}\n**Country** ➭ {data['country_name']}\n**Postal Code** ➭ {data['postal']}\n**Timezone** ➭ {data['timezone']}\n**Latitude** ➭ {data['latitude']}\n**Longitude** ➭ {data['longitude']}", inline=False)
        embed.add_field(name="__Additional Details__", value=f"**ASN** ➭ {data['asn']}\n**ORG** ➭ {data['org']}\n**ISP** ➭ {data['org']}", inline=False)
        await ctx.edit(embed=embed)


    @buttonAddSubCommands.command(name="role", description="Add a role button to a message.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    async def role_button_add(self, ctx: discord.ApplicationContext, 
                            message_link: Option(str, "The link of the message. (Right click the message and select 'Copy Message Link')"), 
                            role: Option(discord.Role, "The role the button will give."),
                            color: Option(str, "The color of the button.", choices=["Blue", "Grey", "Green", "Red"], default=discord.ButtonStyle.grey, required=False),
                            emoji: Option(str, "The emoji to use on the button.", default=None, required=False)):
        
        invoker_top_role_position = ctx.author.top_role.position
        user_top_role_position = role.position

        if role.managed:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"You can not create a button for managed roles.")
            await ctx.respond(embed=embed, ephemeral=True)
            return 

        if invoker_top_role_position <= user_top_role_position and not ctx.author.id == ctx.author.guild.owner.id:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"You can not create a button for the {role.mention} role.")
            await ctx.respond(embed=embed, ephemeral=True)
            return 
        
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
            existing_view = discord.ui.View.from_message(message)

            if not message.author.id == ctx.guild.me.id:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="I can not edit a message that was not sent by me.")
                await ctx.respond(embed=embed, ephemeral=True)
                return
            
            if existing_view and existing_view.get_item(f"role|{role.id}"):
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="This role already exists on the message.")
                await ctx.respond(embed=embed, ephemeral=True)
                return

            color_mapping = {"Blue": discord.ButtonStyle.blurple, "Grey": discord.ButtonStyle.grey, "Green": discord.ButtonStyle.green, "Red": discord.ButtonStyle.red}
            style = color_mapping.get(color, discord.ButtonStyle.grey)

            await Views.add_role_button(message, role, style, emoji)

            embed = await db.build_embed(ctx.guild, title="<a:Information:1247223152367636541> Role Button Added", description=f"The {role.mention} role will be granted via the button.")
            await ctx.respond(embed=embed, ephemeral=True)

        except discord.NotFound:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The specified message was not found.")
            await ctx.respond(embed=embed, ephemeral=True)
            return

        except discord.Forbidden:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="I do not have the necessary permissions to edit this message.")
            await ctx.respond(embed=embed, ephemeral=True)
            return

        except discord.HTTPException as e:
            if e.code == 50035:
                await ctx.respond(embed=await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The emoji you provided was invalid."), ephemeral=True)
            else:
                await ctx.respond(embed=await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Unknown HTTP error occured."), ephemeral=True)


    @buttonAddSubCommands.command(name="link", description="Add a link button to a message.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def url_button_add(self, ctx: discord.ApplicationContext, message_link: Option(str, "The link of the message. (Right click the message and select 'Copy Message Link')"),  
                            label: Option(str, "The label of the button."), url: Option(str, "The link the button will redirect to."), emoji: Option(str, "The emoji to use on the button.", default=None, required=False)):
        
        pattern = r"https://(?:canary\.|ptb\.|)discord(?:app)?\.com/channels/(\d+)/(\d+)/(\d+)"
        if not re.search(pattern, message_link):
            await ctx.respond(embed=await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The message link you provided was incorrect. Make sure to right click the message and select 'Copy Message Link'."), ephemeral=True)
            return

        message_link_parts = message_link.split('/')
        channel_id = int(message_link_parts[-2])
        message_id = int(message_link_parts[-1])

        try:
            channel = ctx.guild.get_channel(channel_id)
            message = await channel.fetch_message(message_id)

            if message.author.id != ctx.guild.me.id:
                await ctx.respond(embed=await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="I can not edit a message that was not sent by me."), ephemeral=True)
                return

            if not validators.url(url):
                await ctx.respond(embed=await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The link provided for the button was invalid."), ephemeral=True)
                return

            await Views.add_url_button(message, label, url, emoji)

            await ctx.respond(embed=await db.build_embed(ctx.guild, title="<a:Information:1247223152367636541> Link Button Added", description=f"The **{label}** button will redirect any interactions to {url}."), ephemeral=True)

        except discord.NotFound:
            await ctx.respond(embed=await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The channel or message could not be found."), ephemeral=True)

        except discord.Forbidden:
            await ctx.respond(embed=await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="I do not have the necessary permissions to edit this message."), ephemeral=True)

        except discord.HTTPException as e:
            if e.code == 50035:
                await ctx.respond(embed=await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The emoji you provided was invalid."), ephemeral=True)
            else:
                await ctx.respond(embed=await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Unknown HTTP error occured."), ephemeral=True)

    
    @buttonSubCommands.command(name="remove", description="Remove a button by name.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def button_remove(self, ctx: discord.ApplicationContext, message_link: Option(str, "The link of the message with the button. (Right click the message and select 'Copy Message Link')"), 
                            button_name: Option(str, "The name of the button to remove.")):        

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

            existing_view = discord.ui.View.from_message(message) or discord.ui.View()
            found_button = None

            for item in existing_view.children:
                if isinstance(item, discord.ui.Button) and item.label == button_name:
                    found_button = item
                    break

            if found_button:
                existing_view.remove_item(found_button)
                await message.edit(view=existing_view)

                embed = await db.build_embed(ctx.guild, title="🗑 Button Removed", description=f"The **{button_name}** button has been removed.")
                await ctx.respond(embed=embed, ephemeral=True)

            else:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"No button with the name **{button_name}** was found on the message.")
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


    @addSubCommands.command(name="emoji", description="Adds an emoji to the server.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_permissions(manage_emojis=True)
    async def steal_emoji(self, ctx: discord.ApplicationContext, emoji: Option(discord.PartialEmoji, "The emoji to add to the server.")):

            embed = await db.build_embed(ctx.author.guild, title="<a:Loading:1247220769511964673> Adding Emoji", description=f"Adding **{emoji.name}** to the server...")
            await ctx.respond(embed=embed)

            try:
                emoji = ctx.selected_options
                emoji_id = [int(entry["value"].split(":")[2][:-1]) for entry in ctx.selected_options if entry["name"] == "emoji"]
                emoji_name = [str(entry["value"].split(":")[1]) for entry in ctx.selected_options if entry["name"] == "emoji"]

                emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id[0]}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(emoji_url) as response:
                        if response.status == 200:
                            emoji_bytes = await response.read()

                emoji = await ctx.guild.create_custom_emoji(name=emoji_name[0], image=emoji_bytes)

                embed = await db.build_embed(ctx.author.guild, title=":ninja: Emoji Added", description=f"The emoji **{emoji_name[0]}** has been added to the server.")
                embed.set_thumbnail(url=emoji.url)
                await ctx.edit(embed=embed)

            except Exception as e:
                print("[steal_emoji]: ", e)
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The emoji could not be added to the server.")
                await ctx.edit(embed=embed)


    @addSubCommands.command(name="sticker", description="Adds a sticker to the server.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_permissions(manage_emojis=True)
    async def steal_sticker(self, ctx: discord.ApplicationContext, message_link: Option(str, "The message link containing the sticker. (Right click the message and select 'Copy Message Link')", required=False), image: Option(discord.Attachment, "The image to save as a sticker.", required=False)):

        try:
            if message_link and image:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Please only select one option at a time.")
                await ctx.respond(embed=embed, ephemeral=True)
                return
            
            if message_link is not None:
                pattern = r"https://(?:canary\.|ptb\.|)discord(?:app)?\.com/channels/(\d+)/(\d+)/(\d+)"
                match = re.search(pattern, message_link)

                if not match:
                    embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The message link you provided was incorrect. Make sure to right click the message and select 'Copy Message Link'.")
                    await ctx.respond(embed=embed, ephemeral=True)
                    return
                
                embed = await db.build_embed(ctx.author.guild, title="<a:Loading:1247220769511964673> Fetching Message", description=f"Fetching message with the link {message_link}...")
                await ctx.respond(embed=embed)

                message_link_parts = message_link.split('/')
                channel_id = int(message_link_parts[-2])
                message_id = int(message_link_parts[-1])

                try:
                    channel = ctx.guild.get_channel(channel_id)
                    message = await channel.fetch_message(message_id)
                except discord.NotFound:
                    embed = await db.build_embed( ctx.author.guild, title=f"{error_emoji} Request Failed", description="The specified message was not found.")
                    await ctx.edit(embed=embed)
                    return
                
                sticker_data = message.stickers[0]
                sticker_id = sticker_data.id
                sticker_name = sticker_data.name
                
                embed = await db.build_embed(ctx.author.guild, title="<a:Loading:1247220769511964673> Adding Sticker", description=f"Adding **{sticker_name}** to the server...")
                await ctx.edit(embed=embed)

                sticker_url = f"https://cdn.discordapp.com/stickers/{sticker_id}.png"
                async with aiohttp.ClientSession() as session:
                    async with session.get(sticker_url) as response:
                        if response.status == 200:
                            sticker_bytes = await response.read()
                        else:
                            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The sticker could not be added to the server.")
                            await ctx.edit(embed=embed)
                            return

                sticker_file = discord.File(io.BytesIO(sticker_bytes), filename=f"{sticker_name}.png")

                await ctx.guild.create_sticker(name=sticker_name, description="Added with Trinity Bot", emoji="🐱‍👤", file=sticker_file)

                embed = await db.build_embed(ctx.author.guild, title=":ninja: Sticker Added", description=f"The sticker **{sticker_name}** has been added to the server.")
                embed.set_thumbnail(url=sticker_url)
                await ctx.edit(embed=embed)

            if image:
                if image.content_type not in ["image/png", "image/jpg", "image/jpeg", "image/gif"]:
                    embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The image should be a be a png, jpg or gif.")
                    await ctx.respond(embed=embed, ephemeral=True)
                    return

                sticker_bytes = await image.read()
                sticker_name, _ = os.path.splitext(image.filename)
                
                embed = await db.build_embed(ctx.author.guild, title="<a:Loading:1247220769511964673> Saving Sticker", description=f"Saving the sticker **{sticker_name}**...")
                await ctx.respond(embed=embed)

                sticker_file = discord.File(io.BytesIO(sticker_bytes), filename=f"{sticker_name}.png")
                new_sticker = await ctx.guild.create_sticker(name=sticker_name, description="Added with Trinity Bot", emoji="🐱‍👤", file=sticker_file)

                embed = await db.build_embed(ctx.author.guild, title=":ninja: Sticker Added", description=f"The sticker **{sticker_name}** has been added to the server.")
                embed.set_thumbnail(url=new_sticker.url)
                await ctx.edit(embed=embed)

        except discord.HTTPException as e:
            if e.status == 400 and e.code == 30039:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The maximum number of stickers has been reached.")
            else:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The sticker could not be added to the server.")
            await ctx.edit(embed=embed)

        except Exception as e:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The sticker could not be added to the server.")
            await ctx.edit(embed=embed)


    @commands.slash_command(name="afk", description="Set your AFK status.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def afk(self, ctx: discord.ApplicationContext, reason: Option(str, "The reason for being AFK.")):

        embed = await db.build_embed(ctx.author.guild, title="<a:Loading:1247220769511964673> Updating Status", description="Updating your AFK status...")
        await ctx.respond(embed=embed)

        try:
            if ctx.author.nick and not ctx.author.nick.startswith("[AFK]"):
                await ctx.author.edit(nick=f"[AFK] {ctx.author.global_name}")
        except:
            pass
        
        try:
            existing_data = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "AFK")
            if existing_data:
                existing_data = json.loads(existing_data)
            else:
                existing_data = {}

            if existing_data and existing_data.get(str(ctx.author.id)):
                await db.remove_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "AFK", str(ctx.author.id))
                del afk[ctx.author.id]


            existing_data = [f"{reason}.", datetime.now().timestamp()]
            await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "AFK", ctx.author.id, existing_data)

            afk[ctx.author.id] = [f"{reason}.", datetime.now().timestamp()]

            embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} AFK Status Updated", description=f"You are now AFK with the reason **{reason}**.")
            await ctx.edit(embed=embed)
        except Exception as e:
            print("[afk]: ", e)
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"An error occurred while processing your request.")
            await ctx.edit(embed=embed)


    @reminderSubCommands.command(name="create", description="Create a reminder.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def reminder(self, ctx: discord.ApplicationContext, time: Option(str, "The time until the reminder (1s, 2m, 3h, 4d)."), reminder: Option(str, "The reminder message.")):

        if time.endswith("s"):
            time = time[:-1]
            time = int(time)
        elif time.endswith("m"):
            time = time[:-1]
            time = int(time) * 60
        elif time.endswith("h"):
            time = time[:-1]
            time = int(time) * 60 * 60
        elif time.endswith("d"):
            time = time[:-1]
            time = int(time) * 60 * 60 * 24
        else:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Invalid time format. Please use a valid time format (s, m, h, d).")
            await ctx.respond(embed=embed, ephemeral=True)
            return

        reminder_time = datetime.now() + timedelta(seconds=time)
        reminder_time = reminder_time.timestamp()
        time_now = datetime.now().timestamp()
        time_now = round(time_now)

        if reminders.get(ctx.author.id):
            reminders[ctx.author.id].append([reminder, reminder_time, ctx.channel, time_now])
        else:
            reminders[ctx.author.id] = [[reminder, reminder_time, ctx.channel, time_now]]

        embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Reminder Set", description=f"Your reminder has been set for **{time}** seconds from now.")
        await ctx.respond(embed=embed)


    @reminderSubCommands.command(name="list", description="View your reminders.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def reminders(self, ctx: discord.ApplicationContext):
            
        if reminders.get(ctx.author.id):
            reminders_list = reminders[ctx.author.id]
            embed = await db.build_embed(ctx.author.guild, title="<a:Information:1247223152367636541> Reminders", description=f"You have **{len(reminders_list)}** reminders set.")
            for reminder in reminders_list:
                embed.add_field(name=f"Reminder #{reminders_list.index(reminder) + 1}", value=f"**Reminder** ➭ {reminder[0]}\n**Time** ➭ <t:{round(reminder[1])}:R>\n**Channel** ➭ {reminder[2].mention}", inline=False)
            await ctx.respond(embed=embed)
        else:
            embed = await db.build_embed(ctx.author.guild, title="<a:Information:1247223152367636541> Reminders", description="You have no reminders set.")
            await ctx.respond(embed=embed, ephemeral=True)


    @reminderSubCommands.command(name="clear", description="Clear your reminders.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def reminder_clear(self, ctx: discord.ApplicationContext):
                
        if reminders.get(ctx.author.id):
            reminders_list = reminders[ctx.author.id]
            for reminder in reminders_list:
                reminders_list.remove(reminder)
            embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Reminders Cleared", description="All of your reminders have been cleared.")
            await ctx.respond(embed=embed)
        else:
            embed = await db.build_embed(ctx.author.guild, title="<a:Information:1247223152367636541> Reminders", description="You have no reminders set.")
            await ctx.respond(embed=embed, ephemeral=True)


    @reminderSubCommands.command(name="remove", description="Remove a reminder.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def reminder_remove(self, ctx: discord.ApplicationContext, reminder: Option(str, "The reminder to remove.", autocomplete=basic_autocomplete(Utils.get_reminder_names))):
      
        if reminders.get(ctx.author.id):
            reminders_list = reminders[ctx.author.id]
            for reminder_ in reminders_list:
                if reminder_[0] == reminder:
                    reminders_list.remove(reminder_)
                    embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Reminder Removed", description="Your reminder has been removed.")
                    await ctx.respond(embed=embed)
                    return

            embed = await db.build_embed(ctx.author.guild, title="<a:Information:1247223152367636541> Reminder Removal", description="The specified reminder was not found.")
            await ctx.respond(embed=embed)
        else:
            embed = await db.build_embed(ctx.author.guild, title="<a:Information:1247223152367636541> Reminders", description="You have no reminders set.")
            await ctx.respond(embed=embed, ephemeral=True)


    @searchSubCommands.command(name="google", description="Search for something on google.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def google_search(self, ctx: discord.ApplicationContext, query: Option(str, "The search query.")):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Searching Google", description=f"Searching Google for **{query}**...")
        await ctx.respond(embed=embed)

        try:
            top_results = await Utils.get_top_10_results(query)
        except Exception as e:
            print(f"Error during Google search: {e}")
            embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="An unknown error occured during the google search.")
            await ctx.edit(embed=embed)
            return

        titles_and_links = [(result.title, result.url) for result in top_results]
        response_text = "\n".join([f"[{title}]({link})" for title, link in titles_and_links])

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Search Results", style=discord.ButtonStyle.link, url=f"https://www.google.com/search?q={query}"))

        embed = await db.build_embed(ctx.author.guild, title=f"<a:Information:1247223152367636541> Google Search | {query}", description=response_text)
        await ctx.edit(embed=embed)

    
    @searchSubCommands.command(name="itunes", description="Search a song on iTunes.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def itunes_search(self, ctx: discord.ApplicationContext, query: Option(str, "The search query.")):
        
        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Searching iTunes", description=f"Searching iTunes for **{query}**...")
        await ctx.respond(embed=embed)

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.popcat.xyz/itunes?q={query}") as response:
                if response.status == 200:
                    data = await response.json(content_type="application/json")

                    if "error" in data:
                        embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description=data["error"])
                        await ctx.edit(embed=embed)
                        return
                    
                    url = data["url"]
                    name = data["name"]
                    artist = data["artist"]
                    album = data["album"]
                    release_date = data["release_date"]
                    thumbnail = data["thumbnail"]
                    length = data["length"]
                    genre = data["genre"]
                    price = data["price"]

                    view = discord.ui.View()
                    view.add_item(discord.ui.Button(label="View on iTunes", style=discord.ButtonStyle.link, url=url))

                    embed = await db.build_embed(ctx.guild, title=f"<a:Information:1247223152367636541> iTunes Search | {name}", description=f"**Artist** ➭ {artist}\n**Album** ➭ {album}\n**Release Date** ➭ {release_date}\n**Length** ➭ {length}\n**Genre** ➭ {genre}\n**Price** ➭ {price}")
                    embed.set_thumbnail(url=thumbnail)
                    await ctx.edit(embed=embed, view=view)

                else:
                    embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description=f"An error occurred while searching iTunes.")
                    await ctx.edit(embed=embed)


    @searchSubCommands.command(name="imbd", description="Search a for a movie on IMBD.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def imbd_search(self, ctx: discord.ApplicationContext, query: Option(str, "The search query.")):
        
        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Searching IMBD",
                                    description=f"Searching IMBD for **{query}**...")
        await ctx.respond(embed=embed)

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.popcat.xyz/imdb?q={query}") as response:
                if response.status == 200:
                    data = await response.json(content_type="application/json")

                    if "error" in data:
                        error = data["error"].replace("No", "No results found.")
                        embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed",
                                                    description=error)
                        await ctx.edit(embed=embed)
                        return

                    ratings = data["ratings"]
                    rating_str = "\n".join(f"**{rating['source']}** ➭ {rating['value']}" for rating in ratings)

                    title = data["title"]
                    plot = data["plot"]
                    poster = data["poster"]
                    imdb_url = data["imdburl"]

                    embed = await db.build_embed(ctx.guild, title=f"<a:Information:1247223152367636541> IMBD Search | {title}",
                                                description=f"```{plot}```")
                    embed.add_field(name="**__Ratings__**", value=rating_str, inline=False)
                    embed.add_field(name="**__Information__**",
                                    value=f"**Year** ➭ {data['year']}\n**Rated** ➭ {data['rated']}\n**Released** ➭ {data['released']}\n"
                                        f"**Runtime** ➭ {data['runtime']}\n**Genre** ➭ {data['genres']}\n**Director** ➭ {data['director']}\n"
                                        f"**Writer** ➭ {data['writer']}\n**Actors** ➭ {data['actors']}\n**Language** ➭ {data['languages']}\n"
                                        f"**Country** ➭ {data['country']}\n**Awards** ➭ {data['awards']}", inline=False)
                    embed.set_thumbnail(url=poster)

                    view = discord.ui.View()
                    view.add_item(discord.ui.Button(label="View on IMBD", style=discord.ButtonStyle.link, url=imdb_url))

                    await ctx.edit(embed=embed, view=view)

                else:
                    embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed",
                                                description=f"An error occurred while searching IMBD.")
                    await ctx.edit(embed=embed)


    @searchSubCommands.command(name="lyrics", description="Search for a song's lyrics.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def lyric_search(self, ctx: discord.ApplicationContext, query: str):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Searching Lyrics",
                                    description=f"Searching for **{query}** lyrics...")
        await ctx.respond(embed=embed)

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.popcat.xyz/lyrics?song={query}") as response:
                if response.status == 200:
                    data = await response.json(content_type="application/json")

                    if "error" in data:
                        error = data["error"].replace("No", "No results found.")
                        embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed",
                                                    description=error)
                        await ctx.edit(embed=embed)
                        return

                    title = data["title"]
                    plot = data["lyrics"]
                    poster = data["image"]
                    artist = data["artist"]

                    embed = await db.build_embed(ctx.guild, title=f"<a:Information:1247223152367636541> Lyrics Search | {title} by {artist}",
                                                description=f"```{plot}```")
                    embed.set_thumbnail(url=poster)

                    await ctx.edit(embed=embed)

                else:
                    embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed",
                                                description=f"An error occurred while searching lyrics.")
                    await ctx.edit(embed=embed)


    @searchSubCommands.command(name="urban", description="Search for a word on Urban Dictionary.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def urban_search(self, ctx: discord.ApplicationContext, query: Option(str, "The search query.")):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Searching Urban Dictionary",
                                    description=f"Searching Urban Dictionary for **{query}**...")
        await ctx.respond(embed=embed)

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.urbandictionary.com/v0/define?term={query}") as response:
                if response.status == 200:
                    data = await response.json(content_type="application/json")
                    
                    if not data["list"]:
                        embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description=f"No results found for **{query}**.")
                        await ctx.edit(embed=embed)
                        return
                    
                    first_entry = data["list"][0]

                    title = first_entry["word"]
                    definition = first_entry["definition"]
                    example = first_entry["example"]
                    author = first_entry["author"]
                    url = first_entry["permalink"]

                    embed = await db.build_embed(ctx.guild, title=f"<a:Information:1247223152367636541> Urban Dictionary Search | {title}")
                    embed.add_field(name="**__Definition__**", value=f"```{definition}```", inline=False)
                    embed.add_field(name="**__Example__**", value=f"```{example}```", inline=False)
                    embed.set_footer(text=f"Author: {author}")

                    view = discord.ui.View()
                    view.add_item(discord.ui.Button(label="View on Urban Dictionary", style=discord.ButtonStyle.link, url=url))

                    await ctx.edit(embed=embed, view=view)

                else:
                    embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description=f"An error occurred while searching Urban Dictionary.")
                    await ctx.edit(embed=embed)


    @commands.slash_command(name="upload", description="Upload an image to imgur.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def upload_image(self, ctx: discord.ApplicationContext, image: Option(discord.Attachment, "The image to upload."), title: Option(str, "The title of the image.", required=False), description: Option(str, "The description of the image.", default="Uploaded using Trinity Bot. https://xetrinityz.com/", required=False)):

        if "image" not in image.content_type:
            embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="This file type is not supported.")
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Uploading Image", description=f"Uploading image to imgur...")
        await ctx.respond(embed=embed)

        headers = {
            "Authorization": "Client-ID 6f3be42002fd06b"
        }

        image_data = await image.read()
        body = {
            "image": image_data,
            "title": title if title else image.filename,
            "description": description
        }

        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.imgur.com/3/image", data=body, headers=headers) as response:
                if response.status == 200:
                    response = await response.json(content_type="application/json")
                    image_url = response["data"]["link"]
                    delete_hash = response["data"]["deletehash"]
                    image_id = response["data"]["id"]
                    image_title = response["data"]["title"]

                    embed = await db.build_embed(ctx.guild, title=f"{success_emoji} Image Uploaded", description=f"Your image has been uploaded to imgur successfully.")
                    embed.add_field(name="**Image Title**", value=image_title)
                    embed.add_field(name="**Image ID**", value=image_id)
                    embed.set_image(url=image_url)

                    view = discord.ui.View()
                    view.add_item(discord.ui.Button(label="View Image", style=discord.ButtonStyle.link, url=f"https://imgur.com/{image_id}"))
                    view.add_item(discord.ui.Button(label="Delete Image", style=discord.ButtonStyle.link, url=f"https://imgur.com/delete/{delete_hash}"))
                    await ctx.edit(embed=embed, view=view)


    @triggerSubCommands.command(name="add", description="Add an auto response.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def trigger_create(self, ctx: discord.ApplicationContext, type: Option(str, "The type of auto response.", choices=["Text", "Embed", "Reaction"]), trigger: Option(str, "The trigger word."), response: Option(str, "The response.", required=False)):

        try:
            if (type == "Text" or type == "Reaction") and response is None:
                embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="Please provide a response.")
                await ctx.respond(embed=embed, ephemeral=True)
                return

            existing_data = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TRIGGERS")
            if existing_data:
                triggers = json.loads(existing_data)
            else:
                triggers = {}

            if trigger in triggers:
                embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description=f"An auto response with the word **{trigger}** already exists.")
                await ctx.respond(embed=embed, ephemeral=True)
                return
            
            if len(triggers) > 20:
                embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description=f"You can not have more than **20** auto responses.")
                await ctx.respond(embed=embed, ephemeral=True)
                return

            if type == "Reaction":
                try:
                    split_text = response.split(":")
                    result = split_text[2].rstrip(">")
                except:
                    embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="Invalid custom emoji. Please use a valid custom emoji from this server.")
                    await ctx.respond(embed=embed, ephemeral=True)
                    return
                
                emoji_list = await ctx.guild.fetch_emoji(int(result))
                if not emoji_list:
                    embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="Invalid custom emoji. Please use a valid custom emoji from this server.")
                    await ctx.respond(embed=embed, ephemeral=True)
                    return
                
                response = result

            if type != "Embed":
                triggers = {"type": type, "response": response}
                await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TRIGGERS", trigger, triggers)
                embed = await db.build_embed(ctx.guild, title=f"{success_emoji} Auto Response Created", description=f"The auto response with the word **{trigger}** has been created.")
                await ctx.respond(embed=embed)
            else:
                user_embed = await db.build_embed(ctx.author.guild, title=f"Embed Builder", description=f"Click the buttons below to build your embed.")
                embed_tool = EmbedToolView(channel_or_message=None, is_new_embed=True, custom=f"trigger_{trigger}", view=None, ctx=ctx)
                await ctx.respond(embed=user_embed, view=embed_tool, ephemeral=True)

        except Exception as e:
            print("[trigger_create]: ", e)

    
    @triggerSubCommands.command(name="remove", description="Remove an auto response.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def trigger_remove(self, ctx: discord.ApplicationContext, trigger: Option(str, "The trigger word.", autocomplete=basic_autocomplete(Utils.get_trigger_names))):

        existing_data = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TRIGGERS")
        if existing_data:
            triggers = json.loads(existing_data)
        else:
            triggers = {}

        if trigger not in triggers:
            embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description=f"No auto response with the name **{trigger}** exists.")
            await ctx.respond(embed=embed, ephemeral=True)
            return

        await db.remove_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TRIGGERS", trigger)
        embed = await db.build_embed(ctx.guild, title=f"{success_emoji} Auto Response Removed", description=f"The auto response with the word **{trigger}** has been removed.")
        await ctx.respond(embed=embed)

    
    @triggerSubCommands.command(name="edit", description="Edit an auto response.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def trigger_edit(self, ctx: discord.ApplicationContext, trigger: Option(str, "The auto response to edit.", autocomplete=basic_autocomplete(Utils.get_trigger_names)), type: Option(str, "The type of trigger response.", choices=["Text", "Embed", "Reaction"]), response: Option(str, "The response.", required=False)):
            
        try:
            if type != "Embed":
                embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Editing Auto Response", description=f"Editing the auto response with the word **{trigger}**...")
                await ctx.respond(embed=embed)

            if (type == "Text" or type == "Reaction") and response is None:
                embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="Please provide a response.")
                await ctx.edit(embed=embed)
                return
        
            existing_data = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TRIGGERS")
            if existing_data:
                triggers = json.loads(existing_data)
            else:
                triggers = {}

            if trigger not in triggers:
                embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description=f"No auto response with the word **{trigger}** exists.")
                await ctx.edit(embed=embed)
                return

            if type == "Reaction":
                split_text = response.split(":")
                result = split_text[2].rstrip(">")
                
                emoji_list = await ctx.guild.fetch_emoji(int(result))
                if not emoji_list:
                    embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="Invalid custom emoji. Please use a valid custom emoji from this server.")
                    await ctx.edit(embed=embed)
                    return
                
                response = result

            if type != "Embed":
                triggers = {"type": type, "response": response}
                await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TRIGGERS", trigger, triggers)
                embed = await db.build_embed(ctx.guild, title=f"{success_emoji} Auto Response Edited", description=f"The auto response with the word **{trigger}** has been edited.")
                await ctx.edit(embed=embed)
            else:
                user_embed = await db.build_embed(ctx.author.guild, title=f"Embed Builder", description=f"Click the buttons below to build your embed.")
                embed_tool = EmbedToolView(channel_or_message=None, is_new_embed=True, custom=f"trigger_{trigger}", view=None, ctx=ctx)
                await ctx.respond(embed=user_embed, view=embed_tool, ephemeral=True)

        except Exception as e:
            print("[trigger_edit]: ", e)

    
    @triggerSubCommands.command(name="clear", description="Clear all auto responses.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def trigger_clear(self, ctx: discord.ApplicationContext):
            
            existing_data = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TRIGGERS")
            if existing_data:
                triggers = json.loads(existing_data)
            else:
                triggers = {}
    
            if not triggers:
                embed = await db.build_embed(ctx.guild, title="<a:Information:1247223152367636541> Auto Responses", description="There are no auto responses set.")
                await ctx.respond(embed=embed, ephemeral=True)
                return
    
            for trigger in triggers:
                await db.remove_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TRIGGERS", trigger)
            embed = await db.build_embed(ctx.guild, title=f"{success_emoji} Auto Responses Cleared", description=f"All auto responses have been cleared.")
            await ctx.respond(embed=embed)

    
    @triggerSubCommands.command(name="list", description="View all auto response.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def triggers(self, ctx: discord.ApplicationContext):

        existing_data = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TRIGGERS")
        if existing_data:
            triggers = json.loads(existing_data)
        else:
            triggers = {}

        if not triggers:
            embed = await db.build_embed(ctx.guild, title="<a:Information:1247223152367636541> Auto Responses", description="There are no auto responses set.")
            await ctx.respond(embed=embed, ephemeral=True)
            return

        list = ""
        for trigger, data in triggers.items():
            if data['type'] == "Reaction":
                formatted_response = f"<:emoji:{data['response']}>"
            elif data['type'] == "Embed":
                formatted_response = "Embed"
            else:
                formatted_response = data.get('response', 'No response specified')
            list += f"**Word** ➭ {trigger}\n**Type** ➭ {data['type']}\n"
            if formatted_response != "Embed":
                list += f"**Response** ➭ {formatted_response}\n\n"
            else:
                list += "\n"

        embed = await db.build_embed(ctx.guild, title="<a:Information:1247223152367636541> Auto Responses", description=f"There are **{len(triggers)}** auto responses set.\n\n{list}")
        await ctx.respond(embed=embed)


    @inviteSubCommands.command(name="create", description="Create a new invite for the current channel.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_permissions(manage_guild=True)
    async def create_invite(self, ctx: discord.ApplicationContext, 
                            expires_after: Option(str, "When the invite should expire.", choices = ["30 Minutes", "1 Hour", "6 Hours", "12 Hours", "1 Day", "7 Days", "Never"]),
                            max_uses: Option(str, "How many times can the invite be used.", choices = ["No Limit", "1 Use", "5 Uses", "10 Uses", "25 Uses", "50 Uses", "100 Uses"]),
                            temporary: Option(bool, "Should the invite only grant a temporary membership.")):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Creating Invite", description=f"Creating a new invite for the {ctx.channel.mention} channel...")
        await ctx.respond(embed=embed)

        expire_dict = {
            "30 Minutes": 1800,
            "1 Hour": 3600,
            "6 Hours": 21600,
            "12 Hours": 43200,
            "1 Day": 86400,
            "7 Days": 604800,
            "Never": 0,
        }

        uses_dict = {
            "No Limit": 0,
            "1 Use": 1,
            "5 Uses": 5,
            "10 Uses": 10,
            "25 Uses": 25,
            "50 Uses": 50,
            "100 Uses": 100,
        }

        invite = await ctx.channel.create_invite(reason=f"Created By {ctx.author.display_name}", max_age=expire_dict[expires_after], max_uses=uses_dict[max_uses], temporary=temporary)

        creation_timestamp = int(invite.created_at.timestamp())
        max_age_timestamp = f"<t:{creation_timestamp + invite.max_age}:d> (<t:{creation_timestamp + invite.max_age}:R>)" if invite.max_age else "Never"
        max_uses = invite.max_uses if invite.max_uses else "No Limit"
        inviter = invite.inviter

        view = discord.ui.View()
        invite_link = discord.ui.Button(label="Link", url=f"https://discord.gg/{invite.code}", style=discord.ButtonStyle.link)
        view.add_item(invite_link)

        embed = await db.build_embed(invite.guild, title=f"{success_emoji} Invite Created")
        embed.set_thumbnail(url="")
        embed.add_field(name="Created By", value=inviter.name if inviter else "Unknown", inline=True)
        embed.add_field(name="Code", value=invite.code, inline=True)
        embed.add_field(name="Creation Date", value=f"<t:{creation_timestamp}:d> (<t:{creation_timestamp}:R>)", inline=True)
        embed.add_field(name="Max Uses", value=str(max_uses), inline=True)
        embed.add_field(name="Temporary", value=str(invite.temporary), inline=True)
        embed.add_field(name="Expiration", value=max_age_timestamp, inline=True) 
        await ctx.edit(embed=embed, view=view)


    @inviteSubCommands.command(name="delete", description="Delete an invite.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.bot_has_permissions(manage_guild=True)
    async def invite_delete(self, ctx: discord.ApplicationContext, invite: Option(str, "The invite to delete.", autocomplete=basic_autocomplete(Utils.get_invite_codes))):
        
        try:
            invite = invite.split(" | ")[1]
        except:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"There is no invite with the code **{invite}**.")
            return await ctx.respond(embed=embed, ephemeral=True)

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Deleting Invite", description=f"Deleting the invite with the code **{invite}**...")
        await ctx.respond(embed=embed)
        
        invite_list = await ctx.guild.invites()
        
        for invites in invite_list:
            if invites.code == invite:
                invite = invites
                break

        creation_timestamp = int(invite.created_at.timestamp())
        max_age_timestamp = f"<t:{creation_timestamp + invite.max_age}:d> (<t:{creation_timestamp + invite.max_age}:R>)" if invite.max_age else "Never"
        max_uses = invite.max_uses if invite.max_uses else "No Limit"
        inviter = invite.inviter

        embed = await db.build_embed(invite.guild, title=f"{success_emoji} Invite Deleted")
        embed.set_thumbnail(url="")
        embed.add_field(name="Created By", value=inviter.name if inviter else "Unknown", inline=True)
        embed.add_field(name="Code", value=invite.code, inline=True)
        embed.add_field(name="Creation Date", value=f"<t:{creation_timestamp}:d> (<t:{creation_timestamp}:R>)", inline=True)
        embed.add_field(name="Max Uses", value=str(max_uses), inline=True)
        embed.add_field(name="Temporary", value=str(invite.temporary), inline=True)
        embed.add_field(name="Expiration", value=max_age_timestamp, inline=True) 
        await ctx.edit(embed=embed)
        await invite.delete()

def setup(client):
    client.add_cog(say(client))