import json
import discord
from discord.ext import pages
from discord.ui import View
from utils.lists import *
from utils.database import Database

db = Database()

class EditFieldModal(discord.ui.Modal):

    def __init__(self, *args, ctx: discord.ApplicationContext, user_embed: discord.Embed, **kwargs):

        self.ctx: discord.ApplicationContext = ctx
        self.user_embed: discord.Embed = user_embed
        super().__init__(*args, **kwargs)
        
        super().__init__(
            discord.ui.InputText(
                label="New Suggestion",
                style=discord.InputTextStyle.long,
                max_length=500,
                required=True), *args, **kwargs)

    async def callback(self, interaction: discord.Interaction) -> None:

        await interaction.response.defer()
        value = self.children[0].value
        original_string = self.user_embed.fields[0].value

        for lines in original_string.split("\n"):
            if lines.startswith("~~"):
                original_string = lines[2:-2]
                break
        
        self.user_embed.set_field_at(index=0, name=self.user_embed.fields[0].name, value=f"~~{original_string}~~\n{value}", inline=False)
        
        await self.ctx.edit(embed=self.user_embed)


async def get_suggestion_data(guild_id, message_id):
    try:
        suggestions = await db.get_value_from_table(guild_id, "ServerConfigurations", "Setting", "Feature", "SUGGESTIONS")
        suggestions = json.loads(suggestions) if suggestions else {}
        data = suggestions.get(str(message_id), {"upvotes": 0, "downvotes": 0, "upvoted_users": [], "downvoted_users": []})
        return data
    except Exception as e:
        print("[get_suggestion_data]:", e)
        return {"upvotes": 0, "downvotes": 0, "upvoted_users": [], "downvoted_users": []}

async def update_suggestion_data(guild_id, message_id, data):
    try:
        suggestions = await db.get_value_from_table(guild_id, "ServerConfigurations", "Setting", "Feature", "SUGGESTIONS")
        suggestions = json.loads(suggestions) if suggestions else {}
        suggestions[str(message_id)] = data
        await db.update_value_in_table(guild_id, "ServerConfigurations", "Setting", "Feature", "SUGGESTIONS", str(message_id), data)
    except Exception as e:
        print("[update_suggestion_data]:", e)
        

class SuggestionButtons(View):
    def __init__(self):
        super().__init__(timeout=None)

    class SuggestionSettingsAdmin(discord.ui.View):
        def __init__(self, embed):
            super().__init__(timeout=120)
            self.embed = embed

        async def on_timeout(self):
            try:
                self.disable_all_items()
                await self.message.edit(view=self)
            except:
                pass

        @discord.ui.select(
            custom_id="suggestion_settings",
            placeholder="Select a setting...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Approve Suggestion",
                    value="approve_suggestion",
                    emoji=f"{success_emoji}",
                ),
                discord.SelectOption(
                    label="Deny Suggestion",
                    value="deny_suggestion",
                    emoji=f"{error_emoji}",
                ),
                discord.SelectOption(
                    label="Edit Suggestion",
                    value="edit_suggestion",
                    emoji="🛠",
                ),
                discord.SelectOption(
                    label="Delete Suggestion",
                    value="delete_suggestion",
                    emoji="🗑",
                ),
                discord.SelectOption(
                    label="View Votes",
                    value="view_votes_suggestion",
                    emoji="📊",
                ),
            ],
        )
        async def select_callback(self, select, interaction: discord.Interaction):
            choice = select.values[0]
            if choice == "approve_suggestion":
                existing_view = discord.ui.View.from_message(self.embed)
                embed = self.embed.embeds[0]
                
                for child in existing_view.children:
                    if child.label == "Settings":
                        setting_button = child
                    child.disabled = True

                existing_view.remove_item(setting_button)

                embed.set_field_at(index=1, name="Status", value=f"{success_emoji} Suggestion Approved", inline=False)
                embed.colour = discord.Colour.green()
                await self.embed.edit(embed=embed, view=existing_view)
                await self.embed.thread.edit(locked=True)
                await interaction.response.edit_message(view=self)
                await db.remove_value_from_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "SUGGESTIONS", str(self.embed.id))
                await interaction.delete_original_response()

                user_id = int(embed.footer.text)
                user = interaction.guild.get_member(user_id)
                if user:
                    embed = await db.build_embed(interaction.guild, title=f"{success_emoji} Suggestion Approved", description=f"Your suggestion was approved by {interaction.user.mention} in **{interaction.guild.name}**.")
                    view = discord.ui.View()
                    view.add_item(discord.ui.Button(label="View Suggestion", url=self.embed.jump_url, style=discord.ButtonStyle.link))
                    try:
                        await user.send(embed=embed, view=view)
                    except:
                        pass

            elif choice == "deny_suggestion":
                existing_view = discord.ui.View.from_message(self.embed)
                embed = self.embed.embeds[0]
                
                for child in existing_view.children:
                    if child.label == "Settings":
                        setting_button = child
                    child.disabled = True

                existing_view.remove_item(setting_button)

                embed.set_field_at(index=1, name="Status", value=f"{error_emoji} Suggestion Denied", inline=False)
                embed.colour = discord.Colour.red()
                await self.embed.edit(embed=embed, view=existing_view)
                await self.embed.thread.edit(locked=True)
                await interaction.response.edit_message(view=self)
                await interaction.delete_original_response()
                await db.remove_value_from_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "SUGGESTIONS", str(self.embed.id))

                user_id = int(embed.footer.text)
                user = interaction.guild.get_member(user_id)
                if user:
                    embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Suggestion Denied", description=f"Your suggestion was denied by {interaction.user.mention} in **{interaction.guild.name}**.")
                    view = discord.ui.View()
                    view.add_item(discord.ui.Button(label="View Suggestion", url=self.embed.jump_url, style=discord.ButtonStyle.link))
                    try:
                        await user.send(embed=embed, view=view)
                    except:
                        pass
            
            elif choice == "edit_suggestion":
                embed = self.embed.embeds[0]
                suggestion_data = await get_suggestion_data(interaction.guild.id, self.embed.id)
                await interaction.response.send_modal(EditFieldModal(title="Edit Suggestion", ctx=self.embed, user_embed=embed))
                await interaction.delete_original_response()

            elif choice == "delete_suggestion":
                await self.embed.thread.delete()
                await interaction.response.edit_message(view=self)
                await interaction.delete_original_response()
                await db.remove_value_from_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "SUGGESTIONS", str(self.embed.id))
                await self.embed.delete()
                
            elif choice == "view_votes_suggestion":
                msg = interaction.message.id
                suggestion_data = await get_suggestion_data(interaction.guild.id, self.embed.id)
                upvoters = suggestion_data.get("upvoted_users", [])
                downvoters = suggestion_data.get("downvoted_users", [])

                upvoters_mentions = []
                downvoters_mentions = []

                for user_id in upvoters:
                    member = interaction.guild.get_member(user_id)
                    if member:
                        upvoters_mentions.append(member.display_name)

                for user_id in downvoters:
                    member = interaction.guild.get_member(user_id)
                    if member:
                        downvoters_mentions.append(member.display_name)

                upvoters_str = "\n".join(upvoters_mentions) if upvoters_mentions else "None"
                downvoters_str = "\n".join(downvoters_mentions) if downvoters_mentions else "None"

                if len(upvoters_mentions) + len(downvoters_mentions) < 10:
                    embed = await db.build_embed(interaction.guild, title="📊 Suggestion Votes", description=f"{success_emoji} **Upvoted**\n{upvoters_str}\n\n{error_emoji} **Downvoted**\n{downvoters_str}")
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    embed_pages = []
                    for i in range(0, len(upvoters_mentions), 10):
                        upvoters_slice = upvoters_mentions[i:i + 10]
                        downvoters_slice = downvoters_mentions[i:i + 10]

                        upvoters_str = "\n".join(upvoters_slice)
                        downvoters_str = "\n".join(downvoters_slice)

                        embed = await db.build_embed(
                            interaction.guild,
                            title="📊 Suggestion Votes",
                            description=f"{success_emoji} **Upvoted**\n{upvoters_str}\n\n{error_emoji} **Downvoted**\n{downvoters_str}"
                        )
                        embed_pages.append(embed)

                    paginator = pages.Paginator(pages=embed_pages, disable_on_timeout=True, use_default_buttons=False, show_indicator=True, loop_pages=True, timeout=60)
                    paginator.add_button(pages.PaginatorButton("prev", label="", emoji="<a:LeftArrow:1156039371624026112>", style=discord.ButtonStyle.grey))
                    paginator.add_button(pages.PaginatorButton("page_indicator", style=discord.ButtonStyle.gray, disabled=True))
                    paginator.add_button(pages.PaginatorButton("next", label="", emoji="<a:RightArrow:1156039369875001385>", style=discord.ButtonStyle.grey))
                    await paginator.respond(interaction, ephemeral=True)
            
                await interaction.followup.delete_message(message_id=msg)


    class SuggestionSettings(discord.ui.View):
        def __init__(self, embed):
            super().__init__(timeout=120)
            self.embed = embed

        async def on_timeout(self):
            try:
                self.disable_all_items()
                await self.message.edit(view=self)
            except:
                pass

        @discord.ui.select(
            custom_id="suggestion_settings",
            placeholder="Select a setting...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Edit Suggestion",
                    value="edit_suggestion",
                    emoji="🛠",
                ),
                discord.SelectOption(
                    label="View Votes",
                    value="view_votes_suggestion",
                    emoji="📊",
                ),
            ],
        )
        async def select_callback(self, select, interaction: discord.Interaction):
            choice = select.values[0]
            
            if choice == "edit_suggestion":
                embed = self.embed.embeds[0]
                await interaction.response.send_modal(EditFieldModal(title="Edit Suggestion", ctx=self.embed, user_embed=embed))
                await interaction.delete_original_response()
            
            elif choice == "view_votes_suggestion":
                msg = interaction.message.id
                suggestion_data = await get_suggestion_data(interaction.guild.id, self.embed.id)
                upvoters = suggestion_data.get("upvoted_users", [])
                downvoters = suggestion_data.get("downvoted_users", [])

                upvoters_mentions = []
                downvoters_mentions = []

                for user_id in upvoters:
                    member = interaction.guild.get_member(user_id)
                    if member:
                        upvoters_mentions.append(member.display_name)

                for user_id in downvoters:
                    member = interaction.guild.get_member(user_id)
                    if member:
                        downvoters_mentions.append(member.display_name)

                upvoters_str = "\n".join(upvoters_mentions) if upvoters_mentions else "None"
                downvoters_str = "\n".join(downvoters_mentions) if downvoters_mentions else "None"

                if len(upvoters_mentions) + len(downvoters_mentions) < 10:
                    embed = await db.build_embed(interaction.guild, title="📊 Suggestion Votes", description=f"{success_emoji} **Upvoted**\n{upvoters_str}\n\n{error_emoji} **Downvoted**\n{downvoters_str}")
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    embed_pages = []
                    for i in range(0, len(upvoters_mentions), 10):
                        upvoters_slice = upvoters_mentions[i:i + 10]
                        downvoters_slice = downvoters_mentions[i:i + 10]

                        upvoters_str = "\n".join(upvoters_slice)
                        downvoters_str = "\n".join(downvoters_slice)

                        embed = await db.build_embed(
                            interaction.guild,
                            title="📊 Suggestion Votes",
                            description=f"{success_emoji} **Upvoted**\n{upvoters_str}\n\n{error_emoji} **Downvoted**\n{downvoters_str}"
                        )
                        embed_pages.append(embed)

                    paginator = pages.Paginator(pages=embed_pages, disable_on_timeout=True, use_default_buttons=False, show_indicator=True, loop_pages=True, timeout=60)
                    paginator.add_button(pages.PaginatorButton("prev", label="", emoji="<a:LeftArrow:1156039371624026112>", style=discord.ButtonStyle.grey))
                    paginator.add_button(pages.PaginatorButton("page_indicator", style=discord.ButtonStyle.gray, disabled=True))
                    paginator.add_button(pages.PaginatorButton("next", label="", emoji="<a:RightArrow:1156039369875001385>", style=discord.ButtonStyle.grey))
                    await paginator.respond(interaction, ephemeral=True)
            
                await interaction.followup.delete_message(message_id=msg)
                
                    
    async def handle_vote(self, interaction: discord.Interaction, is_upvote):
        try:
            await interaction.response.defer(ephemeral=True)
            suggestion_data = await get_suggestion_data(interaction.guild.id, interaction.message.id)
            upvotes = suggestion_data.get("upvotes", 0)
            downvotes = suggestion_data.get("downvotes", 0)
            upvoters = suggestion_data.get("upvoted_users", [])
            downvoters = suggestion_data.get("downvoted_users", [])
            user_id = interaction.user.id

            embed = interaction.message.embeds[0]
            if interaction.user.id == int(embed.footer.text):
                embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description=f"You can not vote on your own suggestion.")
                return await interaction.followup.send(embed=embed, ephemeral=True)

            if is_upvote:
                if user_id in downvoters:
                    # Toggle the upvote and downvote
                    upvoters.append(user_id)
                    downvoters.remove(user_id)
                    upvotes += 1
                    downvotes -= 1
                elif user_id in upvoters:
                    # Remove the upvote
                    upvoters.remove(user_id)
                    upvotes -= 1
                else:
                    # Cast a new upvote
                    upvoters.append(user_id)
                    upvotes += 1
            else:
                if user_id in upvoters:
                    # Toggle the downvote and upvote
                    downvoters.append(user_id)
                    upvoters.remove(user_id)
                    downvotes += 1
                    upvotes -= 1
                elif user_id in downvoters:
                    # Remove the downvote
                    downvoters.remove(user_id)
                    downvotes -= 1
                else:
                    # Cast a new downvote
                    downvoters.append(user_id)
                    downvotes += 1

            total_votes = upvotes + downvotes
            percentage_up = round((upvotes / total_votes) * 100) if total_votes > 0 else 0
            percentage_down = round((downvotes / total_votes) * 100) if total_votes > 0 else 0

            upvote_button = self.children[0]
            downvote_button = self.children[1]
            upvote_button.label = f"{upvotes} ({percentage_up}%)"
            downvote_button.label = f"{downvotes} ({percentage_down}%)"

            await update_suggestion_data(interaction.guild.id, interaction.message.id, {"upvotes": upvotes, "downvotes": downvotes, "upvoted_users": upvoters, "downvoted_users": downvoters})
            await interaction.message.edit(view=self)

        except Exception as e:
            import traceback
            print("[handle_vote]:", traceback.format_exc())

    @discord.ui.button(label="0 (0%)", style=discord.ButtonStyle.green, emoji="👍", custom_id="suggestions_upvote")
    async def upvote_button_callback(self, button, interaction: discord.Interaction):
        await self.handle_vote(interaction, is_upvote=True)

    @discord.ui.button(label="0 (0%)", style=discord.ButtonStyle.red, emoji="👎", custom_id="suggestions_downvote")
    async def downvote_button_callback(self, button, interaction: discord.Interaction):
        await self.handle_vote(interaction, is_upvote=False)

    @discord.ui.button(label="Settings", style=discord.ButtonStyle.gray, emoji="🔧", custom_id="suggestions_settings")
    async def manage_suggestion(self, button, interaction: discord.Interaction):
        try:
            embed = interaction.message.embeds[0]
            if interaction.user.guild_permissions.manage_messages:
                embed = await db.build_embed(interaction.guild, title=f"📝 Suggestion Settings", description="Use the menu below to edit this suggestion.")
                return await interaction.response.send_message(embed=embed, view=self.SuggestionSettingsAdmin(embed=interaction.message), ephemeral=True)

            elif interaction.user.id == int(embed.footer.text):
                embed = await db.build_embed(interaction.guild, title=f"📝 Suggestion Settings", description="Use the menu below to edit this suggestion.")
                return await interaction.response.send_message(embed=embed, view=self.SuggestionSettings(embed=interaction.message), ephemeral=True)

            else:
                embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description=f"You do not have permission to edit this suggestion.")
                return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            print("[manage_suggestion]: ", e)