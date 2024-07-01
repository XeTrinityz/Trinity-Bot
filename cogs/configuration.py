# Discord Imports
from discord.ext import commands, pages
from discord import Option
import discord

# Standard / Third-Party Library Imports
from validators import url as is_valid_url
import json

# Local Module Imports
from utils.database import Database
from utils.functions import Utils
from Bot import is_blocked
from utils.lists import *

db = Database()

class Configuration(commands.Cog):
    def __init__(self, client):
        self.client = client

    conSubCommands = discord.SlashCommandGroup("configure", "Embed, Channels, Counters, Protections, Roles, Self Roles, Stats, Toggles.", default_member_permissions=discord.Permissions(administrator=True))

    @commands.slash_command(name="config", description="Read settings for a specific category.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @discord.default_permissions(administrator=True)
    async def read_settings(self, ctx: discord.ApplicationContext, category: Option(str, "The category of settings to read", choices=["All", "Embed", "Toggles", "Channels", "Counters", "Roles", "Protections"], required=True)):
        await ctx.defer()

        feature_mapping = {
            "Toggles": "TOGGLES",
            "Protections": "PROTECTIONS",
            "Embed": "EMBED",
            "Channels": "CHANNELS",
            "Counters": "COUNTERS",
            "Roles": "ROLES",
        }
                    
        data_type_formatters = {
            bool: lambda value: "✓" if value else "✗",
            int: lambda value: str(value),
        }

        rules = await ctx.guild.fetch_auto_moderation_rules()
        rule_list = [f"**{rule.name}** ➭ ✓" if rule.enabled else f"**{rule.name}** ➭ ✗" for rule in rules]
        auto_mod_rules = "\n".join(rule_list)

        try:
            # Check if the category is "All" to display all categories
            if category == "All":
                all_categories = ["Embed", "Toggles", "Channels", "Counters", "Roles", "Protections"]
                # Create a list of embeds for each category
                category_embeds = []

                for category_name in all_categories:
                    category_configuration = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", feature_mapping.get(category_name))
                    if category_configuration:
                        category_configuration = json.loads(category_configuration)
                    else:
                        category_configuration = {}

                    # Create an embed for each category
                    title = f"<a:Information:1247223152367636541> Server Config | {category_name}"
                    embed = await db.build_embed(ctx.author.guild, title=title, description="")
                    
                    # Add settings to the embed description with dynamic names
                    for setting, value in category_configuration.items():
                        if value is None:
                            value = "None"
                        else:
                            # Format channels and roles as mentions
                            if feature_mapping.get(category_name) == "CHANNELS" or feature_mapping.get(category_name) == "COUNTERS":
                                value = f"<#{value}>"
                            elif feature_mapping.get(category_name) == "ROLES":
                                value = f"<@&{value}>"
                            elif setting == "footer_icon" or setting == "author_icon":
                                value = f"[Click Here]({value})"
                            else:
                                data_type_formatter = data_type_formatters.get(type(value), str)
                                value = data_type_formatter(value)

                        embed.description += f"**{setting.replace('_', ' ').title()}** ➭ {value}\n"
                    
                    if auto_mod_rules and feature_mapping.get(category_name) == "PROTECTIONS":
                        embed.description += f"\n**__AutoMod Rules__**\n{auto_mod_rules}\n"

                    category_embeds.append(embed)

                # Create a paginator with the list of category embeds
                paginator = pages.Paginator(pages=category_embeds, disable_on_timeout=True, use_default_buttons=False, show_indicator=True, loop_pages=True, timeout=60)
                if len(category_embeds) > 10:
                    paginator.add_button(pages.PaginatorButton("first", label="", emoji="<a:First:1182373753498370069>", style=discord.ButtonStyle.grey))
                paginator.add_button(pages.PaginatorButton("prev", label="", emoji="<a:LeftArrow:1156039371624026112>", style=discord.ButtonStyle.grey))
                paginator.add_button(pages.PaginatorButton("page_indicator", style=discord.ButtonStyle.gray, disabled=True))
                paginator.add_button(pages.PaginatorButton("next", label="", emoji="<a:RightArrow:1156039369875001385>", style=discord.ButtonStyle.grey))
                if len(category_embeds) > 10:
                    paginator.add_button(pages.PaginatorButton("last", label="", emoji="<a:Last:1182374111306063902>", style=discord.ButtonStyle.grey))
                await paginator.respond(ctx.interaction)

            else:
                # Display settings for the specified category
                feature = feature_mapping.get(category)
                if not feature:
                    raise commands.BadArgument("Invalid category.")

                category_configuration = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", feature)
                if category_configuration:
                    category_configuration = json.loads(category_configuration)

                # Create an embed to display the category configuration
                title = f"<a:Information:1247223152367636541> Server Config | {category}"
                embed = await db.build_embed(ctx.author.guild, title=title, description="")

                # Add settings to the embed description with dynamic names
                for setting, value in category_configuration.items():
                    if value is None:
                        value = "None"
                    else:
                        # Format channels and roles as mentions
                        if feature == "CHANNELS" or feature == "COUNTERS":
                            value = f"<#{value}>"
                        elif feature == "ROLES":
                            value = f"<@&{value}>"
                        elif setting == "footer_icon" or setting == "author_icon":
                            value = f"[Click Here]({value})"
                        else:
                            data_type_formatter = data_type_formatters.get(type(value), str)
                            value = data_type_formatter(value)

                    embed.description += f"**{setting.replace('_', ' ').title()}** ➭ {value}\n"

                if auto_mod_rules and feature == "PROTECTIONS":
                    embed.description += f"\n**__AutoMod Rules__**\n{auto_mod_rules}\n"

                await ctx.respond(embed=embed)

        except commands.BadArgument as bad_arg:
            # Create an embed for the error message
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=str(bad_arg))
            await ctx.respond(embed=embed)

        except Exception as e:
            print(f"[Config > {category}]: {e}")
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="An error occurred and the developer was informed.")
            await ctx.respond(embed=embed)


    @conSubCommands.command(name="toggles", description="Configure toggle settings.")
    @commands.bot_has_permissions(manage_channels=True, view_audit_log=True, manage_roles=True, manage_messages=True)
    @commands.check(is_blocked)
    @commands.guild_only()
    async def toggles(self, ctx: discord.ApplicationContext, setting: Option(str, "The toggle setting to configure", choices=["Welcome Messages", "Audit Logs", "Auto Roles", "XP System", "Chatbot", "Suggestions", "Message Link Embedding"], required=True), value: Option(bool, "Toggle the setting on or off", required=True)):
        await ctx.defer()
        
        # Define the database feature and column mapping
        feature = "TOGGLES"
        column_mapping = {
            "Welcome Messages": "welcome_messages",
            "Audit Logs": "audit_logs",
            "Auto Roles": "auto_roles",
            "XP System": "xp_system",
            "Chatbot": "chatbot",
            "Suggestions": "suggestions",
            "Message Link Embedding": "message_link_embed",
        }

        try:
            # Get the current toggle configuration
            channel_configuration = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")
            role_configuration = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "ROLES")
            if channel_configuration and role_configuration:
                channel_configuration = json.loads(channel_configuration)
                role_configuration = json.loads(role_configuration)

                welcome_channel = channel_configuration.get("welcome_channel")
                audit_log_channel = channel_configuration.get("audit_log_channel")
                auto_role = role_configuration.get("auto_role")
                chatbot_channel = channel_configuration.get("chatbot_channel")
                suggestion_channel = channel_configuration.get("suggestion_channel")

            if setting == "Welcome Messages" and value and not welcome_channel:
                raise commands.BadArgument("Please set a welcome channel first.")
            elif setting == "Audit Logs" and value and not audit_log_channel:
                raise commands.BadArgument("Please set an audit log channel first.")
            elif setting == "Auto Roles" and value and not auto_role:
                raise commands.BadArgument("Please set an auto role first.")
            elif setting == "Chatbot" and value and not chatbot_channel:
                raise commands.BadArgument("Please set a chatbot channel first.")
            elif setting == "Suggestions" and value and not suggestion_channel:
                raise commands.BadArgument("Please set a suggestion channel first.")

            toggle_configuration = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", feature)
            if toggle_configuration:
                toggle_configuration = json.loads(toggle_configuration)
            else:
                toggle_configuration = {}

            # Map the setting to the appropriate column name
            column_name = column_mapping.get(setting)
            if not column_name:
                raise commands.BadArgument("Invalid setting.")

            # Update the toggle configuration in the database
            toggle_configuration[column_name] = value
            await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", feature, column_name, value)
            
            # Create an embed for the response
            embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Toggle Setting Updated",
                                          description=f"The **{setting}** setting has been {'**enabled**' if value else '**disabled**'}.")
            await ctx.respond(embed=embed)

        except commands.BadArgument as bad_arg:
            # Create an embed for the error message
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=str(bad_arg))
            await ctx.respond(embed=embed)

        except Exception as e:
            print("[Configure > Toggles]: ", e)
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="An error occurred and the developer was informed.")
            await ctx.respond(embed=embed)


    @conSubCommands.command(name="roles", description="Configure role settings.")
    @commands.bot_has_permissions(manage_roles=True)
    @commands.check(is_blocked)
    @commands.guild_only()
    async def roles(self, ctx: discord.ApplicationContext, setting: Option(str, "The role setting to configure", choices=["Auto Role", "Verified Role", "Custom Role Counter"], required=True), role: Option(discord.Role, "The role to set.", required=True)):
        await ctx.defer()

        # Define the database feature and column mapping
        feature = "ROLES"
        column_mapping = {
            "Auto Role": "auto_role",
            "Verified Role": "verified_role",
            "Custom Role Counter": "custom_role_counter",
        }

        bot_top_role = ctx.guild.me.top_role.position
        role_position = role.position
        if bot_top_role < role_position:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Please make sure the bots role is above the selected role.")
            return await ctx.respond(embed=embed, ephemeral=True)

        try:
            # Get the current role configuration
            role_configuration = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", feature)
            if role_configuration:
                role_configuration = json.loads(role_configuration)
            else:
                role_configuration = {}

            # Map the setting to the appropriate column name
            column_name = column_mapping.get(setting)
            if not column_name:
                raise commands.BadArgument("Invalid setting.")

            # Update the role configuration in the database
            role_configuration[column_name] = role.id
            await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", feature, column_name, role.id)

            if setting == "Auto Role":
                await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", "auto_roles", True)

            # Create an embed for the response
            embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Role Setting Updated",
                                          description=f"The **{setting}** setting has been set to {role.mention}{' and **enabled**' if setting == 'Auto Role' else ''}.")
            await ctx.respond(embed=embed)

        except commands.BadArgument as bad_arg:
            # Create an embed for the error message
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=str(bad_arg))
            await ctx.respond(embed=embed)

        except Exception as e:
            print("[Configure > Roles]: ", e)
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="An error occurred and the developer was informed.")
            await ctx.respond(embed=embed)


    @conSubCommands.command(name="protections", description="Configure protection settings.")
    @commands.bot_has_permissions(manage_messages=True, moderate_members=True)
    @commands.check(is_blocked)
    @commands.guild_only()
    async def protections(self, ctx: discord.ApplicationContext, setting: Option(str, "The protection setting to configure", choices=["Anti Spam", "Anti Ghost Ping", "Anti Selfbot", "Anti Raid"], required=True), value: Option(bool, "The value to set (true or false)", required=True)):
        await ctx.defer()
        
        # Define the database feature and column mapping
        feature = "PROTECTIONS"
        column_mapping = {
            "Anti Spam": "anti_spam",
            "Anti Ghost Ping": "anti_ghost_ping",
            "Anti Selfbot": "anti_selfbot",
            "Anti Raid": "anti_raid",
        }

        try:
            # Get the current protection configuration
            protection_configuration = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", feature)
            if protection_configuration:
                protection_configuration = json.loads(protection_configuration)
            else:
                protection_configuration = {}

            # Map the setting to the appropriate column name
            column_name = column_mapping.get(setting)
            if not column_name:
                raise commands.BadArgument("Invalid setting.")

            # Update the protection configuration in the database
            protection_configuration[column_name] = value
            await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", feature, column_name, value)

            # Create an embed for the response
            embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Protection Setting Updated",
                                          description=f"The **{setting}** setting has been {'**enabled**' if value else '**disabled**'}.")
            await ctx.respond(embed=embed)

        except commands.BadArgument as bad_arg:
            # Create an embed for the error message
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=str(bad_arg))
            await ctx.respond(embed=embed)

        except Exception as e:
            print("[Configure > Protections]: ", e)
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="An error occurred and the developer was informed.")
            await ctx.respond(embed=embed)


    @conSubCommands.command(name="channels", description="Configure channel settings.")
    @commands.bot_has_permissions(view_audit_log=True, manage_messages=True, manage_channels=True)
    @commands.check(is_blocked)
    @commands.guild_only()
    async def channels(self, ctx: discord.ApplicationContext, setting: Option(str, "The setting to configure", choices=["Welcome Channel", "Audit Log Channel", "Moderation Log Channel", "Suggestion Channel", "Starboard Channel", "Chatbot Channel"], required=True),channel: Option(discord.TextChannel, "The channel to set", required=True)):
        await ctx.defer()

        # Define the database feature and column mapping
        feature = "CHANNELS"
        column_mapping = {
            "Welcome Channel": "welcome_channel",
            "Audit Log Channel": "audit_log_channel",
            "Moderation Log Channel": "moderation_log_channel",
            "Suggestion Channel": "suggestion_channel",
            "Starboard Channel": "starboard_channel",
            "Chatbot Channel": "chatbot_channel"
        }

        column_mapping_toggles = {
            "Welcome Channel": "welcome_messages",
            "Audit Log Channel": "audit_logs",
            "Suggestion Channel": "suggestions",
            "Chatbot Channel": "chatbot",
        }

        try:
            # Get the current channel configuration
            channel_configuration = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", feature)
            if channel_configuration:
                channel_configuration = json.loads(channel_configuration)
            else:
                channel_configuration = {}

            # Map the setting to the appropriate column name
            column_name = column_mapping.get(setting)
            if not column_name:
                raise commands.BadArgument("Invalid setting.")

            # Update the channel configuration in the database
            channel_configuration[column_name] = channel.id if channel else None
            await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", feature, column_name, channel_configuration[column_name])

            if setting == "Welcome Channel" or setting == "Audit Log Channel" or setting == "Suggestion Channel" or setting == "Chatbot Channel":
                await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "TOGGLES", column_mapping_toggles[setting], True)
            
            if setting == "Chatbot Channel":
                await channel.edit(slowmode_delay=30)
                
            # Create an embed for the response
            embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Channel Setting Updated",
                                          description=f"The **{setting}** setting has been updated to {channel.mention}{' and **enabled**' if setting == 'Welcome Channel' or setting == 'Audit Log Channel' or setting == 'Chatbot Channel' or setting == 'Suggestion Channel' else ''}.")
            await ctx.respond(embed=embed)

        except commands.BadArgument as bad_arg:
            # Create an embed for the error message
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=str(bad_arg))
            await ctx.respond(embed=embed)

        except Exception as e:
            print("[Configure > Channels]: ", e)
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="An error occurred and the developer was informed.")
            await ctx.respond(embed=embed)


    @conSubCommands.command(name="counters", description="Configure counter settings.")
    @commands.bot_has_permissions(manage_channels=True)
    @commands.check(is_blocked)
    @commands.guild_only()
    async def counters(self, ctx: discord.ApplicationContext, text: Option(str, "The counter text | e.g. Members"), setting: Option(str, "The setting to configure", choices=["Member Counter", "Resolved Ticket Counter", "Active Ticket Counter", "Role Counter", "Custom Role Counter"], required=True), channel: Option(discord.VoiceChannel, "The channel to set", required=True)):
        await ctx.defer()

        feature = "COUNTERS"
        column_mapping = {
            "Member Counter": "member_counter",
            "Resolved Ticket Counter": "resolved_ticket_counter",
            "Active Ticket Counter": "active_ticket_counter",
            "Role Counter": "role_counter",
            "Custom Role Counter": "custom_role_counter",
        }

        embed = await db.build_embed(ctx.author.guild, title="<a:Nuke:1153887377165656114> Updating Counter", description=f"Updating {channel.mention} to the **{setting}** counter...")
        await ctx.respond(embed=embed)

        try:
            counter_configuration = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", feature)
            if counter_configuration:
                counter_configuration = json.loads(counter_configuration)
            else:
                counter_configuration = {}

            column_name = column_mapping.get(setting)
            if not column_name:
                raise commands.BadArgument("Invalid setting.")
            
            for key, value in counter_configuration.items():
                if value == channel.id:
                    await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", feature, key, None)

            position = channel.position
            new_channel = await channel.clone()
            await channel.delete()
            await new_channel.edit(position=position)
            channel = new_channel

            if setting == "Member Counter":
                member_counters[ctx.guild.id] = channel.id
                try:
                    await channel.edit(name=f"{text}: {channel.guild.member_count}")
                except:
                    pass                    

            if setting == "Active Ticket Counter":
                ticket_data = await db.get_value_from_table(channel.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

                if ticket_data:
                    ticket_data = json.loads(ticket_data)
                    ticket_data = ticket_data.get("ticket_data")
                
                open_tickets = ticket_data["open_tickets"]
                active_ticket_counters[ctx.guild.id] = channel.id
                try:
                    await channel.edit(name=f"{text}: {len(open_tickets)}")
                except:
                    pass

            if setting == "Resolved Ticket Counter":
                stat = await db.get_guild_leaderboard_data(ctx.guild, "tickets_resolved")
                resolved_ticket_counters[ctx.guild.id] = channel.id
                try:
                    await channel.edit(name=f"{text}: {stat}")
                except:
                    pass

            elif setting == "Role Counter":
                role_counters[ctx.guild.id] = channel.id
                try:
                    await channel.edit(name=f"{text}: {len(channel.guild.roles)}")
                except:
                    pass
                
            elif setting == "Custom Role Counter":
                custom_role_configuration = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "ROLES")
                if custom_role_configuration:
                    custom_role_configuration = json.loads(custom_role_configuration)
                    custom_role = custom_role_configuration.get("custom_role_counter")
                    if custom_role:
                        custom_role_counters[ctx.guild.id] = channel.id
                        custom_role = ctx.guild.get_role(custom_role)
                        try:
                            await channel.edit(name=f"{text}: {len(custom_role.members)}")
                        except:
                            pass
                    
                    else:
                        embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="Please set a custom role first.")
                        await ctx.edit(embed=embed)
                        return

            counter_configuration[column_name] = channel.id if channel else None
            await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", feature, column_name, counter_configuration[column_name])

            embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Counter Setting Updated",
                                          description=f"The **{setting}** setting has been updated to {channel.mention if channel else '**None**'}.")
            await ctx.edit(embed=embed)

        except commands.BadArgument as bad_arg:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=str(bad_arg))
            await ctx.edit(embed=embed)

        except discord.errors.Forbidden:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The bot is missing permissions to edit this channel.")
            await ctx.edit(embed=embed)

        except Exception as e:
            print("[Configure > Counters]: ", e)
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="An error occurred and the developer was informed.")
            await ctx.edit(embed=embed)


    @conSubCommands.command(name="embed", description="Configure embed settings.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def embed(self, ctx: discord.ApplicationContext,
                    setting: Option(str,
                                    "The setting to configure",
                                    choices=["Color", "Thumbnail", "Author", "Author Icon", "Footer", "Footer Icon"],
                                    required=True),
                    value: Option(str, "The value to set the setting to | None = off", required=True)):
        await ctx.defer()

        # Define the database feature and column mapping
        feature = "EMBED"
        column_mapping = {
            "Color": "color",
            "Thumbnail": "thumbnail",
            "Author": "author",
            "Author Icon": "author_icon",
            "Footer": "footer",
            "Footer Icon": "footer_icon"
        }

        try:
            embed_configuration = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", feature)
            if embed_configuration:
                embed_configuration = json.loads(embed_configuration)
                embed_data = embed_configuration.get("embed_data", {})

            # Map the setting to the appropriate column name
            column_name = column_mapping.get(setting)
            if not column_name:
                raise commands.BadArgument("Invalid setting.")

            # Handle "None" value
            if value.lower() == "none":
                value = None
            elif column_name == "color" and not Utils.is_valid_hex_color(value):
                raise commands.BadArgument("Invalid color format. Please use the format `#2acb65`.")

            # Validate URL inputs
            if column_name in ["thumbnail", "author_icon", "footer_icon"] and value is not None and not is_valid_url(value):
                raise commands.BadArgument("Invalid URL format. Please use a valid URL.")

            # Update the setting in the database
            await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", feature, column_name, value)

            # Update the embed_data if needed
            if column_name in embed_data:
                embed_data[column_name] = value

            embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Embed Setting Updated",
                                        description=f"The **{setting}** setting has been set to **{value if value is not None else 'None'}**.")
            await ctx.respond(embed=embed)

        except commands.BadArgument as bad_arg:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=str(bad_arg))
            await ctx.respond(embed=embed)

        except Exception as e:
            print("[Configure > Embed]: ", e)
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="An error occurred and the developer was informed.")
            await ctx.respond(embed=embed)


    @conSubCommands.command(name="stats", description="Configure a members stats.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def stat_c(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to update the stats of.", required=True), 
                    stat: Option(str, "The stat to update.", choices=["Cash", "Messages", "Reputation", "Stars"], required=True),
                    value: Option(int, "The value to update the stat to.", required=True)):
        await ctx.defer()
        
        original_stat = await db.get_leaderboard_data(member, stat.lower())
        new_val = value + original_stat

        if new_val < 0:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You can not set the stat to a negative value.")
            return await ctx.respond(embed=embed, ephemeral=True)

        await db.update_leaderboard_stat(member, stat.lower(), value)

        operation = "increased" if value > 0 else "decreased"

        embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Stat Updated", description=f"{member.mention}'s **{stat.lower()}** stat has been {operation} by **{value}**, bringing the total to **{new_val}**.")     
        await ctx.respond(embed=embed)


def setup(client):
    client.add_cog(Configuration(client))