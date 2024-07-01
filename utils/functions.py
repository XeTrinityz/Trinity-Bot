import discord
import random
import string
import json
import asyncio
import aiohttp
import time
from datetime import datetime, timedelta
from utils.lists import *
from utils.views import CancelRaid
from utils.database import Database
from googlesearch import search
from bs4 import BeautifulSoup

db = Database()

class Utils:

    @staticmethod
    def is_valid_hex_color(code):
        if not code.startswith("#") or len(code) not in (4, 7):
            return False
        return all(char in string.hexdigits for char in code[1:])

    
    @staticmethod
    def generate_loading_bar(progress):
        total_slots = 6  # Total number of slots in the loading bar
        filled_slots = round(total_slots * progress)
        empty_slots = total_slots - filled_slots

        empty_segment = f"<:LG1:1162579205943472229><:MG2:1162579206878806107><:RG3:1162579208841723924>"
        filled_segment = f"<:LA1:1162579204584513537><:MA2:1162579202869047417><:RA3:1162579201719812147>"

        loading_bar = filled_segment * filled_slots + empty_segment * empty_slots

        return loading_bar


    @staticmethod
    async def get_channel_mention(guild, channel_id):
        channel = guild.get_channel(channel_id)
        return channel.mention if channel else f"Channel Not Found ({channel_id})"


    @staticmethod
    async def get_role_mention(guild, role_id):
        role = guild.get_role(role_id)
        return role.mention if role else f"Role Not Found ({role_id})"


    @staticmethod
    async def get_banned_users(ctx):
        ban_list = await ctx.interaction.guild.bans()
        return [f"{banned.user.name} ({banned.user.id})" for banned in ban_list]


    @staticmethod
    def generate_random_string():
        return ''.join(random.choice(string.ascii_letters) for i in range(5))
    

    @staticmethod
    async def get_prize_names(ctx: discord.AutocompleteContext):
        try:
            existing_data = await db.get_value_from_table(ctx.interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "GIVEAWAYS")
            if existing_data:
                existing_data_json = json.loads(existing_data)
                return [giveaway["prize"] for giveaway in existing_data_json.get("active_giveaways", {}).values() if "prize" in giveaway]
        except Exception as e:
            print(f"[get_prize_names]: {e}")
        return []


    @staticmethod
    async def get_shop_items(ctx: discord.AutocompleteContext):
        try:
            existing_data = await db.get_value_from_table(ctx.interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "SHOP")

            if existing_data:
                existing_data = json.loads(existing_data)
                items = []
                for item_name, item_details in existing_data.items():
                    items.append(item_name)
                return items

        except Exception as e:
            print("[get_prize_names]: ", e)

        return []


    @staticmethod
    async def get_completed_giveaway_names(ctx: discord.AutocompleteContext):
        try:
            existing_data = await db.get_value_from_table(ctx.interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "GIVEAWAYS")

            if existing_data:
                existing_data = json.loads(existing_data)

            completed_giveaways = existing_data.get("completed_giveaways")
            if completed_giveaways:
                if len(completed_giveaways) > 10:
                    first_key = next(iter(completed_giveaways))  # Get the first key
                    completed_giveaways.pop(first_key)  # Remove the first item
                    await db.update_value_in_table(ctx.interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "GIVEAWAYS", "completed_giveaways", completed_giveaways)

                prize_names = [giveaway["prize"] for giveaway in completed_giveaways.values() if "prize" in giveaway]
                return prize_names

        except Exception as e:
            print("[get_completed_giveaway_names]: ", e)

        return []


    @staticmethod
    async def get_invite_codes(ctx: discord.AutocompleteContext):
        try:
            invites = await ctx.interaction.guild.invites()
            return [f"{invite.inviter.display_name} | {invite.code}" for invite in invites]
        except Exception as e:
            print("[get_invite_codes]: ", e)
        return []
    

    @staticmethod
    async def get_webhooks(ctx: discord.AutocompleteContext):
        try:
            webhooks = ctx.interaction.guild.webhooks()
            return [f"{webhooks.channel.name} | {webhooks.name}" for webhooks in await webhooks]
        except Exception as e:
            print("[get_webhooks]: ", e)

        return []


    @staticmethod
    async def get_rules(ctx: discord.AutocompleteContext):
        try:
            if ctx.interaction.guild:
                rules = await ctx.interaction.guild.fetch_auto_moderation_rules()
                return [rule.name for rule in rules]
            else:
                return []
        except Exception as e:
            print("[get_rules]: ", e)
        return []


    @staticmethod
    async def get_reminder_names(ctx: discord.AutocompleteContext):
        try:
            if ctx.interaction.user.id in reminders:
                user_reminders = reminders[ctx.interaction.user.id]
                return [reminder[0] for reminder in user_reminders]
            else:
                return []

        except Exception as e:
            print("[get_reminder_names]: ", e)
            return []


    @staticmethod
    async def get_member_warnings(ctx: discord.AutocompleteContext):
        try:
            member = ctx.interaction.data
            warnings = await db.get_warnings_for_user(ctx.interaction.guild.id, str(member['options'][0]['value']))

            if warnings:
                warnings = [f"#{warning['id']} | {warning['reason']}" for warning in warnings]

            if warnings != 0:
                return warnings
            else:
                return []

        except Exception as e:
            print("[get_member_warnings]: ", e)
            return []


    @staticmethod
    async def get_trigger_names(ctx: discord.AutocompleteContext):
        triggers = []
        try:
            existing_data = await db.get_value_from_table(ctx.interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "TRIGGERS")

            if existing_data:
                existing_data = json.loads(existing_data)
                for trigger in existing_data:
                    triggers.append(trigger)

        except Exception as e:
            print("[get_trigger_names]: ", e)

        return triggers
    

    @staticmethod
    def format_duration(duration):
        days = duration.days
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        time_units = [
            ("day", days),
            ("hour", hours),
            ("minute", minutes),
            ("second", seconds),
        ]

        formatted_units = [f"{value} {unit}{'s' if value != 1 else ''}" for unit, value in time_units if value > 0]
        formatted_duration = ", ".join(formatted_units)

        return formatted_duration
    

    @staticmethod
    async def check_anti_raid(self, member, inviter_obj, invite_code):
        channels = await db.get_value_from_table(member.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")
        if channels:
            mod_channels = json.loads(channels)
            moderation_log_channel = mod_channels.get("moderation_log_channel")

            now = datetime.now()
            join_times = self.join_times.setdefault(member.guild.id, [])
            join_times.append(now)

            max_joins = 10
            join_times = [time for time in join_times if now - time < timedelta(seconds=5)]

            if len(join_times) > max_joins:
                current_time = time.time()
                last_execution = self.join_time.get(member.guild.id, 0)

                if current_time - last_execution >= max_joins:
                    end_time = (datetime.now() + timedelta(seconds=3600)).timestamp()
                    raided[member.guild.id] = [[end_time]]

                    log_channel = discord.utils.get(member.guild.channels, id=moderation_log_channel)
                    embed = await db.build_embed(member.guild, title="<a:Moderation:1153886511893332018> Possible Raid Detected", description="The bot has identified a substantial influx of new members within a brief timeframe. Consequently, the generation of invites has been temporarily halted.")
                    await log_channel.send(embed=embed)

                    if inviter_obj:
                        try:
                            await member.guild.ban(inviter_obj, delete_message_seconds=604800, reason="Server Raid Invite Creator.")
                        except discord.Forbidden:
                            embed = await db.build_embed(member.guild, title="<a:Moderation:1153886511893332018> Possible Raid Detected", description=f"Failed to ban the invite creator {inviter_obj.mention}.")
                            await log_channel.send(embed=embed, view=CancelRaid())
                        for invite in await member.guild.invites():
                            if invite.code == invite_code:
                                await invite.delete()
                                break

                    await member.send(content="The server is currently being raided, please try rejoining later.")
                    await member.kick(reason="Anti-Raid Triggered")

                    self.join_time[member.guild.id] = current_time
                    self.join_times[member.guild.id] = []
                

    @staticmethod
    async def get_top_10_results(query):
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, lambda: list(search(query, sleep_interval=2, num_results=10, advanced=True)))
        return results


    @staticmethod
    def random_chark(char_num):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(char_num))