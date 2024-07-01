import aiomysql
import json
import discord
from datetime import datetime
from utils.lists import *

import aiomysql
import json

class Database:
    def __init__(self):
        self.pool = None

    async def create_db_pool(self):
        return await aiomysql.create_pool(
            host="",
            user="",
            password="",
            db="",
            autocommit=True,
            minsize=1,
            maxsize=10,
            pool_recycle=60,
        )

    async def initialize_db_pool(self):
        if self.pool is None:
            self.pool = await self.create_db_pool()

    async def initialize_tables_and_settings(self, guild_id):
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Consolidate table existence checks into a single query
                    table_exists_query = """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 's134412_trinity' 
                    AND table_name IN ('ServerConfigurations', 'LeaderboardStats', 'global_settings')
                    """
                    await cursor.execute(table_exists_query)
                    existing_tables = {result[0] for result in await cursor.fetchall()}

                    # Create tables if they don't exist
                    if 'ServerConfigurations' not in existing_tables:
                        await cursor.execute("""
                        CREATE TABLE ServerConfigurations (
                            ID INT AUTO_INCREMENT PRIMARY KEY,
                            ServerID VARCHAR(255),
                            Feature VARCHAR(255),
                            Setting TEXT,
                            UNIQUE (ServerID, Feature)
                        )
                        """)

                    if 'LeaderboardStats' not in existing_tables:
                        await cursor.execute("""
                        CREATE TABLE LeaderboardStats (
                            ID INT AUTO_INCREMENT PRIMARY KEY,
                            ServerID VARCHAR(255),
                            Value longtext,
                            UNIQUE (ServerID, Value)
                        )
                        """)

                    if 'global_settings' not in existing_tables:
                        await cursor.execute("""
                        CREATE TABLE `global_settings` (
                            `FEATURE` varchar(255) NOT NULL,
                            `ARG1` text DEFAULT NULL,
                            `ARG2` varchar(255) DEFAULT NULL,
                            `ARG3` varchar(255) DEFAULT NULL,
                            PRIMARY KEY (`FEATURE`)
                        );
                        """)
                        # Insert default values into 'global_settings'
                        await cursor.execute("""
                        INSERT INTO `global_settings` (`FEATURE`, `ARG1`, `ARG2`, `ARG3`) 
                        VALUES 
                        ('BLOCKED', '{"users": [1136023740388474880, 570753792895746048, 1167440084258271233, 1131323126932844724, 1169375272332701747, 561655770706477059, 728080688032776212, 1099359826699620453], "guilds": [1169375473688662068, 1085763511923265546]}', NULL, NULL),
                        ('STATUS', 'Online', 'None', '/help | 🔗 xetrinityz.com');
                        """)

                    # Initialize default settings for new guilds in a single transaction
                    default_settings = json.dumps({
                        "EMBED": {
                            "color": "#FFFFFF",
                            "thumbnail": None,
                            "author": None,
                            "author_icon": None,
                            "footer": None,
                            "footer_icon": None,
                        },
                        "PROTECTIONS": {
                            "anti_spam": False,
                            "anti_ghost_ping": False,
                            "anti_selfbot": False,
                            "anti_raid": False,
                        },
                        "CHANNELS": {
                            "welcome_channel": None,
                            "audit_log_channel": None,
                            "moderation_log_channel": None,
                            "suggestion_channel": None,
                            "starboard_channel": None,
                            "chatbot_channel": None,
                        },
                        "COUNTERS": {
                            "member_counter": None,
                            "custom_role_counter": None,
                            "role_counter": None,
                            "active_ticket_counter": None,
                            "resolved_ticket_counter": None,
                        },
                        "TOGGLES": {
                            "welcome_messages": False,
                            "audit_logs": False,
                            "auto_roles": False,
                            "xp_system": False,
                            "chatbot": False,
                            "suggestions": False,
                        },
                        "ROLES": {
                            "auto_role": None, 
                            "verified_role": None,
                            "customer_role": None,
                            "custom_role_counter": None,
                        },
                        "TICKETS": {
                            "ticket_data": {
                                "category_roles": {},
                                "open_tickets": {},
                                "ticket_panel": {"Channel ID": None, "Message ID": None},
                                "ticket_counter": 0,
                            }
                        },
                    })

                    # Check and insert default settings for LeaderboardStats and ServerConfigurations
                    await cursor.execute("SELECT ServerID FROM LeaderboardStats WHERE ServerID = %s LIMIT 1", (str(guild_id),))
                    if not await cursor.fetchone():
                        await cursor.execute("INSERT INTO LeaderboardStats (ServerID, Value) VALUES (%s, %s)", (str(guild_id), '{}'))

                    await cursor.execute("SELECT ServerID FROM ServerConfigurations WHERE ServerID = %s LIMIT 1", (str(guild_id),))
                    if not await cursor.fetchone():
                        await cursor.execute("INSERT INTO ServerConfigurations (ServerID, Feature, Setting) VALUES (%s, 'default', %s)", (str(guild_id), default_settings))

        except Exception as e:
            print("[initialize_tables_and_settings]: ", e)


    async def get_value_from_table(self, ServerID: str, table_name: str, column_name: str, condition_column: str, condition_value):
        if self.pool is None:
            self.pool = await self.create_db_pool()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                query = f"SELECT {column_name} FROM {table_name} WHERE {condition_column} = %s and ServerID = %s"
                await cursor.execute(query, (condition_value, ServerID))
                result = await cursor.fetchone()

                return result[0] if result else None


    async def get_single_value_from_table(self, table_name: str, column_name: str, condition_column: str, condition_value):
        if self.pool is None:
            await self.initialize_db_pool()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                query = f"SELECT {column_name} FROM {table_name} WHERE {condition_column} = %s"
                await cursor.execute(query, (condition_value,))
                result = await cursor.fetchone()

                return result[0] if result else None


    async def update_value_in_table(self, ServerID: str, table_name: str, column_name: str, condition_column: str, condition_value, key_to_update, new_value):
        await self.initialize_db_pool()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Check if the row exists
                select_query = f"SELECT {column_name} FROM {table_name} WHERE {condition_column} = %s and ServerID = %s"
                await cursor.execute(select_query, (condition_value, ServerID))
                existing_data = await cursor.fetchone()

                if existing_data:
                    existing_json = json.loads(existing_data[0])
                else:
                    # Initialize with empty JSON if not exists
                    existing_json = {}

                # Update the value
                existing_json[key_to_update] = new_value
                updated_json_str = json.dumps(existing_json)

                # Upsert query to handle both insert and update in one query
                upsert_query = f"""
                INSERT INTO {table_name} (ServerID, {condition_column}, {column_name}) 
                VALUES (%s, %s, %s) 
                ON DUPLICATE KEY UPDATE {column_name} = VALUES({column_name})
                """
                await cursor.execute(upsert_query, (ServerID, condition_value, updated_json_str))


    async def custom_query(self, query: str):
        await self.initialize_db_pool()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query)

    
    async def clean_unused_servers(self, guilds):
        try:
            await self.initialize_db_pool()

            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Combine deletion queries into a single operation for efficiency
                    delete_configurations_query = """
                    DELETE FROM ServerConfigurations 
                    WHERE ServerID NOT IN %s
                    """
                    await cursor.execute(delete_configurations_query, (guilds,))

                    delete_leaderboard_query = """
                    DELETE FROM LeaderboardStats 
                    WHERE ServerID NOT IN %s
                    """
                    await cursor.execute(delete_leaderboard_query, (guilds,))

            return True

        except Exception as e:
            print("[clean_unused_servers]: ", e)
            return False


    async def set_default_values(self, feature):
        await self.initialize_db_pool()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Use placeholders in the query to prevent SQL injection
                update_query = "UPDATE ServerConfigurations SET Setting = %s WHERE Feature = %s"
                
                # Define default values based on the feature
                default_values = {}
                if feature == "protections":
                    default_values = {
                        "anti_spam": False,
                        "anti_ghost_ping": False,
                        "anti_selfbot": False
                    }

                # Convert default values to JSON string once before the query
                default_values_json = json.dumps(default_values)

                # Update all rows with default values
                await cursor.execute(update_query, (default_values_json, feature))

        return True


    async def remove_value_from_table(self, ServerID: str, table_name: str, column_name: str, condition_column: str, condition_value, key_to_remove):
        await self.initialize_db_pool()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                select_query = f"SELECT {column_name} FROM {table_name} WHERE {condition_column} = %s and ServerID = %s"
                await cursor.execute(select_query, (condition_value, ServerID))
                existing_data = await cursor.fetchone()

                if existing_data:
                    existing_json = json.loads(existing_data[0])
                    if key_to_remove in existing_json:
                        del existing_json[key_to_remove]
                        updated_json_str = json.dumps(existing_json)

                        update_query = f"UPDATE {table_name} SET {column_name} = %s WHERE {condition_column} = %s and ServerID = %s"
                        await cursor.execute(update_query, (updated_json_str, condition_value, ServerID))
                    else:
                        print(f"Key {key_to_remove} does not exist in the database.")


    async def update_sticky_data(self, server_id, channel_id, message_id, new_sticky_data):
        await self.initialize_db_pool()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                select_query = "SELECT Setting FROM ServerConfigurations WHERE ServerID = %s and Feature = 'STICKY'"
                await cursor.execute(select_query, (server_id,))
                existing_data = await cursor.fetchone()

                if existing_data:
                    existing_json = json.loads(existing_data[0])
                else:
                    existing_json = {}

                channel_key = str(channel_id)
                # Simplify the logic for updating the sticky data
                if new_sticky_data:
                    if channel_key not in existing_json:
                        existing_json[channel_key] = {}
                    existing_json[channel_key][message_id] = new_sticky_data
                else:
                    if channel_key in existing_json and message_id in existing_json[channel_key]:
                        del existing_json[channel_key][message_id]
                        if not existing_json[channel_key]:
                            del existing_json[channel_key]

                if existing_json:
                    updated_json_str = json.dumps(existing_json)
                    update_query = "UPDATE ServerConfigurations SET Setting = %s WHERE ServerID = %s and Feature = 'STICKY'"
                    await cursor.execute(update_query, (updated_json_str, server_id))
                else:
                    delete_query = "DELETE FROM ServerConfigurations WHERE ServerID = %s and Feature = 'STICKY'"
                    await cursor.execute(delete_query, (server_id,))


    async def delete_sticky_entry(self, server_id, channel_id, message_id):
        await self.initialize_db_pool()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                select_query = "SELECT Setting FROM ServerConfigurations WHERE ServerID = %s and Feature = 'STICKY'"
                await cursor.execute(select_query, (server_id,))
                existing_data = await cursor.fetchone()

                if existing_data:
                    existing_json = json.loads(existing_data[0])

                    channel_key = str(channel_id)
                    # Check if the channel and message ID exist in the JSON
                    if channel_key in existing_json and message_id in existing_json[channel_key]:
                        # Delete the message ID entry
                        del existing_json[channel_key][message_id]
                        # If no more entries for the channel, delete the channel key
                        if not existing_json[channel_key]:
                            del existing_json[channel_key]
                        updated_json_str = json.dumps(existing_json)

                        update_query = "UPDATE ServerConfigurations SET Setting = %s WHERE ServerID = %s and Feature = 'STICKY'"
                        await cursor.execute(update_query, (updated_json_str, server_id))


    async def update_single_value_in_table(self, table_name: str, column_name: str, condition_column: str, condition_value, new_value):
        await self.initialize_db_pool()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                update_query = f"UPDATE {table_name} SET {column_name} = %s WHERE {condition_column} = %s"
                await cursor.execute(update_query, (new_value, condition_value,))


    async def append_ids_to_lists(self, table_name: str, list_name: str, condition_column: str, condition_value):
        await self.initialize_db_pool()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                select_query = f"SELECT ARG1 FROM {table_name} WHERE {condition_column} = %s and FEATURE = 'BLOCKED'"
                await cursor.execute(select_query, (condition_value,))
                current_data_str = await cursor.fetchone()

                if current_data_str is not None:
                    current_data = json.loads(current_data_str[0])
                    if not isinstance(current_data, dict):
                        current_data = {"users": [], "guilds": []}
                else:
                    current_data = {"users": [], "guilds": []}

                # Assuming 'blacklist' and 'blacklist_guilds' are defined elsewhere and should be appended
                if list_name in current_data:
                    # Append new IDs to the list instead of overwriting
                    if list_name == "users":
                        current_data[list_name].extend(blacklist)
                    elif list_name == "guilds":
                        current_data[list_name].extend(blacklist_guilds)

                    # Remove duplicates by converting to set and back to list
                    current_data[list_name] = list(set(current_data[list_name]))

                updated_data_str = json.dumps(current_data)
                update_query = f"UPDATE {table_name} SET ARG1 = %s WHERE {condition_column} = %s and FEATURE = 'BLOCKED'"
                await cursor.execute(update_query, (updated_data_str, condition_value,))


    async def update_list_value_in_table(self, ServerID: str, table_name: str, column_name: str, condition_column: str, condition_value, key_to_update, new_value):
        await self.initialize_db_pool()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                select_query = f"SELECT {column_name} FROM {table_name} WHERE {condition_column} = %s and ServerID = %s"
                await cursor.execute(select_query, (condition_value, ServerID))
                existing_data = await cursor.fetchone()

                if existing_data:
                    existing_json = json.loads(existing_data[0])
                else:
                    existing_json = {}

                # Directly update the value without checking if it exists, as it will be created or overwritten
                existing_json[key_to_update] = new_value

                updated_json_str = json.dumps(existing_json)

                update_query = f"UPDATE {table_name} SET {column_name} = %s WHERE {condition_column} = %s and ServerID = %s"
                await cursor.execute(update_query, (updated_json_str, condition_value, ServerID))


    async def get_leaderboard_data(self, user, stat):
        await self.initialize_db_pool()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                check_query = "SELECT Value FROM LeaderboardStats WHERE ServerID = %s"
                await cursor.execute(check_query, (str(user.guild.id),))
                existing_data = await cursor.fetchone()

                if existing_data:
                    current_values = json.loads(existing_data[0])
                else:
                    current_values = {}

                return current_values.get(str(user.id), {}).get(stat, 0)


    async def get_guild_leaderboard_data(self, guild, stat):
        await self.initialize_db_pool()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                check_query = "SELECT Value FROM LeaderboardStats WHERE ServerID = %s"
                await cursor.execute(check_query, (str(guild.id),))
                existing_data = await cursor.fetchone()

                if existing_data:
                    current_values = json.loads(existing_data[0])
                else:
                    current_values = {}

                # Corrected the key used to access user_data from current_values
                user_data = current_values.get(stat, {})
                return user_data.get("value", 0)  # Assuming each stat is stored with a "value" key
    

    async def get_all_leaderboard_data(self, server_id, stat):
        await self.initialize_db_pool()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                query = "SELECT Value FROM LeaderboardStats WHERE ServerID = %s"
                await cursor.execute(query, (str(server_id),))
                result = await cursor.fetchone()

                if result:
                    value_json = result[0]
                    value_dict = json.loads(value_json)

                    if isinstance(value_dict, dict):
                        leaderboard_data = [(int(user_id), stats.get(stat, 0)) for user_id, stats in value_dict.items() if stat in stats]

                        leaderboard_data.sort(key=lambda x: x[1], reverse=True)

                        return leaderboard_data

        return []


    async def update_leaderboard_stat(self, user, stat: str, value: int):
        await self.initialize_db_pool()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                check_query = "SELECT Value FROM LeaderboardStats WHERE ServerID = %s"
                await cursor.execute(check_query, (str(user.guild.id),))
                existing_data = await cursor.fetchone()

                if existing_data:
                    current_values = json.loads(existing_data[0])
                else:
                    current_values = {}

                user_data = current_values.get(str(user.id), {})
                user_data[stat] = user_data.get(stat, 0) + value
                current_values[str(user.id)] = user_data

                update_query = "UPDATE LeaderboardStats SET Value = %s WHERE ServerID = %s"
                await cursor.execute(update_query, (json.dumps(current_values), str(user.guild.id)))


    async def update_guild_leaderboard_stat(self, guild, stat: str, value: int):
        await self.initialize_db_pool()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                check_query = "SELECT Value FROM LeaderboardStats WHERE ServerID = %s"
                await cursor.execute(check_query, (str(guild.id),))
                existing_data = await cursor.fetchone()

                if existing_data:
                    current_values = json.loads(existing_data[0])
                else:
                    current_values = {}

                # Simplify the update process by directly adding the value
                current_values.setdefault(str(guild.id), {}).setdefault(stat, 0)
                current_values[str(guild.id)][stat] += value

                update_query = "UPDATE LeaderboardStats SET Value = %s WHERE ServerID = %s"
                await cursor.execute(update_query, (json.dumps(current_values), str(guild.id)))


    async def update_invite_data(self, guild, user, member):
        await self.initialize_db_pool()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                check_query = "SELECT Value FROM LeaderboardStats WHERE ServerID = %s"
                await cursor.execute(check_query, (str(guild.id),))
                existing_data = await cursor.fetchone()

                if existing_data:
                    current_values = json.loads(existing_data[0])
                else:
                    current_values = {}

                # Efficiently update the invited_users list
                user_data = current_values.setdefault(str(user.id), {})
                invited_users = user_data.setdefault("invited_users", [])
                if member.id not in invited_users:
                    invited_users.append(member.id)

                update_query = "UPDATE LeaderboardStats SET Value = %s WHERE ServerID = %s"
                await cursor.execute(update_query, (json.dumps(current_values), str(guild.id)))
            

    async def remove_user_from_invite_list(self, guild, user, member):
        await self.initialize_db_pool()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                check_query = "SELECT Value FROM LeaderboardStats WHERE ServerID = %s"
                await cursor.execute(check_query, (str(guild.id),))
                existing_data = await cursor.fetchone()

                if existing_data:
                    current_values = json.loads(existing_data[0])
                else:
                    current_values = {}

                user_data = current_values.get(str(user.id), {})
                invited_users = user_data.get("invited_users", [])
                if member.id in invited_users:
                    invited_users.remove(member.id)  # Remove the member from the list
                    user_data["invited_users"] = invited_users  # Ensure the updated list is set back
                    current_values[str(user.id)] = user_data

                    update_query = "UPDATE LeaderboardStats SET Value = %s WHERE ServerID = %s"
                    await cursor.execute(update_query, (json.dumps(current_values), str(guild.id)))


    async def get_all_leaderboard_data_1(self, guild_id):
        await self.initialize_db_pool()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Retrieve data for the specified guild
                select_query = "SELECT Value FROM LeaderboardStats WHERE ServerID = %s"
                await cursor.execute(select_query, (str(guild_id),))
                data = await cursor.fetchone()

                return json.loads(data[0]) if data else {}


    async def check_level_up(self, ctx, user):
        try:
            level, xp, next_level = await asyncio.gather(
                self.get_leaderboard_data(user, "level"),
                self.get_leaderboard_data(user, "xp"),
                self.get_leaderboard_data(user, "next_level")
            )

            if level == 0:
                await self.update_leaderboard_stat(user, "level", 1)
                await self.update_leaderboard_stat(user, "next_level", 500)  # Set initial next_level
                next_level = 500  # Update next_level locally to avoid re-fetching

            if xp >= next_level:
                new_next_level = next_level * 2  # Assuming the intention is to double the next level requirement
                await asyncio.gather(
                    self.update_leaderboard_stat(user, "next_level", new_next_level),
                    self.update_leaderboard_stat(user, "level", level + 1)  # Directly increment level
                )

                embed = await self.build_embed(ctx.author.guild, title=f"<a:Level:1153886483183304768> Levelled Up", description=f"Congratulations, {ctx.author.mention}! You've reached Level {level + 1}!")
                return await ctx.reply(embed=embed, delete_after=10)

        except Exception as e:
            print("[check_level_up]: ", e)


    async def get_warnings_for_user(self, ServerID: str, user_id: str):
        await self.initialize_db_pool()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                select_query = "SELECT Value FROM LeaderboardStats WHERE ServerID = %s"
                await cursor.execute(select_query, (ServerID,))
                server_data = await cursor.fetchone()

                if server_data:
                    server_data_json = json.loads(server_data[0])
                    return server_data_json.get(user_id, {}).get("warnings", [])

        return []
        

    async def remove_all_warnings_in_table(self, ServerID: str, user_id: str):
        await self.initialize_db_pool()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                select_query = "SELECT Value FROM LeaderboardStats WHERE ServerID = %s"
                await cursor.execute(select_query, (ServerID,))
                existing_data = await cursor.fetchone()

                if existing_data:
                    existing_data_json = json.loads(existing_data[0])
                    if user_id in existing_data_json and "warnings" in existing_data_json[user_id]:
                        del existing_data_json[user_id]["warnings"]
                        new_data_json = json.dumps(existing_data_json)

                        update_query = "UPDATE LeaderboardStats SET Value = %s WHERE ServerID = %s"
                        await cursor.execute(update_query, (new_data_json, ServerID))


    async def remove_warning_in_table(self, ServerID: str, user_id: str, warning_id: int):
        await self.initialize_db_pool()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                select_query = "SELECT Value FROM LeaderboardStats WHERE ServerID = %s"
                await cursor.execute(select_query, (ServerID,))
                existing_data = await cursor.fetchone()

                if existing_data:
                    existing_data_json = json.loads(existing_data[0])
                    user_data = existing_data_json.get(user_id, {})
                    warnings = user_data.get("warnings", [])

                    if 1 <= warning_id <= len(warnings):
                        warnings.pop(warning_id - 1)
                        user_data["warnings"] = warnings
                        existing_data_json[user_id] = user_data
                        new_data_json = json.dumps(existing_data_json)

                        update_query = "UPDATE LeaderboardStats SET Value = %s WHERE ServerID = %s"
                        await cursor.execute(update_query, (new_data_json, ServerID))
                    else:
                        print("Warning ID not found.")
                else:
                    print("Server data not found.")


    async def update_warnings_in_table(self, ServerID: str, user_id: str, warned_by: str, reason: str):
        await self.initialize_db_pool()

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                select_query = "SELECT Value FROM LeaderboardStats WHERE ServerID = %s"
                await cursor.execute(select_query, (ServerID,))
                existing_data = await cursor.fetchone()

                timestamp = datetime.now().timestamp()
                if existing_data:
                    existing_data_json = json.loads(existing_data[0])
                    user_data = existing_data_json.get(user_id, {})

                    new_warning = {
                        "id": len(user_data.get("warnings", [])) + 1,
                        "timestamp": timestamp,
                        "reason": reason,
                        "warned_by": warned_by
                    }
                    
                    user_data.setdefault("warnings", []).append(new_warning)
                    
                    existing_data_json[user_id] = user_data
                    new_data_json = json.dumps(existing_data_json)

                    update_query = "UPDATE LeaderboardStats SET Value = %s WHERE ServerID = %s"
                    await cursor.execute(update_query, (new_data_json, ServerID))
                else:
                    new_data_json = json.dumps({
                        user_id: {
                            "warnings": [{
                                "id": 1,
                                "timestamp": timestamp,
                                "reason": reason,
                                "warned_by": warned_by
                            }]}
                    })
                    
                    insert_query = "INSERT INTO LeaderboardStats (ServerID, Value) VALUES (%s, %s)"
                    await cursor.execute(insert_query, (ServerID, new_data_json))


    async def build_embed(self, guild, title=None, description=None):
        server_id = guild.id
        feature = "EMBED"

        embed_configuration = await self.get_value_from_table(server_id, "ServerConfigurations", "Setting", "Feature", feature)
        if embed_configuration:
            embed_settings = json.loads(embed_configuration)  # Deserialize the JSON
            color = embed_settings.get("color", "#FFFFFF")
            title = f"**{title}**" if title else ""

            embed = discord.Embed(title=title, description=description, color=int(color.strip("#"), 16))

            thumbnail = embed_settings.get("thumbnail")
            if thumbnail and thumbnail.startswith(("http://", "https://")):
                embed.set_thumbnail(url=thumbnail)

            author = embed_settings.get("author")
            author_icon = embed_settings.get("author_icon")
            if author_icon and author_icon.startswith(("http://", "https://")):
                embed.set_author(name=author, icon_url=author_icon)
            elif author:
                embed.set_author(name=author)

            footer = embed_settings.get("footer")
            footer_icon = embed_settings.get("footer_icon")
            if footer_icon and footer_icon.startswith(("http://", "https://")):
                embed.set_footer(text=footer, icon_url=footer_icon)
            elif footer:
                embed.set_footer(text=footer)

            return embed