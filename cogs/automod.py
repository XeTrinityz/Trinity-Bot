# Discord Imports
from discord.utils import basic_autocomplete
from discord.ext import commands
from discord import Option
import discord

import datetime

# Local Module Imports
from utils.database import Database
from Bot import is_blocked
from utils.functions import Utils
from utils.lists import *

db = Database()

class AutoMod(commands.Cog):
    def __init__(self, client):
        self.client = client

    automodSubCommands = discord.SlashCommandGroup("automod", "Update, Delete, Spam, Mentions, Invites, Links, Profanity, Obfuscated, Pings, Custom.", default_member_permissions=discord.Permissions(manage_guild=True))
    mentionSubCommands = automodSubCommands.create_subgroup("mentions", "Configure")
    pingsSubCommands = automodSubCommands.create_subgroup("pings", "Configure")
    inviteSubCommands = automodSubCommands.create_subgroup("invites", "Configure")
    linksSubCommands = automodSubCommands.create_subgroup("links", "Configure")
    obfuscatedSubCommands = automodSubCommands.create_subgroup("obfuscated", "Configure")
    spamSubCommands = automodSubCommands.create_subgroup("spam", "Configure")
    badwordsSubCommands = automodSubCommands.create_subgroup("profanity", "Configure")
    customSubCommands = automodSubCommands.create_subgroup("custom", "Configure")

    @automodSubCommands.command(name="delete", description="Delete an AutoMod rule.")
    @commands.bot_has_permissions(manage_guild=True)
    @commands.check(is_blocked)
    @commands.guild_only()
    async def automod_delete(self, ctx: discord.ApplicationContext, rule: Option(str, "The AutoMod rule to delete.", autocomplete=basic_autocomplete(Utils.get_rules))):
        
        auto_mod_rules = await ctx.guild.fetch_auto_moderation_rules()
        matching_rule = next((rules for rules in auto_mod_rules if rules.name.lower() == rule.lower()), None)

        if matching_rule:
            await matching_rule.delete()
            embed = await db.build_embed(ctx.guild, f"{success_emoji} AutoMod Rule Deleted", f"The **{rule}** rule was deleted successfully.")
            await ctx.respond(embed=embed)
        else:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"I could not find the AutoMod rule with the name **{rule}**.")
            await ctx.respond(embed=embed, ephemeral=True)


    @automodSubCommands.command(name="update", description="Update an AutoMod rule.")
    @commands.bot_has_permissions(manage_guild=True)
    @commands.check(is_blocked)
    @commands.guild_only()
    async def automod_update(self, ctx: discord.ApplicationContext, rule: Option(str, "The AutoMod rule to update.", autocomplete=basic_autocomplete(Utils.get_rules)),
                              state: Option(bool, "Choose to enable or disable the rule.", required=False),
                              mute: Option(str, "Should the member be muted.", choices=["Don't Mute", "60 Seconds", "5 Minutes", "10 Minutes", "1 Day", "1 Week"], required=False),
                              exempt_channel: Option(discord.TextChannel | discord.CategoryChannel, "The channel to add or remove from exemption.", required=False),
                              exempt_role: Option(discord.Role, "The role to add or remove from exemption.", required=False),
                              exempt_word: Option(str, "The word to add or remove from exemption.", min_length=1, max_length = 60, required=False),
                              block_ping: Option(discord.Member | discord.Role, "The member or role to add or remove from the ping filter.", required=False),
                              block_word: Option(str, "The word to add or remove from the block list.", required=False)):
        
        auto_mod_rules = await ctx.guild.fetch_auto_moderation_rules()
        matching_rule = next((rules for rules in auto_mod_rules if rules.name.lower() == rule.lower()), None)
        
        if matching_rule:
            if state is not None:
                await matching_rule.edit(enabled=state)

            if mute:
                if matching_rule.trigger_type == discord.AutoModTriggerType.keyword or matching_rule.trigger_type == discord.AutoModTriggerType.mention_spam:
                    mute_dict = {
                        "Don't Mute": datetime.timedelta(seconds=0),
                        "60 Seconds": datetime.timedelta(seconds=60),
                        "5 Minutes": datetime.timedelta(minutes=5),
                        "10 Minutes": datetime.timedelta(minutes=10),
                        "1 Day": datetime.timedelta(days=1),
                        "1 Week": datetime.timedelta(days=7),
                    }

                    if mute == "Don't Mute":
                        matching_rule.actions = [action for action in matching_rule.actions if not isinstance(action, discord.AutoModAction) or action.type != discord.AutoModActionType.timeout]
                    else:
                        timeout_duration = mute_dict.get(mute, datetime.timedelta(seconds=0))
                        action_metadata = discord.AutoModActionMetadata(timeout_duration=timeout_duration)
                        action_mute = discord.AutoModAction(action_type=discord.AutoModActionType.timeout, metadata=action_metadata)

                        matching_rule.actions = [action for action in matching_rule.actions if not isinstance(action, discord.AutoModAction) or action.type != discord.AutoModActionType.timeout]
                        matching_rule.actions.append(action_mute)

                    await matching_rule.edit(actions=matching_rule.actions)
                else:
                    embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="This AutoMod rule does not support muting.")
                    return await ctx.respond(embed=embed, ephemeral=True)
            
            if exempt_channel is not None:
                existing_channels = matching_rule.exempt_channels
                
                if exempt_channel in existing_channels:
                    existing_channels.remove(exempt_channel)
                else:
                    existing_channels.append(exempt_channel)
                await matching_rule.edit(exempt_channels=existing_channels)

            if exempt_role is not None:
                existing_roles = matching_rule.exempt_roles
                
                if exempt_role in existing_roles:
                    existing_roles.remove(exempt_role)
                else:
                    existing_roles.append(exempt_role)
                await matching_rule.edit(exempt_roles=existing_roles)

            if exempt_word is not None:
                if matching_rule.trigger_type == discord.AutoModTriggerType.keyword:
                    existing_words = matching_rule.trigger_metadata.allow_list
                    if exempt_word in existing_words:
                        existing_words.remove(exempt_word)
                    else:
                        existing_words.append(exempt_word)

                    matching_rule.trigger_metadata.allow_list = existing_words
                    await matching_rule.edit(trigger_metadata=matching_rule.trigger_metadata)
                else:
                    embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="This AutoMod rule does not support exempt words.")
                    return await ctx.respond(embed=embed, ephemeral=True)

            if block_word is not None:
                if matching_rule.trigger_type == discord.AutoModTriggerType.keyword:
                    existing_keywords = matching_rule.trigger_metadata.keyword_filter
                    
                    if block_word in existing_keywords:
                        existing_keywords.remove(block_word)
                    else:
                        existing_keywords.append(block_word)
                    
                    matching_rule.trigger_metadata.keyword_filter = existing_keywords
                    await matching_rule.edit(trigger_metadata=matching_rule.trigger_metadata)
                else:
                    embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="This AutoMod rule does not support custom words.")
                    return await ctx.respond(embed=embed, ephemeral=True)

            if block_ping is not None:
                if matching_rule.trigger_type == discord.AutoModTriggerType.keyword:
                    existing_keywords = matching_rule.trigger_metadata.keyword_filter
                    if block_ping == ctx.guild.default_role:
                        ping = "@everyone"
                    else:
                        ping = f"<@{block_ping.id}>"
                    
                    if ping in existing_keywords:
                        existing_keywords.remove(ping)
                    else:
                        existing_keywords.append(ping)
                    
                    matching_rule.trigger_metadata.keyword_filter = existing_keywords
                    await matching_rule.edit(trigger_metadata=matching_rule.trigger_metadata)
                else:
                    embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="This AutoMod rule does not support custom words.")
                    return await ctx.respond(embed=embed, ephemeral=True)

            embed = await db.build_embed(ctx.guild, f"{success_emoji} AutoMod Rule Updated", f"The **{rule}** rule was updated successfully.")
            await ctx.respond(embed=embed)
        else:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"I could not find the AutoMod rule with the name **{rule}**.")
            await ctx.respond(embed=embed, ephemeral=True)


    @mentionSubCommands.command(name="configure", description="Configure the anti mass mention rule.")
    @commands.bot_has_permissions(manage_guild=True)
    @commands.check(is_blocked)
    @commands.guild_only()
    async def mentions_config(self, ctx: discord.ApplicationContext, 
                              mention_limit: Option(int, "The limit of unique mentions allowed in a message.", min_value=1, max_value=50),
                              mute: Option(str, "Should the member be muted.", choices=["Don't Mute", "60 Seconds", "5 Minutes", "10 Minutes", "1 Day", "1 Week"])):
        
        auto_mod_rules = await ctx.guild.fetch_auto_moderation_rules()
        for rules in auto_mod_rules:
            if rules.trigger_type == discord.AutoModTriggerType.mention_spam:
                await rules.delete()

        rule_name = "[Trinity] Anti Mass Mentions"
        event_type = discord.AutoModEventType.message_send
        trigger_type = discord.AutoModTriggerType.mention_spam
        trigger_metadata = discord.AutoModTriggerMetadata(mention_total_limit=mention_limit)

        # Define the action to be taken when the rule is triggered
        mute_dict = {
            "Don't Mute": datetime.timedelta(seconds=0),
            "60 Seconds": datetime.timedelta(seconds=60),
            "5 Minutes": datetime.timedelta(minutes=5),
            "10 Minutes": datetime.timedelta(minutes=10),
            "1 Day": datetime.timedelta(days=1),
            "1 Week": datetime.timedelta(days=7),
        }

        timeout_duration = mute_dict[mute]
        action_metadata = discord.AutoModActionMetadata(
            timeout_duration=timeout_duration,
        )
        action_block = discord.AutoModAction(
            action_type=discord.AutoModActionType.block_message,
            metadata=action_metadata
        )
        if mute != "Don't Mute":
            action_mute = discord.AutoModAction(
                action_type=discord.AutoModActionType.timeout,
                metadata=action_metadata
            )

        await ctx.guild.create_auto_moderation_rule(
            name=rule_name,
            event_type=event_type,
            trigger_type=trigger_type,
            trigger_metadata=trigger_metadata,
            actions=[action_block, action_mute] if mute != "Don't Mute" else [action_block],
            enabled=True,
            reason="Trinity's Anti Mass Mention Rule"
        )

        embed = await db.build_embed(ctx.guild, f"{success_emoji} AutoMod Rule Created", "The **Anti Mass Mention** rule was created successfully.")
        await ctx.respond(embed=embed)


    @inviteSubCommands.command(name="configure", description="Configure the anti invite rule.")
    @commands.bot_has_permissions(manage_guild=True)
    @commands.check(is_blocked)
    @commands.guild_only()
    async def invite_config(self, ctx: discord.ApplicationContext, 
                            mute: Option(str, "Should the member be muted.", choices=["Don't Mute", "60 Seconds", "5 Minutes", "10 Minutes", "1 Day", "1 Week"])):
        
        auto_mod_rules = await ctx.guild.fetch_auto_moderation_rules()
        matching_rule = next((rule for rule in auto_mod_rules if "invite" in rule.name.lower()), None)

        rule_name = "[Trinity] Anti Invite Links"
        event_type = discord.AutoModEventType.message_send
        trigger_type = discord.AutoModTriggerType.keyword
        trigger_metadata = discord.AutoModTriggerMetadata(regex_patterns=["(?:https?://)?(?:www.|ptb.|canary.)?(?:discord(?:app)?.(?:(?:com|gg)/(?:invite|servers)/[a-z0-9-_]+)|discord.gg/[a-z0-9-_]+)|(?:https?://)?(?:www.)?(?:dsc.gg|invite.gg+|discord.link|(?:discord.(gg|io|me|li|id))|disboard.org)/[a-z0-9-_/]+"])

        # Define the action to be taken when the rule is triggered
        mute_dict = {
            "Don't Mute": datetime.timedelta(seconds=0),
            "60 Seconds": datetime.timedelta(seconds=60),
            "5 Minutes": datetime.timedelta(minutes=5),
            "10 Minutes": datetime.timedelta(minutes=10),
            "1 Day": datetime.timedelta(days=1),
            "1 Week": datetime.timedelta(days=7),
        }

        timeout_duration = mute_dict[mute]
        action_metadata = discord.AutoModActionMetadata(
            timeout_duration=timeout_duration,
        )
        action_block = discord.AutoModAction(
            action_type=discord.AutoModActionType.block_message,
            metadata=action_metadata
        )
        if mute != "Don't Mute":
            action_mute = discord.AutoModAction(
                action_type=discord.AutoModActionType.timeout,
                metadata=action_metadata
            )

        # Create the auto moderation rule
        if matching_rule:
            await matching_rule.edit(
            name=rule_name,
            event_type=event_type,
            trigger_metadata=trigger_metadata,
            actions=[action_block, action_mute] if mute != "Don't Mute" else [action_block],
            enabled=True,
            reason="Trinity's Anti Invite Links Rule"
            )
        else:
            await ctx.guild.create_auto_moderation_rule(
                name=rule_name,
                event_type=event_type,
                trigger_type=trigger_type,
                trigger_metadata=trigger_metadata,
                actions=[action_block, action_mute] if mute != "Don't Mute" else [action_block],
                enabled=True,
                reason="Trinity's Anti Invite Link Rule"
            )

        embed = await db.build_embed(ctx.guild, f"{success_emoji} AutoMod Rule Created", "The **Anti Invite Link** rule was created successfully.")
        await ctx.respond(embed=embed)


    @pingsSubCommands.command(name="configure", description="Configure the ping filter rule.")
    @commands.bot_has_permissions(manage_guild=True)
    @commands.check(is_blocked)
    @commands.guild_only()
    async def everyonehere_config(self, ctx: discord.ApplicationContext, 
                            ping: Option(discord.Member | discord.Role, "Select a member or role the rule should block from being pinged."),
                            mute: Option(str, "Should the member be muted.", choices=["Don't Mute", "60 Seconds", "5 Minutes", "10 Minutes", "1 Day", "1 Week"])):
        
        auto_mod_rules = await ctx.guild.fetch_auto_moderation_rules()
        matching_rule = next((rule for rule in auto_mod_rules if "ping" in rule.name.lower()), None)

        rule_name = "[Trinity] Ping Filter"
        event_type = discord.AutoModEventType.message_send
        trigger_type = discord.AutoModTriggerType.keyword

        if ping == ctx.guild.default_role:
            keyword_ping = "@everyone"
        else:
            keyword_ping = f"<@{ping.id}>" 
            
        trigger_metadata = discord.AutoModTriggerMetadata(keyword_filter=[keyword_ping])

        # Define the action to be taken when the rule is triggered
        mute_dict = {
            "Don't Mute": datetime.timedelta(seconds=0),
            "60 Seconds": datetime.timedelta(seconds=60),
            "5 Minutes": datetime.timedelta(minutes=5),
            "10 Minutes": datetime.timedelta(minutes=10),
            "1 Day": datetime.timedelta(days=1),
            "1 Week": datetime.timedelta(days=7),
        }

        timeout_duration = mute_dict[mute]
        action_metadata = discord.AutoModActionMetadata(
            timeout_duration=timeout_duration,
        )
        action_block = discord.AutoModAction(
            action_type=discord.AutoModActionType.block_message,
            metadata=action_metadata
        )
        if mute != "Don't Mute":
            action_mute = discord.AutoModAction(
                action_type=discord.AutoModActionType.timeout,
                metadata=action_metadata
            )

        # Create the auto moderation rule
        if matching_rule:
            await matching_rule.edit(
            name=rule_name,
            event_type=event_type,
            trigger_metadata=trigger_metadata,
            actions=[action_block, action_mute] if mute != "Don't Mute" else [action_block],
            enabled=True,
            reason="Trinity's Ping Filter Rule"
            )
        else:
            await ctx.guild.create_auto_moderation_rule(
                name=rule_name,
                event_type=event_type,
                trigger_type=trigger_type,
                trigger_metadata=trigger_metadata,
                actions=[action_block, action_mute] if mute != "Don't Mute" else [action_block],
                enabled=True,
                reason="Trinity's Ping Filter Rule"
            )

        embed = await db.build_embed(ctx.guild, f"{success_emoji} AutoMod Rule Created", "The **Ping Filter** rule was created successfully. If you would like to block additional pings, use </automod update:1175203997875978281>.")
        await ctx.respond(embed=embed)


    @customSubCommands.command(name="configure", description="Configure the custom word filter rule.")
    @commands.bot_has_permissions(manage_guild=True)
    @commands.check(is_blocked)
    @commands.guild_only()
    async def custom_config(self, ctx: discord.ApplicationContext, 
                            keyword: Option(str, "The keyword the rule should block.", min_length=1, max_length=60),
                            mute: Option(str, "Should the member be muted.", choices=["Don't Mute", "60 Seconds", "5 Minutes", "10 Minutes", "1 Day", "1 Week"])):
        
        auto_mod_rules = await ctx.guild.fetch_auto_moderation_rules()
        matching_rule = next((rule for rule in auto_mod_rules if "custom word" in rule.name.lower()), None)

        rule_name = "[Trinity] Custom Word Filter"
        event_type = discord.AutoModEventType.message_send
        trigger_type = discord.AutoModTriggerType.keyword
        trigger_metadata = discord.AutoModTriggerMetadata(keyword_filter=[keyword])

        # Define the action to be taken when the rule is triggered
        mute_dict = {
            "Don't Mute": datetime.timedelta(seconds=0),
            "60 Seconds": datetime.timedelta(seconds=60),
            "5 Minutes": datetime.timedelta(minutes=5),
            "10 Minutes": datetime.timedelta(minutes=10),
            "1 Day": datetime.timedelta(days=1),
            "1 Week": datetime.timedelta(days=7),
        }

        timeout_duration = mute_dict[mute]
        action_metadata = discord.AutoModActionMetadata(
            timeout_duration=timeout_duration,
        )
        action_block = discord.AutoModAction(
            action_type=discord.AutoModActionType.block_message,
            metadata=action_metadata
        )
        if mute != "Don't Mute":
            action_mute = discord.AutoModAction(
                action_type=discord.AutoModActionType.timeout,
                metadata=action_metadata
            )

        # Create the auto moderation rule
        if matching_rule:
            await matching_rule.edit(
            name=rule_name,
            event_type=event_type,
            trigger_metadata=trigger_metadata,
            actions=[action_block, action_mute] if mute != "Don't Mute" else [action_block],
            enabled=True,
            reason="Trinity's Custom Word Filter Rule"
            )
        else:
            await ctx.guild.create_auto_moderation_rule(
                name=rule_name,
                event_type=event_type,
                trigger_type=trigger_type,
                trigger_metadata=trigger_metadata,
                actions=[action_block, action_mute] if mute != "Don't Mute" else [action_block],
                enabled=True,
                reason="Trinity's Custom Word Filter Rule"
            )

        embed = await db.build_embed(ctx.guild, f"{success_emoji} AutoMod Rule Created", "The **Custom Word Filter** rule was created successfully. If you would like to block additional words, use </automod update:1175203997875978281>.")
        await ctx.respond(embed=embed)


    @linksSubCommands.command(name="configure", description="Configure the anti link rule.")
    @commands.bot_has_permissions(manage_guild=True)
    @commands.check(is_blocked)
    @commands.guild_only()
    async def links_config(self, ctx: discord.ApplicationContext, 
                            links: Option(bool, "Should this rule block all links."),
                            hyperlinks: Option(bool, "Should this rule block all hyperlinks."),
                            ignore_gifs: Option(bool, "Should this rule ignore gifs."),
                            mute: Option(str, "Should the member be muted.", choices=["Don't Mute", "60 Seconds", "5 Minutes", "10 Minutes", "1 Day", "1 Week"])):
        
        if links == False and hyperlinks == False:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Please enable at least one option between links/hyperlinks links.")
            return await ctx.respond(embed=embed)
        
        auto_mod_rules = await ctx.guild.fetch_auto_moderation_rules()
        matching_rule = next((rule for rule in auto_mod_rules if "anti link" in rule.name.lower()), None)

        rule_name = "[Trinity] Anti Links"
        event_type = discord.AutoModEventType.message_send
        trigger_type = discord.AutoModTriggerType.keyword

        # Set up trigger_metadata with optional options
        regex_patterns = []

        if links:
            regex_patterns.append("(?:https?://)[a-z0-9_\-\.]*[a-z0-9_\-]+(?:\.[a-z]{2,})?(?:\/[^\s]*)?\/?")

        if hyperlinks:
            regex_patterns.append("\[.*\]\(<?(?:https?://)?[a-z0-9_\-\.]*[a-z0-9_\-]+\.[a-z]{2,}.*>?\)")
        
        trigger_metadata = discord.AutoModTriggerMetadata(regex_patterns=regex_patterns, allow_list=["*media.discordapp.net*", "*tenor.com*", "*giphy.com*"] if ignore_gifs else [])

        # Define the action to be taken when the rule is triggered
        mute_dict = {
            "Don't Mute": datetime.timedelta(seconds=0),
            "60 Seconds": datetime.timedelta(seconds=60),
            "5 Minutes": datetime.timedelta(minutes=5),
            "10 Minutes": datetime.timedelta(minutes=10),
            "1 Day": datetime.timedelta(days=1),
            "1 Week": datetime.timedelta(days=7),
        }

        timeout_duration = mute_dict[mute]
        action_metadata = discord.AutoModActionMetadata(
            timeout_duration=timeout_duration,
        )
        action_block = discord.AutoModAction(
            action_type=discord.AutoModActionType.block_message,
            metadata=action_metadata
        )
        if mute != "Don't Mute":
            action_mute = discord.AutoModAction(
                action_type=discord.AutoModActionType.timeout,
                metadata=action_metadata
            )

        # Create the auto moderation rule
        if matching_rule:
            await matching_rule.edit(
            name=rule_name,
            event_type=event_type,
            trigger_metadata=trigger_metadata,
            actions=[action_block, action_mute] if mute != "Don't Mute" else [action_block],
            enabled=True,
            reason="Trinity's Anti Link Rule"
            )
        else:
            await ctx.guild.create_auto_moderation_rule(
                name=rule_name,
                event_type=event_type,
                trigger_type=trigger_type,
                trigger_metadata=trigger_metadata,
                actions=[action_block, action_mute] if mute != "Don't Mute" else [action_block],
                enabled=True,
                reason="Trinity's Anti Link Rule"
            )

        embed = await db.build_embed(ctx.guild, f"{success_emoji} AutoMod Rule Created", "The **Anti Link** rule was created successfully.")
        await ctx.respond(embed=embed)


    @obfuscatedSubCommands.command(name="configure", description="Configure the obfuscated word filter.")
    @commands.bot_has_permissions(manage_guild=True)
    @commands.check(is_blocked)
    @commands.guild_only()
    async def custom_config(self, ctx: discord.ApplicationContext, 
                            mute: Option(str, "Should the member be muted.", choices=["Don't Mute", "60 Seconds", "5 Minutes", "10 Minutes", "1 Day", "1 Week"])):
        
        auto_mod_rules = await ctx.guild.fetch_auto_moderation_rules()
        matching_rule = next((rule for rule in auto_mod_rules if "obfuscated" in rule.name.lower()), None)

        rule_name = "[Trinity] Obfuscated Word Filter"
        event_type = discord.AutoModEventType.message_send
        trigger_type = discord.AutoModTriggerType.keyword
        
        trigger_metadata = discord.AutoModTriggerMetadata(regex_patterns=["\p{M}{3,}", "(?:\|\|​\|\|\s*){120,}"])

        # Define the action to be taken when the rule is triggered
        mute_dict = {
            "Don't Mute": datetime.timedelta(seconds=0),
            "60 Seconds": datetime.timedelta(seconds=60),
            "5 Minutes": datetime.timedelta(minutes=5),
            "10 Minutes": datetime.timedelta(minutes=10),
            "1 Day": datetime.timedelta(days=1),
            "1 Week": datetime.timedelta(days=7),
        }

        timeout_duration = mute_dict[mute]
        action_metadata = discord.AutoModActionMetadata(
            timeout_duration=timeout_duration,
        )
        action_block = discord.AutoModAction(
            action_type=discord.AutoModActionType.block_message,
            metadata=action_metadata
        )
        if mute != "Don't Mute":
            action_mute = discord.AutoModAction(
                action_type=discord.AutoModActionType.timeout,
                metadata=action_metadata
            )

        # Create the auto moderation rule
        if matching_rule:
            await matching_rule.edit(
            name=rule_name,
            event_type=event_type,
            trigger_metadata=trigger_metadata,
            actions=[action_block, action_mute] if mute != "Don't Mute" else [action_block],
            enabled=True,
            reason="Trinity's Obfuscated Word Filter Rule"
            )
        else:
            await ctx.guild.create_auto_moderation_rule(
                name=rule_name,
                event_type=event_type,
                trigger_type=trigger_type,
                trigger_metadata=trigger_metadata,
                actions=[action_block, action_mute] if mute != "Don't Mute" else [action_block],
                enabled=True,
                reason="Trinity's Obfuscated Word Filter Rule"
            )

        embed = await db.build_embed(ctx.guild, f"{success_emoji} AutoMod Rule Created", "The **Obfuscated Word Filter** rule was created successfully.")
        await ctx.respond(embed=embed)


    @spamSubCommands.command(name="configure", description="Configure the spam content filter rule.")
    @commands.bot_has_permissions(manage_guild=True)
    @commands.check(is_blocked)
    @commands.guild_only()
    async def spam_config(self, ctx: discord.ApplicationContext):
        
        matching_rule = None
        auto_mod_rules = await ctx.guild.fetch_auto_moderation_rules()
        for rules in auto_mod_rules:
            if rules.trigger_type == discord.AutoModTriggerType.spam:
                matching_rule = rules

        rule_name = "[Trinity] Spam Content Filter"
        event_type = discord.AutoModEventType.message_send
        trigger_type = discord.AutoModTriggerType.spam
        trigger_metadata = discord.AutoModTriggerMetadata(presets=[])

        # Define the action to be taken when the rule is triggered
        timeout_duration = datetime.timedelta(minutes=5)
        action_metadata = discord.AutoModActionMetadata(
            timeout_duration=timeout_duration,
        )
        action_block = discord.AutoModAction(
            action_type=discord.AutoModActionType.block_message,
            metadata=action_metadata
        )

        if matching_rule:
            await matching_rule.edit(
                name=rule_name,
                event_type=event_type,
                trigger_metadata=trigger_metadata,
                actions=[action_block],
                enabled=True,
                reason="Trinity's Spam Content Filter Rule"
            )
        else:
            await ctx.guild.create_auto_moderation_rule(
                name=rule_name,
                event_type=event_type,
                trigger_type=trigger_type,
                trigger_metadata=trigger_metadata,
                actions=[action_block],
                enabled=True,
                reason="Trinity's Spam Content Filter Rule"
            )

        embed = await db.build_embed(ctx.guild, f"{success_emoji} AutoMod Rule Created", "The **Anti Spam Content** rule was created successfully.")
        await ctx.respond(embed=embed)


    @badwordsSubCommands.command(name="configure", description="Configure the bad word filter rule.")
    @commands.bot_has_permissions(manage_guild=True)
    @commands.check(is_blocked)
    @commands.guild_only()
    async def badword_config(self, ctx: discord.ApplicationContext, 
                            profanity: Option(bool, "Should profanity be blocked."),
                            slurs: Option(bool, "Should slurs be blocked."),
                            sexual_content: Option(bool, "Should sexual content be blocked.")):
        
        matching_rule = None
        auto_mod_rules = await ctx.guild.fetch_auto_moderation_rules()
        for rules in auto_mod_rules:
            if rules.trigger_type == discord.AutoModTriggerType.keyword_preset:
                matching_rule = rules

        rule_name = "[Trinity] Bad Word Filter"
        event_type = discord.AutoModEventType.message_send
        trigger_type = discord.AutoModTriggerType.keyword_preset
        
        # Define trigger presets based on user input
        presets = []
        if profanity:
            presets.append(discord.AutoModKeywordPresetType.profanity)
        if slurs:
            presets.append(discord.AutoModKeywordPresetType.slurs)
        if sexual_content:
            presets.append(discord.AutoModKeywordPresetType.sexual_content)

        # Define the action to be taken when the rule is triggered
        action_metadata = discord.AutoModActionMetadata(
        )
        action_block = discord.AutoModAction(
            action_type=discord.AutoModActionType.block_message,
            metadata=action_metadata
        )

        # Create the auto moderation rule
        if matching_rule:
            await matching_rule.edit(
            name=rule_name,
            event_type=event_type,
            trigger_metadata=discord.AutoModTriggerMetadata(presets=presets),
            actions=[action_block],
            enabled=True,
            reason="Trinity's Bad Word Filter Rule"
            )
        else:
            await ctx.guild.create_auto_moderation_rule(
                name=rule_name,
                event_type=event_type,
                trigger_type=trigger_type,
                trigger_metadata=discord.AutoModTriggerMetadata(presets=presets),
                actions=[action_block],
                enabled=True,
                reason="Trinity's Bad Word Filter Rule"
            )

        embed = await db.build_embed(ctx.guild, f"{success_emoji} AutoMod Rule Created", "The **Bad Word Filter** rule was created successfully.")
        await ctx.respond(embed=embed)


def setup(client):
    client.add_cog(AutoMod(client))