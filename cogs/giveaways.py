# Discord Imports
from discord.utils import basic_autocomplete
from discord.ext import commands
from discord import Option
import discord

# Standard / Third-Party Library Imports
from datetime import datetime, timedelta
import random
import json
import re

# Local Module Imports
from utils.database import Database
from utils.functions import Utils
from utils.lists import *
from Bot import is_blocked

db = Database()

class GiveawaysCog(commands.Cog):
    def __init__(self, client):
        self.client = client

    giveawaySubCommands = discord.SlashCommandGroup("giveaway", "Start, End, Edit, Reroll, List.", default_member_permissions=discord.Permissions(administrator=True))

    @giveawaySubCommands.command(name="start", description="Start a new giveaway.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def start_giveaway(self, ctx: discord.ApplicationContext,
                            channel: Option(discord.TextChannel, "The channel for the giveaway.", required=True),
                            prize: Option(str, "The prize for the giveaway.", required=True),
                            winners: Option(int, "The number of winners.", min_value=1, required=True),
                            duration: Option(str, "The duration of the giveaway (e.g., 1d, 1w, 1h).", required=True),
                            hosted_by: Option(discord.Member, "The host of the giveaway.", required=False)):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Starting Giveaway", description=f"Starting giveaway in {channel.mention}...")
        await ctx.respond(embed=embed, ephemeral=True)

        try:
            def parse_duration(duration_str):
                # Define a mapping of duration abbreviations to their corresponding timedelta units
                duration_map = {
                    's': 'seconds',
                    'm': 'minutes',
                    'h': 'hours',
                    'd': 'days',
                    'w': 'weeks'
                }

                # Use regular expressions to extract the numerical value and abbreviation
                match = re.match(r'^(\d+)([smhdw]?)$', duration_str)
                if not match:
                    return None  # Invalid format

                # Extract the numerical value and abbreviation
                value, abbreviation = match.groups()

                # Map the abbreviation to a timedelta unit or default to minutes
                unit = duration_map.get(abbreviation, 'minutes')

                # Create a timedelta with the specified duration
                return timedelta(**{unit: int(value)})

            parsed_duration = parse_duration(duration)
            if not parsed_duration:
                embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description=f"Invalid duration format. Use formats like 1d, 1w, 1h, etc.")
                await ctx.edit(embed=embed)
                return

            end_time = datetime.now() + parsed_duration
            formatted_end_time = f"<t:{int(end_time.timestamp())}:R>"

            giveaway_embed = await db.build_embed(ctx.guild, title="🎉 Giveaway Time 🎉", description=f"**Prize** ➭ {prize}\n**Winners** ➭ {winners}\n**Hosted By** ➭ {hosted_by.mention if hosted_by else ctx.author.mention}\n**Ends** ➭ {formatted_end_time}")
            giveaway_message = await channel.send(embed=giveaway_embed)

            await giveaway_message.add_reaction("🎉")

            existing_data = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "GIVEAWAYS")
            if existing_data:
                existing_data = json.loads(existing_data)
            else:
                existing_data = {}

            active_giveaways = existing_data.get("active_giveaways", {})

            # Generate a unique key for the new giveaway using guild ID and a unique identifier (UUID)
            unique_key = f"{channel.id}-{Utils.generate_random_string()}"

            # Create a new entry
            active_giveaways[unique_key] = {
                "message": giveaway_message.id,
                "end_time": end_time.timestamp(),
                "prize": prize,
                "winners": winners,
                "hosted_by": hosted_by.id if hosted_by else ctx.author.id
            }

            existing_data["active_giveaways"] = active_giveaways

            await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "GIVEAWAYS", "active_giveaways", existing_data["active_giveaways"])

            embed = await db.build_embed(ctx.guild, title=f"{success_emoji} Giveaway Started", description=f"Giveaway started in {channel.mention}. Ending {formatted_end_time}. Good luck!")
            await ctx.edit(embed=embed)

        except Exception as e:
            print("[start_giveaway]: ", e)
            embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description=f"An error occurred while starting the giveaway.")
            await ctx.edit(embed=embed)


    @giveawaySubCommands.command(name="end", description="End a giveaway.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def end_giveaway(self, ctx: discord.ApplicationContext, giveaway: Option(str, "The giveaway to end.", autocomplete=basic_autocomplete(Utils.get_prize_names), required=True)):
        try:
            embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Ending Giveaway", description=f"Ending giveaway with prize **{giveaway}**...")
            await ctx.respond(embed=embed)

            existing_data = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "GIVEAWAYS")
            if existing_data:
                existing_data = json.loads(existing_data)
                giveaway_data = existing_data.get("active_giveaways")
                completed_giveaways = existing_data.get("completed_giveaways", {})


                # Iterate through the active giveaways to find matching prize
                for giveaway_id, giveaway_info in giveaway_data.items():
                    if not giveaway:
                        embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description=f"There is no active giveaway with the prize **{giveaway}**.")
                        await ctx.edit(embed=embed)
                        return  
                                      
                    prize = giveaway_info.get("prize")
                    if prize == giveaway:
                        messageID = giveaway_info.get("message")
                        channel_id, _ = giveaway_id.split("-")
                        winners = giveaway_info.get("winners")
                        hosted_by = ctx.guild.get_member(giveaway_info.get("hosted_by"))
                        hosted_by = hosted_by.mention if hosted_by else "Unknown"
                        
                        channel = ctx.guild.get_channel(int(channel_id))
                        try:
                            message = await channel.fetch_message(messageID)
                        except discord.NotFound:
                            del giveaway_data[giveaway_id]
                            await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "GIVEAWAYS", "active_giveaways", giveaway_data)
                            embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="The channel or message for this giveaway no longer exists.")
                            await ctx.edit(embed=embed)
                            return 

                        if message:
                            now_timestamp = datetime.now().timestamp()
                            formatted_end_time = f"<t:{int(now_timestamp)}:R>"
                            reactions = message.reactions

                            if reactions:
                                users = await reactions[0].users().flatten()
                                eligible_users = [user for user in users if not user.bot]

                                if len(eligible_users) >= winners:
                                    selected_winners = random.sample(eligible_users, winners)

                                    if selected_winners:
                                        # Announce the winners
                                        winner_mentions = ", ".join([winner.mention for winner in selected_winners])
                                        await message.reply(f"# 🎉 Giveaway Ended 🎉\nCongratulations to {winner_mentions} for winning **{prize}**!")
                                        embed = await db.build_embed(ctx.guild, title="🎉 Giveaway Ended 🎉", description=f"**Prize** ➭ {prize}\n**Winners** ➭ {winner_mentions}\n**Hosted By** ➭ {hosted_by}\n**Ended** ➭ {formatted_end_time}")
                                        await message.edit(embed=embed)
                                        completed_giveaways[giveaway_id] = {"message": messageID, "prize": prize}
                                        break
                                    else:
                                        completed_giveaways[giveaway_id] = {"message": messageID, "prize": prize}
                                        await message.reply(f"There were not enough participants for the giveaway.")
                                        embed = await db.build_embed(ctx.guild, title="🎉 Giveaway Ended 🎉", description=f"**Prize** ➭ {prize}\n**Winners** ➭ None\n**Hosted By** ➭ {hosted_by}\n**Ended** ➭ {formatted_end_time}")
                                        await message.edit(embed=embed)
                                        break
                                else:
                                    completed_giveaways[giveaway_id] = {"message": messageID, "prize": prize}
                                    embed = await db.build_embed(ctx.guild, title="🎉 Giveaway Ended 🎉", description=f"**Prize** ➭ {prize}\n**Winners** ➭ None\n**Hosted By** ➭ {hosted_by}\n**Ended** ➭ {formatted_end_time}")
                                    await message.edit(embed=embed)
                                    await message.reply(f"There were not enough participants for the giveaway.")
                                    break
                            else:
                                break

                if giveaway_id in completed_giveaways:
                    giveaway_data.pop(giveaway_id, None)

                existing_data["active_giveaways"] = giveaway_data
                existing_data["completed_giveaways"] = completed_giveaways

                await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "GIVEAWAYS", "active_giveaways", giveaway_data)
                await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "GIVEAWAYS", "completed_giveaways", completed_giveaways)

                embed = await db.build_embed(ctx.guild, title=f"{success_emoji} Giveaway Ended", description=f"Giveaway ended with prize **{giveaway}**.")
                await ctx.edit(embed=embed)

        except Exception as e:
            print("[end_giveaway]: ", e)
            embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="An error occurred while ending the giveaway.")
            await ctx.respond(embed=embed)


    @giveawaySubCommands.command(name="edit", description="Edit a giveaway.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def edit_giveaway(self, ctx: discord.ApplicationContext, giveaway: Option(str, "The giveaway to edit.", autocomplete=basic_autocomplete(Utils.get_prize_names), required=True), prize: Option(str, "The giveaway prize.", required=False), winners: Option(int, "The number of winners.", min_value=1, required=False), hosted_by: Option(discord.Member, "The host of the giveaway.", required=False), duration: Option(str, "The duration of the giveaway (e.g., 1d, 1w, 1h).", required=False)):
        
        try:
            if all(var is None for var in [prize, duration, winners, hosted_by]):
                embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="You need to at least select one option to edit.")
                return await ctx.respond(embed=embed)

            existing_data = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "GIVEAWAYS")
            if existing_data:
                existing_data = json.loads(existing_data)
                giveaway_data = existing_data.get("active_giveaways")

                for giveaway_id, giveaway_info in giveaway_data.items():
                    original_prize = giveaway_info.get("prize")
                    oritinal_winners = giveaway_info.get("winners")
                    original_host = giveaway_info.get("hosted_by")
                    original_end_time = giveaway_info.get("end_time")
                    message_id = giveaway_info.get("message")
                    channel_id, _ = giveaway_id.split("-")
                    formatted_end_time = f"<t:{int(original_end_time)}:R>"

                    if original_prize == giveaway:
                        # Update the prize and winners
                        if prize:
                            original_prize = prize
                            giveaway_info["prize"] = original_prize
                        if winners:
                            oritinal_winners = winners
                            giveaway_info["winners"] = oritinal_winners
                        if hosted_by:
                            original_host = hosted_by.id
                            giveaway_info["hosted_by"] = original_host
                        if duration:
                            def parse_duration(duration_str):
                                # Define a mapping of duration abbreviations to their corresponding timedelta units
                                duration_map = {
                                    's': 'seconds',
                                    'm': 'minutes',
                                    'h': 'hours',
                                    'd': 'days',
                                    'w': 'weeks'
                                }

                                # Use regular expressions to extract the numerical value and abbreviation
                                match = re.match(r'^(\d+)([smhdw]?)$', duration_str)
                                if not match:
                                    return None  # Invalid format

                                # Extract the numerical value and abbreviation
                                value, abbreviation = match.groups()

                                # Map the abbreviation to a timedelta unit or default to minutes
                                unit = duration_map.get(abbreviation, 'minutes')

                                # Create a timedelta with the specified duration
                                return timedelta(**{unit: int(value)})

                            parsed_duration = parse_duration(duration)
                            if not parsed_duration:
                                embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description=f"Invalid duration format. Use formats like 1d, 1w, 1h, etc.")
                                await ctx.respond(embed=embed)
                                return

                            original_end_time = datetime.now() + parsed_duration
                            giveaway_info["end_time"] = original_end_time.timestamp()
                            formatted_end_time = f"<t:{int(original_end_time.timestamp())}:R>"

                        try:
                            # Update the giveaway message
                            channel = ctx.guild.get_channel(int(channel_id))
                            message = await channel.fetch_message(message_id)
                            embed = await db.build_embed(ctx.guild, title="🎉 Giveaway Time 🎉", description=f"**Prize** ➭ {original_prize}\n**Winners** ➭ {oritinal_winners}\n**Hosted By** ➭ {ctx.guild.get_member(original_host).mention if original_host else ctx.author.mention}\n**Ends** ➭ {formatted_end_time}")
                            await message.edit(embed=embed)

                            # Update the giveaway data in the database
                            giveaway_data[giveaway_id] = giveaway_info
                            existing_data["active_giveaways"] = giveaway_data
                            await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "GIVEAWAYS", "active_giveaways", giveaway_data)

                            embed = await db.build_embed(ctx.guild, title=f"{success_emoji} Giveaway Edited", description=f"Giveaway with the prize **{giveaway}** has been edited.")
                            await ctx.respond(embed=embed)
                            break

                        except discord.NotFound:
                            del giveaway_data[giveaway_id]
                            await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "GIVEAWAYS", "active_giveaways", giveaway_data)
                            embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Edit Failed", description="The channel or message for this giveaway no longer exists.")
                            return await ctx.respond(embed=embed)
                else:
                    embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Giveaway Not Found", description=f"Giveaway with the prize **{giveaway}** was not found.")
                    await ctx.respond(embed=embed)

        except Exception as e:
            print("[edit_giveaway]: ", e)
            embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="An error occurred while editing the giveaway.")
            await ctx.respond(embed=embed)


    @giveawaySubCommands.command(name="reroll", description="Reroll winner(s) for a giveaway.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def reroll_giveaway(self, ctx: discord.ApplicationContext, giveaway: Option(str, "The giveaway to reroll a winner for.", autocomplete=basic_autocomplete(Utils.get_completed_giveaway_names), required=True), winners: Option(int, "The number of winners to reroll.", min_value=1, required=True)):
        try:
            embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Rerolling Giveaway", description=f"Rerolling winner(s) for giveaway with prize **{giveaway}**...")
            await ctx.respond(embed=embed, ephemeral=True)

            existing_data = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "GIVEAWAYS")
            if existing_data:
                existing_data = json.loads(existing_data)
                completed_giveaways = existing_data.get("completed_giveaways")

                for giveaway_id, giveaway_info in completed_giveaways.items():
                    prize = giveaway_info.get("prize")

                    if prize == giveaway:
                        message_id = giveaway_info.get("message")
                        channel_id, _ = giveaway_id.split("-")

                        try:
                            # Fetch the message and perform the reroll logic
                            channel = ctx.guild.get_channel(int(channel_id))
                            message = await channel.fetch_message(message_id)
                            reactions = message.reactions

                            if reactions:
                                users = await reactions[0].users().flatten()
                                eligible_users = [user for user in users if not user.bot]

                                # Reroll the specified number of winners
                                if len(eligible_users) >= winners:
                                    new_winners = random.sample(eligible_users, winners)
                                    winner_mentions = ", ".join([winner.mention for winner in new_winners])
                                    await message.reply(f"# 🎉 New Winner(s) 🎉\nCongratulations to {winner_mentions} for winning **{prize}** in the reroll!")

                                    embed = await db.build_embed(ctx.guild, title=f"{success_emoji} Reroll Successful", description=f"New winner(s) have been selected for the **{giveaway}** giveaway.")
                                    await ctx.edit(embed=embed)

                                else:
                                    embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Reroll Failed", description="Not enough eligible participants to reroll.")
                                    await ctx.edit(embed=embed)
                            else:
                                embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Reroll Failed", description="No reactions found for the giveaway message.")
                                await ctx.edit(embed=embed)

                        except discord.NotFound:
                            del completed_giveaways[giveaway_id]
                            await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "GIVEAWAYS", "completed_giveaways", completed_giveaways)
                            embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Reroll Failed", description="The channel or message for this giveaway no longer exists.")
                            await ctx.edit(embed=embed)
                        break
                else:
                    embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Giveaway Not Found", description=f"Giveaway with the prize **{giveaway}** was not found.")
                    await ctx.edit(embed=embed)

        except Exception as e:
            print("[reroll_giveaway]: ", e)
            embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="An error occurred while rerolling the giveaway.")
            await ctx.edit(embed=embed)

        
    @giveawaySubCommands.command(name="list", description="List all giveaways.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def list_giveaways(self, ctx: discord.ApplicationContext):
        
        try:
            existing_data = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "GIVEAWAYS")
            if existing_data:
                existing_data = json.loads(existing_data)
                active_giveaways = existing_data.get("active_giveaways")
                completed_giveaways = existing_data.get("completed_giveaways")

                active_giveaway_names = [giveaway_info.get("prize") for giveaway_info in active_giveaways.values()]
                completed_giveaway_names = [giveaway_info.get("prize") for giveaway_info in completed_giveaways.values()]

                embed = await db.build_embed(ctx.guild, title="🎉 Giveaways 🎉")
                embed.add_field(name="Active Giveaways", value="\n".join(active_giveaway_names) if active_giveaway_names else "None")
                embed.add_field(name="Completed Giveaways", value="\n".join(completed_giveaway_names) if completed_giveaway_names else "None")
                await ctx.respond(embed=embed)
            else:
                embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Giveaways Not Found", description="No giveaways were found.")
                await ctx.respond(embed=embed)

        except Exception as e:
            print("[list_giveaways]: ", e)
            embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="An error occurred while listing the giveaways.")
            await ctx.respond(embed=embed)


def setup(client):
    client.add_cog(GiveawaysCog(client))