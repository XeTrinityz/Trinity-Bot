import json
import base64
import aiohttp
import discord
import akinator
import functools
import random
import io
from discord.ext import commands, pages
from datetime import datetime
from typing import List
from cryptography.fernet import Fernet
from discord.ui import View, Button
from utils.lists import *
from captcha.image import ImageCaptcha
from utils.database import Database

db = Database()

class Views:
    def __init__(self, client):
        self.client = client

    class HelpCommand(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=120)

        async def on_timeout(self):
            try:
                self.disable_all_items()
                await self.message.edit(view=self)
            except:
                pass

        @discord.ui.select(
            custom_id="help",
            placeholder="Select a category...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Economy",
                    value="economy",
                    emoji="<:Trinity:1153892344219844639>",
                ),
                discord.SelectOption(
                    label="Fun & Games",
                    value="fun",
                    emoji="<:Trinity:1153892344219844639>",
                ),
                discord.SelectOption(
                    label="Informative",
                    value="info",
                    emoji="<:Trinity:1153892344219844639>",
                ),
                discord.SelectOption(
                    label="Image Tools",
                    value="images",
                    emoji="<:Trinity:1153892344219844639>",
                ),
                discord.SelectOption(
                    label="Moderation",
                    value="moderation",
                    emoji="<:Trinity:1153892344219844639>",
                ),
                discord.SelectOption(
                    label="Tickets",
                    value="tickets",
                    emoji="<:Trinity:1153892344219844639>",
                ),
                discord.SelectOption(
                    label="Utility",
                    value="utility",
                    emoji="<:Trinity:1153892344219844639>",
                ),
                discord.SelectOption(
                    label="Configuration",
                    value="config",
                    emoji="<:Trinity:1153892344219844639>",
                ),
            ],
        )
        async def select_callback(self, select, interaction: discord.Interaction):

            await interaction.response.defer()
            choice = select.values[0]
            embed = None

            if choice == "economy":
                embed = await self.build_economy_embed(interaction.guild)
            elif choice == "fun":
                embed = await self.build_fun_embed(interaction.guild)
            elif choice == "info":
                embed = await self.build_info_embed(interaction.guild)
            elif choice == "images":
                embed = await self.build_images_embed(interaction.guild)
            elif choice == "moderation":
                embed = await self.build_moderation_embed(interaction.guild)
            elif choice == "tickets":
                embed = await self.build_tickets_embed(interaction.guild)
            elif choice == "utility":
                embed = await self.build_utility_embed(interaction.guild)
            elif choice == "woocommerce":
                embed = await self.build_woocommerce_embed(interaction.guild)
            elif choice == "config":
                embed = await self.build_config_embed(interaction.guild)

            if embed:
                await interaction.message.edit(embed=embed)

        async def build_economy_embed(self, guild):
            # Build the economy category embed
            embed = await db.build_embed(
                guild,
                title="<:CMD:1209628815761080391> Economy",
                description=
                            "- </shop purchase:1174737714898272270> ➭ Purchase a role from the shop.\n"
                            + "- </shop role remove:1174737714898272270> ➭ Remove a role from your shop.\n"
                            + "- </shop view:1174737714898272270> ➭ View the shop.\n"
                            + "- </shop role add:1174737714898272270> ➭ Add a role to your shop.\n"
                            + "- </blackjack:1174737715061858439> ➭ Play a game of blackjack.\n"
                            + "- </transfer:1174737715061858437> ➭ Transfer funds to another member.\n"
                            + "- </coinflip:1174737714898272275> ➭ Play a game of coinflip.\n"
                            + "- </balance:1174737714898272271> ➭ Gets the balance from a member.\n"
                            + "- </weekly:1174737714898272274> ➭ Collect your weekly earnings.\n"
                            + "- </slots:1174737715061858435> ➭ Play a game of slots.\n"
                            + "- </daily:1174737714898272273> ➭ Claim your daily reward.\n"
                            + "- </work:1174737714898272272> ➭ Work to earn money.\n"
                            + "- </rob:1174737715061858438> ➭ Rob funds from another member.\n"
            )
            return embed

        async def build_fun_embed(self, guild):
            # Build the fun & games category embed
            embed = await db.build_embed(
                guild,
                title="<:CMD:1209628815761080391> Fun & Games",
                description=
                            "- </games tod dare:1174737712016793644> ➭ Receive a dare to complete.\n"
                            + "- </games tod truth:1174737712016793644> ➭ Receive a truth to answer.\n"
                            + "- </games akinator:1174737712016793644> ➭ Play with Akinator.\n"
                            + "- </games connect4:1174737712016793644> ➭ Play a game of Connect 4.\n"
                            + "- </games tictactoe:1174737712016793644> ➭ Play a game of TicTacToe.\n"
                            + "- </games hangman:1174737712016793644> ➭ Play a game of Hangman.\n"
                            + "- </games wyr:1174737712016793644> ➭ Play a game of would you rather.\n"
                            + "- </games rps:1174737712016793644> ➭ Play a game of RPS.\n"
                            + "- </music play:1174737712473985122> ➭ Play music in a voice channel.\n"
                            + "- </interact slap:1174737712016793647> ➭ Slap a member.\n"
                            + "- </interact kiss:1174737712016793647> ➭ Kiss a member.\n"
                            + "- </interact hug:1174737712016793647> ➭ Hug a member.\n"
                            + "- </interact pet:1174737712016793647> ➭ Pet a member.\n"
                            + "- </text reverse:1174737712016793645> ➭ Reverse text.\n"
                            + "- </text encode:1174737712016793645> ➭ Encode text to binary.\n"
                            + "- </text decode:1174737712016793645> ➭ Decode binary to text.\n"
                            + "- </text lulcat:1174737712016793645> ➭ Converts text to cat lul.\n"
                            + "- </text morse:1174737712016793645> ➭ Convet text to morse code.\n"
                            + "- </text mock:1174737712016793645> ➭ Mock a members message.\n"
                            + "- </text ascii:1174737712016793645> ➭ Converts text to ascii art.\n"
                            + "- </showerthoughts:1174737712473985115> ➭ Generate a random shower thought.\n"
                            + "- </pickupline:1174737712016793649> ➭ Generate a random pickupline.\n"
                            + "- </joke:1174737712473985118> ➭ Generate a random joke."
            )
            return embed

        async def build_info_embed(self, guild):
            # Build the informative category embed
            embed = await db.build_embed(
                guild,
                title="<:CMD:1209628815761080391> Informative",
                description=
                            "- </leaderboard messages:1174737713757442127> ➭ Provides the message leaderboard.\n"
                            + "- </leaderboard balance:1174737713757442127> ➭ Provides the balance leaderboard.\n"
                            + "- </leaderboard invites:1174737713757442127> ➭ Provides the invite leaderboard.\n"
                            + "- </leaderboard level:1174737713757442127> ➭ Provides the level leaderboard.\n"
                            + "- </leaderboard stars:1174737713757442127> ➭ Provides the star leaderboard.\n"
                            + "- </member avatar:1174737712834674722> ➭ Provides the members avatar.\n"
                            + "- </member info:1174737712834674722> ➭ Provides information about a member.\n"
                            + "- </server members:1174737712834674719> ➭ Provides the server member count.\n"
                            + "- </server banner:1174737712834674719> ➭ Provides the server banner.\n"
                            + "- </server emojis:1174737712834674719> ➭ Retreive all the server emojis.\n"
                            + "- </server icon:1174737712834674719> ➭ Provides the server icon.\n"
                            + "- </server info:1174737712834674719> ➭ Provides information about the server.\n"
                            + "- </channelinfo:1181118959727165525> ➭ Provides information about a channel.\n"
                            + "- </inviteinfo:1181118959727165524> ➭ Provides information about an invite.\n"
                            + "- </emojiinfo:1174737712834674726> ➭ Provides information about an emoji.\n"
                            + "- </messages:1174737714185240590> ➭ Provides a members message count.\n"
                            + "- </roleinfo:1174737714462072995> ➭ Provides information about a role.\n"
                            + "- </invites:1174737714185240593> ➭ Provides a members invites.\n"
                            + "- </element:1174737714734714934> ➭ Get information on an element.\n"
                            + "- </bot invite:1174737713283473468> ➭ Generate an invite for the bot.\n"
                            + "- </bot info:1174737713283473468> ➭ Provides information about the bot.\n"
                            + "- </level:1174737714185240592> ➭ Provides a members level.\n"
                            + "- </stars:1174880805579931698> ➭ Provides a members star count.\n"
                            + "- </color:1174737714734714933> ➭ Get information from a HEX color.\n"
                            + "- </fact:1174737712473985116> ➭ Generate a random fact.\n"
                            + "- </help:1174394309244633220> ➭ Provides a list of all commands.\n"
            )
            return embed

        async def build_images_embed(self, guild):
            # Build the image tools category embed
            embed = await db.build_embed(
                guild,
                title="<:CMD:1209628815761080391> Image Tools",
                description=
                            "- </image manipulation whowouldwin:1174737712473985121> ➭ Generate a who would win image.\n"
                            + "- </image manipulation communism:1174737712473985121> ➭ Apply a communism overlay on a member.\n"
                            + "- </image manipulation colorify:1174737712473985121> ➭ Overlay an avatar with colors.\n"
                            + "- </image manipulation colorize:1174737712473985121> ➭ Bring color to a black and white image.\n"
                            + "- </image manipulation pikachu:1174737712473985121> ➭ Generate a surpised Pikachu meme.\n"
                            + "- </image manipulation sharpen:1174737712473985121> ➭ Sharpen an image.\n"
                            + "- </image manipulation sadcat:1174737712473985121> ➭ Generate a sad cat meme.\n"
                            + "- </image manipulation oogway:1174737712473985121> ➭ Generate an Oogway quote.\n"
                            + "- </image manipulation wanted:1174737712473985121> ➭ Generate a wanted poster.\n"
                            + "- </image manipulation drake:1174737712473985121> ➭ Generate a Drake meme.\n"
                            + "- </image manipulation clown:1174737712473985121> ➭ This member is a clown.\n"
                            + "- </image manipulation jail:1174737712473985121> ➭ Put a member in jail.\n"
                            + "- </image manipulation pooh:1174737712473985121> ➭ Generate a pooh meme.\n"
                            + "- </image manipulation drip:1174737712473985121> ➭ Give a member some drip.\n"
                            + "- </image manipulation ship:1174737712473985121> ➭ Ship two members together.\n"
                            + "- </image generate:1174737712473985121> ➭ Generate an image from text.\n"
                            + "- </image qrcode:1174737712473985121> ➭ Generate a QR code.\n"
                            + "- </image meme:1174737712473985121> ➭ Get a random image of a meme.\n"
                            + "- </image car:1174737712473985121> ➭ Get a random image of a car."
            )
            return embed

        async def build_moderation_embed(self, guild):
            # Build the moderation commands category embed
            embed = await db.build_embed(
                guild,
                title="<:CMD:1209628815761080391> Moderation Commands",
                description=
                            "- </automod obfuscated configure:1175203997875978281> ➭ Configure the obfuscated word filter rule.\n"
                            + "- </automod mentions configure:1175203997875978281> ➭ Configure the anti mass mention rule.\n"
                            + "- </automod profanity configure:1175203997875978281> ➭ Configure the bad word filter rule.\n"
                            + "- </automod invites configure:1175203997875978281> ➭ Configure the anti invite rule.\n"
                            + "- </automod custom configure:1175203997875978281> ➭ Configure the custom word filter rule.\n"
                            + "- </automod links configure:1175203997875978281> ➭ Configure the anti link rule.\n"
                            + "- </automod pings configure:1175203997875978281> ➭ Configure the ping filter rule.\n"
                            + "- </automod spam configure:1175203997875978281> ➭ Configure the spam content filter rule.\n"
                            + "- </role remove member:1174737714185240595> ➭ Remove a role from a member.\n"
                            + "- </role add member:1174737714185240595> ➭ Add a role to the member.\n"
                            + "- </role remove all:1174737714185240595> ➭ Remove a role from all members.\n"
                            + "- </role add all:1174737714185240595> ➭ Add a role to all members.\n"
                            + "- </lockdown category:1174737713283473474> ➭ Lock or unlock a category.\n"
                            + "- </lockdown channel:1174737713283473474> ➭ Lock or unlock a channel.\n"
                            + "- </warnings history:1174737713283473472> ➭ List a members warning history.\n"
                            + "- </warnings remove:1174737713283473472> ➭ Remove a warning.\n"
                            + "- </warnings clear:1174737713283473472> ➭ Clear all warnings.\n"
                            + "- </warnings add:1174737713283473472> ➭ Warn a member.\n"
                            + "- </clear messages:1174737713283473470> ➭ Clear a specified amount of messages.\n"
                            + "- </ban remove-all:1174737713283473471> ➭ Remove all bans from the server.\n"
                            + "- </ban member:1174737713283473471> ➭ Ban a member from the server.\n"
                            + "- </ban remove:1174737713283473471> ➭ Remove a ban from a user.\n"
                            + "- </ban list:1174737713283473471> ➭ Provides a list of all banned users.\n"
                            + "- </ban id:1174737713283473471> ➭ Ban a user by their ID.\n"
                            + "- </sanitize:1174737713757442125> ➭ Sanitize a members name.\n"
                            + "- </unmute:1174737713757442119> ➭ Unmute a member in the server.\n"
                            + "- </snipe:1174737713757442122> ➭ Get the last deleted message in the server.\n"
                            + "- </kick:1174737713757442121> ➭ Kick a member from the server.\n"
                            + "- </mute:1174737713283473477> ➭ Mute a member for a specified duration.\n"
                            + "- </nuke:1174737713757442124> ➭ Nukes a channel.\n"
            )
            return embed

        async def build_tickets_embed(self, guild):
            # Build the ticket commands category embed
            embed = await db.build_embed(
                guild,
                title="<:CMD:1209628815761080391> Ticket Commands",
                description=
                            "- </tpanel category remove:1174737712473985119> ➭ Remove a ticket category.\n"
                            + "- </tpanel category edit:1174737712473985119> ➭ Edit a ticket category.\n"
                            + "- </tpanel category add:1174737712473985119> ➭ Add a ticket category.\n"
                            + "- </tpanel setup:1174737712473985119> ➭ Setup the ticket system.\n"
                            + "- </tpanel reset:1174737712473985119> ➭ Reset the ticket system.\n"
                            + "- </tpanel move:1174737712473985119> ➭ Move the ticket panel.\n"
                            + "- </ticket remove member:1174737712473985120> ➭ Remove a member from the ticket.\n"
                            + "- </ticket remove role:1174737712473985120> ➭ Remove a role from the ticket.\n"
                            + "- </ticket add member:1174737712473985120> ➭ Add a member to the ticket.\n"
                            + "- </ticket add role:1174737712473985120> ➭ Add a role to the ticket.\n"
                            + "- </ticket delete:1174737712473985120> ➭ Delete an open ticket.\n"
                            + "- </ticket open:1174737712473985120> ➭ Opens a ticket for a member.\n"
                            + "- </ticket find:1174737712473985120> ➭ Find a members ticket.\n"
                            + "- </ticket move:1174737712473985120> ➭ Move a ticket to another category.\n"
            )
            return embed

        async def build_utility_embed(self, guild):
            # Build the utility commands category embed
            embed = await db.build_embed(
                guild,
                title="<:CMD:1209628815761080391> Utility Commands",
                description=
                            "- </autoresponse remove:1174737714462072997> ➭ Remove a trigger.\n"
                            + "- </autoresponse clear:1174737714462072997> ➭ Clear all triggers.\n"
                            + "- </autoresponse list:1174737714462072997> ➭ List all triggers.\n"
                            + "- </autoresponse edit:1174737714462072997> ➭ Edit a trigger.\n"
                            + "- </autoresponse add:1174737714462072997> ➭ Add a trigger.\n"
                            + "- </say webhook impersonate:1174737714462073001> ➭ Send a message as another member.\n"
                            + "- </say webhook normal:1174737714462073001> ➭ Send a message to a webhook.\n"
                            + "- </say webhook embed:1174737714462073001> ➭ Send a customised embed to a webhook.\n"
                            + "- </say webhook edit:1174737714462073001> ➭ Edit an embed sent from a webhook.\n"
                            + "- </say embedbuilder:1174737714462073001> ➭ Send a customised embed to a channel.\n"
                            + "- </say normal:1174737714462073001> ➭ Send a message to a channel.\n"
                            + "- </say sticky:1174737714462073001> ➭ Send a sticky message to a channel.\n"
                            + "- </say reply:1174737714462073001> ➭ Reply to a message in a channel.\n"
                            + "- </say edit:1174737714462073001> ➭ Edit a message sent by the bot.\n"
                            + "- </webhook create:1174737714462073002> ➭ Create a webhook for a channel.\n"
                            + "- </webhook delete:1174737714462073002> ➭ delete a webhook from a channel.\n"
                            + "- </button add role:1174737714462072996> ➭ Add a role button to a message.\n"
                            + "- </button add link:1174737714462072996> ➭ Add a URL redirect button to a message.\n"
                            + "- </button remove:1174737714462072996> ➭ Remove a button from the bot's message.\n"
                            + "- </giveaway start:1174737713283473469> ➭ Start a giveaway.\n"
                            + "- </giveaway reroll:1174737713283473469> ➭ Reroll a giveaway.\n"
                            + "- </giveaway edit:1174737713283473469> ➭ Edit a giveaway.\n"
                            + "- </giveaway end:1174737713283473469> ➭ End a giveaway.\n"
                            + "- </selfroles setup:1174737714462072994> ➭ Setup your selfrole embed.\n"
                            + "- </selfroles remove:1174737714462072994> ➭ Remove a role from your selfrole menu.\n"
                            + "- </selfroles add:1174737714462072994> ➭ Add a role to your selfrole menu.\n"
                            + "- </reminder create:1174737714462072998> ➭ Create a reminder.\n"
                            + "- </reminder remove:1174737714462072998> ➭ Remove a reminder.\n"
                            + "- </reminder clear:1174737714462072998> ➭ Clear all your reminders.\n"
                            + "- </reminder list:1174737714462072998> ➭ List your reminders.\n"
                            + "- </verify captcha:1174737713757442126> ➭ Send the CAPTCHA based verification system.\n"
                            + "- </verify math:1174737713757442126> ➭ Send the math based verification system.\n"
                            + "- </channel slowmode:1181123164751794267> ➭ Set the slowmode of a channel.\n"
                            + "- </channel rename:1181123164751794267> ➭ Rename a channel.\n"
                            + "- </channel delete:1181123164751794267> ➭ Delete a channel.\n"
                            + "- </channel clone:1181123164751794267> ➭ Clone a channel.\n"
                            + "- </search itunes:1174737714462072999> ➭ Search iTunes for a song.\n"
                            + "- </search google:1174737714462072999> ➭ Search google.\n"
                            + "- </search lyrics:1174737714462072999> ➭ Search for a songs lyrics.\n"
                            + "- </search urban:1174737714462072999> ➭ Search the Urban Dictionary.\n"
                            + "- </search imbd:1174737714462072999> ➭ Search IMBD for a movie.\n"
                            + "- </add sticker:1179094394863894528> ➭ Add a sticker to the server.\n"
                            + "- </add emoji:1179094394863894528> ➭ Add an emoji to the server.\n"
                            + "- </randomcolor:1174737714734714935> ➭ Generate a random HEX color.\n"
                            + "- </translate:1174737714734714938> ➭ Translate text to any language.\n"
                            + "- </ghostping:1174737714734714939> ➭ Ghost ping a role or member.\n"
                            + "- </currency:1174737714898272268> ➭ Convert currency.\n"
                            + "- </upload:1174737714898272269> ➭ Upload an image to imgur.\n"
                            + "- </ipinfo:1174737714898272266> ➭ Retrieve data on an IP address.\n"
                            + "- </poll:1174737714734714937> ➭ Send a poll to a channel.\n"
                            + "- </afk:1174737714898272267> ➭ Mark yourself as AFK.\n"
            )
            return embed

        async def build_woocommerce_embed(self, guild):
            # Build the WooCommerce commands category embed
            embed = await db.build_embed(
                guild,
                title="<:CMD:1209628815761080391> WooCommerce Commands",
                description="- </woocommerce order:1174737722385113189> ➭ Retrieve data on an order.\n"
                            + "- </woocommerce orders:1174737722385113189> ➭ Retrieve a list of your latest orders.\n"
                            + "- </woocommerce stock:1174737722385113189> ➭ Retrieve the current stock from a product.\n"
                            + "- </woocommerce stock-all:1174737722385113189> ➭ Retrieve the stock from all of your products.\n"
                            + "- </woocommerce verification:1174737722385113189> ➭ Configure a panel for customers to verify.\n"
                            + "- </woocommerce coupon:1174737722385113189> ➭ Retrieve data on a coupon.\n"
                            + "- </woocommerce coupons:1174737722385113189> ➭ List all coupons and uses.\n"
                            + "- </woocommerce create_coupon:1174737722385113189> ➭ Create a coupon.\n" 
                            + "- </woocommerce delete_coupon:1174737722385113189> ➭ Delete a coupon.\n"
                            + "- </woocommerce product:1174737722385113189> ➭ Retrieve data on a product.\n"
                            + "- </woocommerce products:1174737722385113189> ➭ List all products.\n"
                            + "- </woocommerce find:1174737722385113189> ➭ Find orders based on email or name.\n"
                            + "- </woocommerce customer:1174737722385113189> ➭ Get data on a customer.\n"
                            + "- </woocommerce analytics:1174737722385113189> ➭ Retrieve analytics data from a time period.\n"
            )
            return embed

        async def build_config_embed(self, guild):
            # Build the configuration commands category embed
            embed = await db.build_embed(
                guild,
                title="<:CMD:1209628815761080391> Configuration Commands",
                description="- </config:1174737712834674718> ➭ Provides the server configuration.\n"
                            + "- </configure toggles:1174737712473985123> ➭ Toggle features on or off.\n"
                            + "- </configure protections:1174737712473985123> ➭ Toggle bot protections on or off.\n"
                            + "- </configure channels:1174737712473985123> ➭ Configure the server channels.\n"
                            + "- </configure embed:1174737712473985123> ➭ Configure the server embed.\n"
                            + "- </configure roles:1174737712473985123> ➭ Configure the server roles.\n"
                            + "- </configure counters:1174737712473985123> ➭ Configure the server counters.\n"
                            + "- </configure stats:1174737712473985123> ➭ Configure the stats of a member.\n"
            )
            return embed
        

    class VerificationModal(discord.ui.Modal):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(
                discord.ui.InputText(
                    label="Order Number",
                    placeholder="Enter your order number",
                ),
                discord.ui.InputText(
                    label="Email",
                    placeholder="Enter your email",
                    style=discord.InputTextStyle.singleline
                ),
                *args,
                **kwargs,
            )

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            order_number = self.children[0].value
            email = self.children[1].value

            woo_data = await db.get_value_from_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "WOOCOMMERCE")
            role = await db.get_value_from_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "ROLES")

            if woo_data:
                woo_data = json.loads(woo_data)
                role = json.loads(role)
                url = woo_data.get("url")
                consumer_key = woo_data.get("consumer_key")
                consumer_secret = woo_data.get("consumer_secret")
                role = role.get("customer_role")

            url = base64.b64decode(url)
            consumer_key = base64.b64decode(consumer_key)
            consumer_secret = base64.b64decode(consumer_secret)

            cipher_suite = Fernet("bxGuWrQ3fia0Ft1YDoVGXOD54y_lnru5LyVHel77W14=")

            params = {
                "url": cipher_suite.decrypt(url).decode(),
                "consumer_key": cipher_suite.decrypt(consumer_key).decode(),
                "consumer_secret": cipher_suite.decrypt(consumer_secret).decode(),
            }

            try:
                async with aiohttp.ClientSession() as cs:
                    async with cs.get(f"{cipher_suite.decrypt(url).decode()}/wp-json/wc/v3/orders/{order_number}", params=params) as r:
                        order = await r.json()

                if order and order["data"]["status"] == 200:
                    order = order.json()

                    if order and order["billing"]["email"] == email and (order["status"] == "completed" or order["status"] == "processing"):
                        role = interaction.guild.get_role(int(role))
                        await interaction.user.add_roles(role)
                        embed = await db.build_embed(interaction.guild, title=f"{success_emoji} Verification Complete", description=f"You have received the {role.mention} role!\nThank you for being a customer.")
                        await interaction.followup.send(embed=embed, ephemeral=True)
                    else:
                        embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Verification Failed", description="No matching order found.")
                        await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Verification Failed", description="No matching order found.")
                    await interaction.followup.send(embed=embed, ephemeral=True)
            except Exception as e:
                embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Verification Failed", description=f"An error occurred while verifying the order: {str(e)}")
                await interaction.followup.send(embed=embed, ephemeral=True)


    class www(View):
        OPT1_CUSTOM_ID = "www_opt1"
        OPT2_CUSTOM_ID = "www_opt2"

        def __init__(self, string1, string2):
            super().__init__(timeout=600)
            self.clicks_option1 = 0
            self.clicks_option2 = 0
            self.voted = {}
            self.string1 = string1
            self.string2 = string2
            self.add_button(self.OPT2_CUSTOM_ID, self.string2)
            self.add_button(self.OPT1_CUSTOM_ID, self.string1)

        async def on_timeout(self):
            try:
                self.disable_all_items()
                await self.message.edit(view=self)
            except:
                pass

        def add_button(self, custom_id, string):
            button = discord.ui.Button(
                label=f"{string} (0%)",
                custom_id=custom_id,
                style=discord.ButtonStyle.grey
            )
            button.callback = functools.partial(self.button_callback, button)
            self.add_item(button)

        async def button_callback(self, button, interaction: discord.Interaction):
            user_id = interaction.user.id
            previous_vote = self.voted.get(user_id)

            # Remove the vote from the previous option
            if previous_vote is not None:
                if previous_vote == self.OPT1_CUSTOM_ID:
                    self.clicks_option1 -= 1
                else:
                    self.clicks_option2 -= 1

            # Record the new vote
            self.voted[user_id] = button.custom_id

            if button.custom_id == self.OPT1_CUSTOM_ID:
                self.clicks_option1 += 1
                other_button_id = self.OPT2_CUSTOM_ID
            else:
                self.clicks_option2 += 1
                other_button_id = self.OPT1_CUSTOM_ID

            total_clicks = self.clicks_option1 + self.clicks_option2

            if total_clicks == 0:
                percentage1 = 0
                percentage2 = 0
            else:
                percentage1 = (self.clicks_option1 / total_clicks) * 100
                percentage2 = (self.clicks_option2 / total_clicks) * 100

            # Update the labels of both buttons
            for buttons in self.children:
                if buttons.custom_id == self.OPT1_CUSTOM_ID:
                    buttons.label = f"{self.string1} ({percentage1:.0f}%)"
                elif buttons.custom_id == self.OPT2_CUSTOM_ID:
                    buttons.label = f"{self.string2} ({percentage2:.0f}%)"

            await interaction.response.edit_message(view=self)


    class Polls(View):
        def __init__(self, option1_label, option2_label):
            super().__init__(timeout=600)
            self.clicks_option1 = 0
            self.clicks_option2 = 0
            self.voted = {}
            self.recent_voters_option1 = []
            self.recent_voters_option2 = []
            self.max_recent_voters = 10
            self.option1_label = option1_label
            self.option2_label = option2_label
            self.add_button(1, self.option1_label)
            self.add_button(2, self.option2_label)

        async def on_timeout(self):
            try:
                self.disable_all_items()
                await self.message.edit(view=self)
            except Exception as e:
                print(e)

        def add_button(self, option_number, label):
            custom_id = f"www_opt{option_number}"
            button = discord.ui.Button(
                label=f"{label} (0%)",
                custom_id=custom_id,
                style=discord.ButtonStyle.grey
            )
            button.callback = functools.partial(self.button_callback, button)
            self.add_item(button)

        async def button_callback(self, button, interaction: discord.Interaction):
            user_id = interaction.user.name
            previous_vote = self.voted.get(user_id)

            # Check if the user is voting for the same option again
            if previous_vote is not None and int(button.custom_id[-1]) == previous_vote:
                # Remove the previous vote
                if previous_vote == 1:
                    self.clicks_option1 -= 1
                    self.recent_voters_option1.remove(user_id)
                else:
                    self.clicks_option2 -= 1
                    self.recent_voters_option2.remove(user_id)

                # Reset the vote in the storage
                self.voted.pop(user_id, None)

            else:
                # Remove the vote from the previous option
                if previous_vote is not None:
                    if previous_vote == 1:
                        self.clicks_option1 -= 1
                        self.recent_voters_option1.remove(user_id)
                    else:
                        self.clicks_option2 -= 1
                        self.recent_voters_option2.remove(user_id)

                # Record the new vote
                option_number = int(button.custom_id[-1])
                self.voted[user_id] = option_number

                if option_number == 1:
                    self.clicks_option1 += 1
                    self.recent_voters_option1.insert(0, user_id)
                else:
                    self.clicks_option2 += 1
                    self.recent_voters_option2.insert(0, user_id)

                # Keep only the most recent voters
                self.recent_voters_option1 = self.recent_voters_option1[:self.max_recent_voters]
                self.recent_voters_option2 = self.recent_voters_option2[:self.max_recent_voters]

            total_clicks = self.clicks_option1 + self.clicks_option2

            # Update the labels of both buttons
            for buttons in self.children:
                option_number = int(buttons.custom_id[-1])
                label = self.option1_label if option_number == 1 else self.option2_label

                # Check if total_clicks is 0 to avoid division by zero
                if total_clicks == 0:
                    percentage = 0
                else:
                    percentage = (self.clicks_option1 / total_clicks) * 100 if option_number == 1 else (self.clicks_option2 / total_clicks) * 100

                buttons.label = f"{label} ({percentage:.0f}%)"

            # Edit the original message to update the field values
            label = self.option1_label if option_number == 1 else self.option2_label

            embed = self.message.embeds[0]
            embed.fields[0].name = f"{self.option1_label} ({len(self.recent_voters_option1)})"
            embed.fields[0].value = '\n'.join(map(str, self.recent_voters_option1))
            
            embed.fields[1].name = f"{self.option2_label} ({len(self.recent_voters_option2)})"
            embed.fields[1].value = '\n'.join(map(str, self.recent_voters_option2))
            await interaction.response.edit_message(content=None, embed=embed, view=self)

        def get_button(self, option_number):
            for buttons in self.children:
                if int(buttons.custom_id[-1]) == option_number:
                    return buttons
            return None


    @staticmethod
    async def add_url_button(message: discord.Message, text: str, url: str, emoji: str, style=discord.ButtonStyle.link):

        existing_view = discord.ui.View.from_message(message) or discord.ui.View()

        if not url.startswith(("http://", "https://")):
            raise ValueError("Invalid URL. It should start with 'http://' or 'https://'.")

        # Add the URL button
        new_button = discord.ui.Button(label=text, emoji=emoji, url=url, style=style)
        existing_view.add_item(new_button)
        await message.edit(view=existing_view)


    @staticmethod
    async def add_role_button(message: discord.Message, role: discord.Role, color: discord.ButtonStyle, emoji: str):
        
        existing_view = discord.ui.View.from_message(message) or discord.ui.View()
        new_button = discord.ui.Button(label=role.name, emoji=emoji, style=color, custom_id=f"role|{role.id}")
        existing_view.add_item(new_button)
        await message.edit(view=existing_view)


class verificationCaptcha(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.image_captcha = ImageCaptcha(width=300, height=100, font_sizes=(50, 50))

    @discord.ui.button(emoji=f"{success_emoji}", label="Verify", style=discord.ButtonStyle.gray, custom_id="verification_captcha")
    async def verify_captcha_button_callback(self, button, interaction: discord.Interaction):
        captcha_text = self.generate_captcha_text()

        # Generate the CAPTCHA image using the captcha module
        captcha_image_data = self.generate_captcha_image(captcha_text)

        # Send the CAPTCHA image in an embed
        embed = await db.build_embed(interaction.guild, title="🔑 CAPTCHA", description="Please enter all the letters below in uppercase without any spaces.")
        embed.set_image(url=f"attachment://captcha.png")
        file = discord.File(captcha_image_data, filename="captcha.png")

        # Using a unique custom_id for each button
        await interaction.response.send_message(embed=embed, file=file, view=VerificationCaptchaComplete(answer=captcha_text), ephemeral=True)

    def generate_captcha_text(self):
        captcha_characters = "ABCDEFGHJKLMNPQRSTUVWXYZ"
        captcha_text = ''.join(random.choice(captcha_characters) for _ in range(6))  # 6 characters
        return captcha_text

    def generate_captcha_image(self, text):
        captcha_image_data = self.image_captcha.generate(text)
        return captcha_image_data


class VerificationCaptchaComplete(discord.ui.View):
    def __init__(self, answer) -> None:
        super().__init__(timeout=60)
        self.answer = answer

    async def on_timeout(self):
        try:
            self.disable_all_items()
            await self.message.edit(view=self)
        except:
            pass

    @discord.ui.button(emoji=f"{success_emoji}", label="Complete", style=discord.ButtonStyle.gray, custom_id="captcha_complete")
    async def complete_captcha_button_callback(self, button, interaction: discord.Interaction):
        await interaction.response.send_modal(VerificationModalCaptcha(answer=self.answer))


class VerificationModalCaptcha(discord.ui.Modal):
    def __init__(self, answer) -> None:
        super().__init__(
            discord.ui.InputText(label="Answer", style=discord.InputTextStyle.singleline, required=True),
            title="Complete CAPTCHA", timeout=None, custom_id="verification_modal_captcha")
        self.answer = answer

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        response = self.children[0].value

        if str(response) == str(self.answer):
            roles_config = await db.get_value_from_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "ROLES")
            roles_config = json.loads(roles_config)

            role = roles_config.get("verified_role", None)

            role = interaction.guild.get_role(role)
            await interaction.user.add_roles(role)

            embed = await db.build_embed(interaction.guild, title=f"{success_emoji} Verification Complete", description=f"You have received the {role.mention} role and now have access to the rest of the server.")
            await interaction.followup.send(embed=embed, ephemeral=True)
            await interaction.delete_original_response()
        else:
            embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Verification Failed", description="You answered incorrectly.")
            await interaction.followup.send(embed=embed, ephemeral=True)
            await interaction.delete_original_response()


class verificationButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(emoji=f"{success_emoji}", label="Verify", style=discord.ButtonStyle.gray, custom_id="verification")
    async def second_button_callback(self, button, interaction):
        self.num1 = random.randint(1, 10)
        self.num2 = random.randint(1, 10)
        self.answer = self.num1 + self.num2
        self.question = f"What is {self.num1} + {self.num2}?"
        await interaction.response.send_modal(verificationModal(num1=self.num1, num2=self.num2, answer=self.answer, question=self.question))


class verificationModal(discord.ui.Modal):
    def __init__(self, num1: int, num2: int, answer: int, question: str) -> None:
        super().__init__(
            discord.ui.InputText(label="Answer", style=discord.InputTextStyle.singleline, required=True), title=question, timeout=None, custom_id="verification")
        self.num1 = num1
        self.num2 = num2
        self.answer = answer
        self.question = question

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        response = self.children[0].value

        if str(response) == str(self.answer):
            roles_config = await db.get_value_from_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "ROLES")
            roles_config = json.loads(roles_config)

            role = roles_config.get("verified_role", None)

            role = interaction.guild.get_role(role)
            await interaction.user.add_roles(role)

            embed = await db.build_embed(interaction.guild, title=f"{success_emoji} Verification Complete", description=f"You have received the {role.mention} role and now have access to the rest of the server.")
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Verification Failed", description="You answered incorrectly.")
            await interaction.followup.send(embed=embed, ephemeral=True)


class Blackjack(discord.ui.View):
    def __init__(self, user_hand, dealer_hand, bet, ctx):
        super().__init__(timeout=120)
        self.user_hand = user_hand
        self.dealer_hand = dealer_hand
        self.bet = bet
        self.ctx = ctx

    async def on_timeout(self):
        if self:
            self.disable_all_items()
            await self.message.edit(view=self)

    @discord.ui.button(label="Hit", custom_id="blackjack_hit", style=discord.ButtonStyle.success)
    async def hit_button_callback(self, button, interaction: discord.Interaction):
        card = random.randint(1, 11)
        self.user_hand.append(card)

        if interaction.user.id == self.ctx.author.id:

            def calculate_hand_value(hand):
                value = sum(hand)
                if value > 21 and 11 in hand:
                    hand.remove(11)
                    hand.append(1)
                    value = sum(hand)
                return value

            dealer_value = calculate_hand_value(self.dealer_hand)
            user_value = calculate_hand_value(self.user_hand)
            second_card_value = self.dealer_hand[1]

            card_emojis = {
                1: "♣ 1",
                2: "♣ 2",
                3: "♣ 3",
                4: "♣ 4",
                5: "♣ 5",
                10: "♣ J",

                6: "♦ 6",
                7: "♦ 7",
                8: "♦ 8",
                9: "♦ 9",
                10: "♦ 10",
                10: "♦ K",

                9: "♥ 9",
                10: "♥ 10",
                10: "♥ Q",
                10: "♥ K",

                11: "♠️ A",
                11: "♥ A",
                11: "♦ A",
            }

            def hand_to_emoji(hand):
                return " ".join([card_emojis[card] for card in hand])

            if user_value > 21:
                embed = await db.build_embed(interaction.guild, title=f"<a:Cards:1153886499486580827> Blackjack", description=f"{interaction.user.mention} lost **${self.bet}**! You got over 21.")
                embed.add_field(name=f"Dealers Hand", value=f"❓ {card_emojis.get(second_card_value)} | {self.dealer_hand[1]}", inline=True)
                embed.add_field(name=f"Your Hand", value=f"{hand_to_emoji(self.user_hand)} | {user_value}", inline=True)
                await db.update_leaderboard_stat(interaction.user, "cash", self.bet)
                return await interaction.response.edit_message(embed=embed, view=None)

            embed = await db.build_embed(interaction.guild, title=f"<a:Cards:1153886499486580827> Blackjack")
            embed.add_field(name=f"Dealers Hand", value=f"❓ {card_emojis.get(second_card_value)} | {self.dealer_hand[1]}", inline=True)
            embed.add_field(name=f"Your Hand", value=f"{hand_to_emoji(self.user_hand)} | {user_value}", inline=True)
            return await interaction.response.edit_message(embed=embed, view=Blackjack(self.user_hand, self.dealer_hand, self.bet, self.ctx))
        
    @discord.ui.button(label="Stand", custom_id="blackjack_stand", style=discord.ButtonStyle.red)
    async def stand_button_callback(self, button, interaction: discord.Interaction):
        try:
            if interaction.user.id == self.ctx.author.id:
                await interaction.response.defer()
                card = random.randint(1, 11)
                self.dealer_hand.append(card)

                def calculate_hand_value(hand):
                    value = sum(hand)
                    if value > 21 and 11 in hand:
                        hand.remove(11)
                        hand.append(1)
                        value = sum(hand)
                    return value

                dealer_value = calculate_hand_value(self.dealer_hand)
                user_value = calculate_hand_value(self.user_hand)

                card_emojis = {
                    1: "♣ 1",
                    2: "♣ 2",
                    3: "♣ 3",
                    4: "♣ 4",
                    5: "♣ 5",
                    10: "♣ J",

                    6: "♦ 6",
                    7: "♦ 7",
                    8: "♦ 8",
                    9: "♦ 9",
                    10: "♦ 10",
                    10: "♦ K",

                    9: "♥ 9",
                    10: "♥ 10",
                    10: "♥ Q",
                    10: "♥ K",

                    11: "♠️ A",
                    11: "♥ A",
                    11: "♦ A",
                }

                def hand_to_emoji(hand):
                    return " ".join([card_emojis[card] for card in hand])

                while dealer_value < 18:
                    card = random.randint(1, 11)
                    self.dealer_hand.append(card)
                    dealer_value = calculate_hand_value(self.dealer_hand)
                    
                if dealer_value > 21:
                    embed = await db.build_embed(interaction.guild, title=f"<a:Cards:1153886499486580827> Blackjack", description=f"{interaction.user.mention} wins **${self.bet}**! The dealer got over 21.")
                    await db.update_leaderboard_stat(interaction.user, "cash", self.bet)

                elif dealer_value == 21 and user_value < 21:
                    embed = await db.build_embed(interaction.guild, title=f"<a:Cards:1153886499486580827> Blackjack", description=f"{interaction.user.mention} lost **${self.bet}**! The dealer got 21.")
                    await db.update_leaderboard_stat(interaction.user, "cash", -self.bet)

                elif dealer_value == 21 and user_value == 21:
                    embed = await db.build_embed(interaction.guild, title=f"<a:Cards:1153886499486580827> Blackjack", description=f"{interaction.user.mention} tied! You and the dealer got 21.")

                else:
                    if dealer_value > user_value:
                        embed = await db.build_embed(interaction.guild, title=f"<a:Cards:1153886499486580827> Blackjack", description=f"{interaction.user.mention} lost **${self.bet}**! The dealer got {dealer_value}.")
                        await db.update_leaderboard_stat(interaction.user, "cash", -self.bet)

                    elif user_value > dealer_value:
                        embed = await db.build_embed(interaction.guild, title=f"<a:Cards:1153886499486580827> Blackjack", description=f"{interaction.user.mention} wins **${self.bet}**! You got {user_value}.")
                        await db.update_leaderboard_stat(interaction.user, "cash", self.bet)

                    else:
                        embed = await db.build_embed(interaction.guild, title=f"<a:Cards:1153886499486580827> Blackjack", description=f"{interaction.user.mention} tied! You and the dealer got {user_value}.")

                embed.add_field(name=f"Dealer's Hand", value=f"{hand_to_emoji(self.dealer_hand)} | {dealer_value}", inline=True)
                embed.add_field(name=f"Your Hand", value=f"{hand_to_emoji(self.user_hand)} | {user_value}", inline=True)

                return await interaction.message.edit(embed=embed, view=None)

        except Exception as e:
            print(f"[stand_button_callback]: ", e)


class TicTacToeButton(Button["TicTacToe"]):
    def __init__(self, x: int, y: int, player1: discord.Member, player2: discord.Member):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y
        self.player2 = player2
        self.player1 = player1

    async def on_timeout(self):
        try:
            self.disable()
            await self.view.message.edit(view=self.view)
        except:
            pass

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: TicTacToe = self.view
        state = view.board[self.y][self.x]
        if state in (view.X, view.O):
            return

        embed = await db.build_embed(interaction.guild, title=f"🎮 TicTacToe", description="The first to match 3 in a row wins!")

        # Check if it's the correct player's turn
        if (view.current_player == view.X and interaction.user.id != self.player1.id) or \
           (view.current_player == view.O and interaction.user.id != self.player2.id):
            return

        content = f"{self.player1.mention} [**X**]"
        if view.current_player == view.X:
            self.style = discord.ButtonStyle.danger
            self.label = "X"
            self.disabled = True
            view.board[self.y][self.x] = view.X
            view.current_player = view.O
            content = f"{self.player2.mention} [**O**]"
        else:
            self.style = discord.ButtonStyle.success
            self.label = "O"
            self.disabled = True
            view.board[self.y][self.x] = view.O
            view.current_player = view.X
            content = f"{self.player1.mention} [**X**]"

        winner = view.check_board_winner()
        if winner is not None:
            content = None
            if winner == view.X:
                embed = await db.build_embed(interaction.guild, title=f"🎮 TicTacToe", description=f"🎉 {self.player1.mention} has won the game!")

            elif winner == view.O:
                embed = await db.build_embed(interaction.guild, title=f"🎮 TicTacToe", description=f"🎉 {self.player2.mention} has won the game!")
            else:
                embed = await db.build_embed(interaction.guild, title=f"🎮 TicTacToe", description="👔 It's a tie!")

            for child in view.children:
                child.disabled = True
            
            view.stop()
        else:
            embed = await db.build_embed(interaction.guild, title=f"🎮 TicTacToe", description="The first to match 3 in a row wins!")
            embed.add_field(name="Turn", value=content, inline=True)


        await interaction.response.edit_message(content=None, embed=embed, view=view)


class TicTacToe(View):
    children: List[TicTacToeButton]
    X = -1
    O = 1
    Tie = 2

    def __init__(self, player1, player2):
        super().__init__()
        self.current_player = self.X
        self.player2 = player2
        self.player1 = player1
        self.board = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]

        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y, self.player1, self.player2))

    def check_board_winner(self):
        for across in self.board:
            value = sum(across)
            if value == 3:
                return self.O
            elif value == -3:
                return self.X

        for line in range(3):
            value = self.board[0][line] + self.board[1][line] + self.board[2][line]
            if value == 3:
                return self.O
            elif value == -3:
                return self.X

        diag = self.board[0][2] + self.board[1][1] + self.board[2][0]
        if diag == 3:
            return self.O
        elif diag == -3:
            return self.X

        diag = self.board[0][0] + self.board[1][1] + self.board[2][2]
        if diag == 3:
            return self.O
        elif diag == -3:
            return self.X

        if all(all(cell != 0 for cell in row) for row in self.board):
            return self.Tie

        return None
    

class AkinatorGame(View):
    def __init__(self, ctx, player):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.aki = akinator.Akinator()
        self.game_active = True
        self.player = player

    async def on_timeout(self):
        try:
            self.game_active = False
            self.disable_all_items()
            await self.ctx.edit(content=None, view=self)
            self.stop()
        except:
            self.stop()

    async def process_answer(self, interaction, answer):
        if interaction.user.id == self.player.id:
            await interaction.response.edit_message(view=self)
            if answer.lower() == "probablynot":
                self.aki.answer(akinator.Answer.ProbablyNot)
            else:
                self.aki.answer(getattr(akinator.Answer, answer.title()))
            await self.ctx.edit(content=None, view=self)

    async def back_button_callback(self, interaction):
        if interaction.user.id == self.player.id:
            try:
                self.aki.back()
                await interaction.response.edit_message(view=self)
            except akinator.CantGoBackAnyFurther:
                await interaction.response.send_message("# {error_emoji} Request Failed\nI can not go back any further.", ephemeral=True)

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green, custom_id="yes", row=0)
    async def yes_button(self, button, interaction):
        await self.process_answer(interaction, "yes")

    @discord.ui.button(label="No", style=discord.ButtonStyle.red, custom_id="no", row=0)
    async def no_button(self, button, interaction):
        await self.process_answer(interaction, "no")

    @discord.ui.button(label="Probably", style=discord.ButtonStyle.blurple, custom_id="probably", row=1)
    async def probably_button(self, button, interaction):
        await self.process_answer(interaction, "probably")

    @discord.ui.button(label="Probably Not", style=discord.ButtonStyle.blurple, custom_id="probablynot", row=1)
    async def probablynot_button(self, button, interaction):
        await self.process_answer(interaction, "probablynot")

    @discord.ui.button(label="I Don't Know", style=discord.ButtonStyle.grey, custom_id="idk", row=2)
    async def idk_button(self, button, interaction):
        await self.process_answer(interaction, "idk")

    @discord.ui.button(label="Back", emoji="<a:LeftArrow:1156039371624026112>", style=discord.ButtonStyle.grey, custom_id="back", row=2)
    async def back_button(self, button, interaction):
        await self.back_button_callback(interaction)

    async def akinator_game(self):
        try:
            intro = discord.Embed(
                title="🎮 Akinator", description=f"Hello, {self.ctx.author.mention}! I am Akinator!\n\n<a:Loading:1247220769511964673> Starting Game...", color=discord.Colour.blue())
            intro.set_image(url="https://i.ytimg.com/vi/FG9lyVryNLg/maxresdefault.jpg")
            self.message = await self.ctx.respond(embed=intro)
            self.aki.start_game()

            await self.process_question()

            if self.game_active:
                self.aki.win()
                answer = discord.Embed(
                    title=f"{self.aki.first_guess.name} | {self.aki.first_guess.description}",
                    color=discord.Colour.blue(),
                )
                answer.set_image(url=self.aki.first_guess.absolute_picture_path)
                await self.ctx.edit(embed=answer, view=None)
                self.stop()

        except Exception as e:
            print("[AkinatorGame]: ", e)

    async def process_question(self):
        if not self.game_active:
            return
        question = discord.Embed(title="", description=f"## {self.aki.question}", color=discord.Colour.blue())
        question.set_image(url="https://i.imgur.com/I0rkmFg.png")
        await self.ctx.edit(embed=question, view=self)
        if self.aki.progression <= 80:
            await self.process_question()


class RockPaperScissors(discord.ui.View):
    def __init__(self, user1, user2):
        super().__init__(timeout=120)
        self.user1 = user1
        self.user2 = user2
        self.moves = {user1: None, user2: None}

    async def on_timeout(self):
        try:
            self.disable_all_items()
            await self.ctx.edit(content=None, view=self)
        except:
            pass

    @discord.ui.button(label="Rock", custom_id="rps_rock", emoji="🗿",style=discord.ButtonStyle.gray)
    async def rock_button_callback(self, button, interaction: discord.Interaction):
        user = interaction.user
        if user in [self.user1, self.user2]:
            self.moves[user] = "rock"
            await self.check_moves(interaction)
            await interaction.response.send_message("You have chosen rock.", ephemeral=True)
            await interaction.message.edit(content=f"{user.mention} has chosen.")

    @discord.ui.button(label="Paper", custom_id="rps_paper", emoji="📄",style=discord.ButtonStyle.gray)
    async def paper_button_callback(self, button, interaction: discord.Interaction):
        user = interaction.user
        if user in [self.user1, self.user2]:
            self.moves[user] = "paper"
            await self.check_moves(interaction)
            await interaction.response.send_message("You have chosen paper.", ephemeral=True)
            await interaction.message.edit(content=f"{user.mention} has chosen.")

    @discord.ui.button(label="Scissors", custom_id="rps_scissors", emoji="✂️", style=discord.ButtonStyle.gray)
    async def scissors_button_callback(self, button, interaction: discord.Interaction):
        user = interaction.user
        if user in [self.user1, self.user2]:
            self.moves[user] = "scissors"
            await self.check_moves(interaction)
            await interaction.response.send_message("You have chosen scissors.", ephemeral=True)
            await interaction.message.edit(content=f"{user.mention} has chosen.")

    async def check_moves(self, interaction):
        if all(self.moves.values()):
            winner = self.determine_winner()
            await self.show_result(interaction, winner)

    def determine_winner(self):
        move1, move2 = self.moves[self.user1], self.moves[self.user2]
        if move1 == move2:
            return "It's a tie!"
        elif (move1 == "rock" and move2 == "scissors") or (move1 == "scissors" and move2 == "paper") or (
                move1 == "paper" and move2 == "rock"):
            return f"{self.user1.mention} wins!"
        else:
            return f"{self.user2.mention} wins!"

    async def show_result(self, interaction, result):

        move_emojis = {
            "rock": "🗿",
            "paper": "📄",
            "scissors": "✂️",
        }

        self.disable_all_items()

        embed = await db.build_embed(interaction.guild, title=f"🎮 Rock Paper Scissors", description=result)
        embed.add_field(name=self.user1.display_name, value=f"ﾠﾠ{move_emojis.get(self.moves[self.user1])}ﾠﾠ", inline=True)
        embed.add_field(name="VS", value="⚡", inline=True)
        embed.add_field(name=self.user2.display_name, value=f"ﾠﾠ{move_emojis.get(self.moves[self.user2])}ﾠﾠ", inline=True)
        await interaction.message.edit(content=None, embed=embed, view=self)


class ConnectFourButton(Button["Connect4"]):
    def __init__(self, x: int, y: int, player1: discord.Member, player2: discord.Member):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y
        self.player2 = player2
        self.player1 = player1

    async def on_timeout(self):
        try:
            self.disable()
            await self.view.message.edit(view=self.view)
        except:
            pass

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: Connect4 = self.view
        state = view.board[self.y][self.x]

        if state != 0 or (self.y < 3 and view.board[self.y + 1][self.x] == 0):  # Check if the current button is already selected or if it's not at the bottom row or above an already selected button
            return

        embed = await db.build_embed(interaction.guild, title=f"🎮 Connect 4", description="The first to match 4 in a row wins!")

        # Check if it's the correct player's turn
        if (view.current_player == view.X and interaction.user.id != self.player1.id) or \
           (view.current_player == view.O and interaction.user.id != self.player2.id):#
            embed = await db.build_embed(interaction.guild, title=f"🎮 Connect 4", description="It's not your turn.")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        content = f"{self.player1.mention} [🔴]"
        if view.current_player == view.X:
            self.style = discord.ButtonStyle.grey
            self.label = "🔴"
            self.disabled = True
            view.board[self.y][self.x] = view.X
            view.current_player = view.O
            content = f"{self.player2.mention} [🟡]"
        else:
            self.style = discord.ButtonStyle.grey
            self.label = "🟡"
            self.disabled = True
            view.board[self.y][self.x] = view.O
            view.current_player = view.X
            content = f"{self.player1.mention} [🔴]"

        winner = view.check_board_winner()
        if winner is not None:
            content = None
            if winner == view.X:
                embed = await db.build_embed(interaction.guild, title=f"🎮 Connect 4", description=f"🎉 {self.player1.mention} has won the game!")

            elif winner == view.O:
                embed = await db.build_embed(interaction.guild, title=f"🎮 Connect 4", description=f"🎉 {self.player2.mention} has won the game!")
            else:
                embed = await db.build_embed(interaction.guild, title=f"🎮 Connect 4", description="😐 It's a tie.")

            for child in view.children:
                child.disabled = True

            view.stop()
        else:
            embed = await db.build_embed(interaction.guild, title=f"🎮 Connect 4", description="The first to match 4 in a row wins!")
            embed.add_field(name="Turn", value=content, inline=True)

        await interaction.response.edit_message(content=None, embed=embed, view=view)


class Connect4(View):
    children: List[ConnectFourButton]
    X = -1
    O = 1
    Tie = 2

    def __init__(self, player1, player2):
        super().__init__()
        self.current_player = self.X
        self.player2 = player2
        self.player1 = player1
        self.board = [
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0]
        ]

        for x in range(5):
            for y in range(5):
                self.add_item(ConnectFourButton(x, y, self.player1, self.player2))

    def check_board_winner(self):
        for row in range(5):
            for col in range(5):
                # Check horizontal line
                if col + 3 < 5:
                    if self.board[row][col] == self.board[row][col + 1] == self.board[row][col + 2] == self.board[row][col + 3] == 1:
                        return self.O
                    elif self.board[row][col] == self.board[row][col + 1] == self.board[row][col + 2] == self.board[row][col + 3] == -1:
                        return self.X

        for row in range(5):
            for col in range(5):
                # Check vertical line
                if row + 3 < 5:
                    if self.board[row][col] == self.board[row + 1][col] == self.board[row + 2][col] == self.board[row + 3][col] == 1:
                        return self.O
                    elif self.board[row][col] == self.board[row + 1][col] == self.board[row + 2][col] == self.board[row + 3][col] == -1:
                        return self.X

        for row in range(5):
            for col in range(5):
                # Check diagonal
                if col + 3 < 5 and row + 3 < 5:
                    if self.board[row][col] == self.board[row + 1][col + 1] == self.board[row + 2][col + 2] == self.board[row + 3][col + 3] == 1:
                        return self.O
                    elif self.board[row][col] == self.board[row + 1][col + 1] == self.board[row + 2][col + 2] == self.board[row + 3][col + 3] == -1:
                        return self.X

                if col - 3 >= 0 and row + 3 < 5:
                    if self.board[row][col] == self.board[row + 1][col - 1] == self.board[row + 2][col - 2] == self.board[row + 3][col - 3] == 1:
                        return self.O
                    elif self.board[row][col] == self.board[row + 1][col - 1] == self.board[row + 2][col - 2] == self.board[row + 3][col - 3] == -1:
                        return self.X

        if all(all(cell != 0 for cell in row) for row in self.board):
            return self.Tie

        return None

    
class Hangman(discord.ui.View):
    def __init__(self, ctx, word):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.word = word
        self.guesses = []
        self.guesses_left = 10
        self.word_guessed = False
        self.game_over = False

    async def on_timeout(self):
        try:
            self.disable_all_items()
            await self.message.edit(view=self)
        except:
            pass

    @discord.ui.button(label="A", custom_id="hangman_a", style=discord.ButtonStyle.gray)
    async def a_button_callback(self, button, interaction: discord.Interaction):
        await self.guess("a", interaction)

    @discord.ui.button(label="B", custom_id="hangman_b", style=discord.ButtonStyle.gray)
    async def b_button_callback(self, button, interaction: discord.Interaction):
        await self.guess("b", interaction)

    @discord.ui.button(label="C", custom_id="hangman_c", style=discord.ButtonStyle.gray)
    async def c_button_callback(self, button, interaction: discord.Interaction):
        await self.guess("c", interaction)

    @discord.ui.button(label="D", custom_id="hangman_d", style=discord.ButtonStyle.gray)
    async def d_button_callback(self, button, interaction: discord.Interaction):
        await self.guess("d", interaction)

    @discord.ui.button(label="E", custom_id="hangman_e", style=discord.ButtonStyle.gray)
    async def e_button_callback(self, button, interaction: discord.Interaction):
        await self.guess("e", interaction)

    @discord.ui.button(label="F", custom_id="hangman_f", style=discord.ButtonStyle.gray)
    async def f_button_callback(self, button, interaction: discord.Interaction):
        await self.guess("f", interaction)

    @discord.ui.button(label="G", custom_id="hangman_g", style=discord.ButtonStyle.gray)
    async def g_button_callback(self, button, interaction: discord.Interaction):
        await self.guess("g", interaction)

    @discord.ui.button(label="H", custom_id="hangman_h", style=discord.ButtonStyle.gray)
    async def h_button_callback(self, button, interaction: discord.Interaction):
        await self.guess("h", interaction)

    @discord.ui.button(label="I", custom_id="hangman_i", style=discord.ButtonStyle.gray)
    async def i_button_callback(self, button, interaction: discord.Interaction):
        await self.guess("i", interaction)

    @discord.ui.button(label="J", custom_id="hangman_j", style=discord.ButtonStyle.gray)
    async def j_button_callback(self, button, interaction: discord.Interaction):
        await self.guess("j", interaction)

    @discord.ui.button(label="K", custom_id="hangman_k", style=discord.ButtonStyle.gray)
    async def k_button_callback(self, button, interaction: discord.Interaction):
        await self.guess("k", interaction)

    @discord.ui.button(label="L", custom_id="hangman_l", style=discord.ButtonStyle.gray)
    async def l_button_callback(self, button, interaction: discord.Interaction):
        await self.guess("l", interaction)

    @discord.ui.button(label="M", custom_id="hangman_m", style=discord.ButtonStyle.gray)
    async def m_button_callback(self, button, interaction: discord.Interaction):
        await self.guess("m", interaction)

    @discord.ui.button(label="N", custom_id="hangman_n", style=discord.ButtonStyle.gray)
    async def n_button_callback(self, button, interaction: discord.Interaction):
        await self.guess("n", interaction)

    @discord.ui.button(label="O", custom_id="hangman_o", style=discord.ButtonStyle.gray)
    async def o_button_callback(self, button, interaction: discord.Interaction):
        await self.guess("o", interaction)

    @discord.ui.button(label="P", custom_id="hangman_p", style=discord.ButtonStyle.gray)
    async def p_button_callback(self, button, interaction: discord.Interaction):
        await self.guess("p", interaction)

    @discord.ui.button(label="Q", custom_id="hangman_q", style=discord.ButtonStyle.gray)
    async def q_button_callback(self, button, interaction: discord.Interaction):
        await self.guess("q", interaction)

    @discord.ui.button(label="R", custom_id="hangman_r", style=discord.ButtonStyle.gray)
    async def r_button_callback(self, button, interaction: discord.Interaction):
        await self.guess("r", interaction)

    @discord.ui.button(label="S", custom_id="hangman_s", style=discord.ButtonStyle.gray)
    async def s_button_callback(self, button, interaction: discord.Interaction):
        await self.guess("s", interaction)

    @discord.ui.button(label="T", custom_id="hangman_t", style=discord.ButtonStyle.gray)
    async def t_button_callback(self, button, interaction: discord.Interaction):
        await self.guess("t", interaction)

    @discord.ui.button(label="U", custom_id="hangman_u", style=discord.ButtonStyle.gray)
    async def u_button_callback(self, button, interaction: discord.Interaction):
        await self.guess("u", interaction)

    @discord.ui.button(label="V", custom_id="hangman_v", style=discord.ButtonStyle.gray)
    async def v_button_callback(self, button, interaction: discord.Interaction):
        await self.guess("v", interaction)

    @discord.ui.button(label="W", custom_id="hangman_w", style=discord.ButtonStyle.gray)
    async def w_button_callback(self, button, interaction: discord.Interaction):
        await self.guess("w", interaction)

    @discord.ui.button(label="X", custom_id="hangman_x", style=discord.ButtonStyle.gray)
    async def x_button_callback(self, button, interaction: discord.Interaction):
        await self.guess("x", interaction)

    @discord.ui.button(label="Y", custom_id="hangman_y", style=discord.ButtonStyle.gray)
    async def y_button_callback(self, button, interaction: discord.Interaction):
        await self.guess("y", interaction)

    async def guess(self, letter, interaction):
        if interaction.user.id == self.ctx.author.id:

            clicked_button = interaction.data.get('custom_id')
            for child in self.children:
                if isinstance(child, discord.ui.Button) and child.custom_id == clicked_button:
                    child.disabled = True 
                    break

            self.guesses.append(letter)

            if letter not in self.word:
                self.guesses_left -= 1

            if self.guesses_left == 0:
                self.game_over = True
                embed = await db.build_embed(interaction.guild, title=f"🎮 Hangman", description=f"You lost! The word was **{self.word}**.")
                self.disable_all_items()
                return await interaction.response.edit_message(embed=embed, view=self)

            if all(letter in self.guesses for letter in self.word):
                self.game_over = True
                embed = await db.build_embed(interaction.guild, title=f"🎮 Hangman", description=f"You won! The word was **{self.word}**.")
                self.disable_all_items()
                return await interaction.response.edit_message(embed=embed, view=self)

            embed = await db.build_embed(interaction.guild, title=f"🎮 Hangman", description=f"You have {self.guesses_left} guesses left.")
            embed.add_field(name="Word", value=f"{' '.join(letter if letter in self.guesses else '🟦' for letter in self.word)}", inline=True)
            embed.add_field(name="Guesses", value=f"{' '.join(self.guesses)}", inline=True)
            await interaction.response.edit_message(embed=embed, view=self)


class GuessTheWord(discord.ui.View):
    def __init__(self, ctx, word, has_image):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.word = word
        self.has_image = has_image  # New attribute to track if an image is present
        self.guesses = []
        self.guesses_left = 10
        self.word_guessed = False
        self.game_over = False

    async def on_timeout(self):
        try:
            await self.ctx.edit(view=None)
        except:
            pass

    class GuessTheWordModal(discord.ui.Modal):
        def __init__(self, word: str, view: discord.ui.View, has_image: discord.Attachment, **kwargs):
            self.word = word
            self.view = view
            self.has_image = has_image  # Receive the information about the image

            super().__init__(
                discord.ui.InputText(
                    label="Guess The Word",
                    style=discord.InputTextStyle.singleline,
                    max_length=4000,
                    required=True
                ),
                **kwargs
            )

        async def callback(self, interaction: discord.Interaction) -> None:
            guess = self.children[0].value.lower()  # Convert guess to lowercase for case-insensitive comparison
            gtw_embed = interaction.message.embeds[0]

            if guess != self.word.lower():
                embed = await db.build_embed(interaction.guild, title="🎮 Guess The Word", description=f"Incorrect!")
                return await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)

            embed = await db.build_embed(
                interaction.guild,
                title="🎮 Guess The Word",
                description=f"{interaction.user.mention} won! The word was **{self.word}**.",
            )

            if self.has_image:
                image_data = await self.has_image.read()
                image_bytes = io.BytesIO(image_data)

                file = discord.File(image_bytes, filename="attached_image.png")
                embed.set_image(url=f"attachment://attached_image.png")

                await interaction.response.edit_message(embed=embed, file=file, view=None)
            else:
                await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="Guess", custom_id="gtw_guess", style=discord.ButtonStyle.gray)
    async def gtw_guess_button_callback(self, button, interaction: discord.Interaction):
        await interaction.response.send_modal(self.GuessTheWordModal(title="Guess The Word", word=self.word, view=self, has_image=self.has_image))


class AutoMod(discord.ui.View):
    def __init__(self, client):
        self.client = client
        super().__init__(timeout=None)

    class BanModal(discord.ui.Modal):
        def __init__(self, client, **kwargs):
            self.client = client

            super().__init__(
                discord.ui.InputText(
                    label="Ban Reason",
                    style=discord.InputTextStyle.paragraph,
                    max_length=1000,
                    required=True
                ),
                **kwargs
            )

        async def callback(self, interaction: discord.Interaction) -> None:
            reason = self.children[0].value.lower()
            automod_embed = interaction.message.embeds[0]
            member_id = automod_embed.footer.text.split("➭")[1]

            ban_list = interaction.guild.bans()
            ban_list_data = []

            async for banned in ban_list:
                ban_list_data.append(banned.user.id)
            
            if int(member_id) in ban_list_data:
                embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description="This user is already banned.")
                return await interaction.response.send_message(embed=embed, ephemeral=True)
        
            member = await self.client.get_or_fetch_user(int(member_id))
            embed = await db.build_embed(interaction.guild, title="<a:loading:1247220769511964673> Banning Member", description=f"The bot is currently banning {member.mention}...")
            loading = await interaction.response.send_message(embed=embed, ephemeral=True)

            if member in interaction.guild.members:
                member = interaction.guild.get_member(int(member_id))
                invoker_top_role_position = interaction.user.top_role.position
                user_top_role_position = member.top_role.position
                
                if user_top_role_position >= interaction.guild.me.top_role.position:
                    embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description=f"The bot can not ban members with the {member.top_role.mention} role.")
                    return await loading.edit(embed=embed)

                elif invoker_top_role_position <= user_top_role_position and not interaction.guild.owner:
                    embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description=f"You can not ban members with the {member.top_role.mention} role.")
                    return await loading.edit(embed=embed)

                elif member == interaction.user:
                    embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description="You can not ban yourself.")
                    return await loading.edit(embed=embed)
                
                elif member == interaction.guild.owner:
                    embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description=f"The bot can not ban the server owner.")
                    return await loading.edit(embed=embed)

            try:
                embed = await db.build_embed(interaction.guild, title="<:Warning:1184336931824341062> Server Notice", description=f"You were banned from **{interaction.guild.name}**.")
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.timestamp = datetime.now()
                await member.send(embed=embed)
            except:
                pass

            await interaction.guild.ban(member, delete_message_seconds=604800, reason=reason + f"\n(Banned By {interaction.user.display_name})")

            embed = await db.build_embed(interaction.guild, title="<a:Moderation:1153886511893332018> Member Banned",
                                        description=f"{member.mention} (``{member.id}``) has been banned.")
            embed.add_field(name="Reason", value=reason + f"\n(``Banned By {interaction.user.display_name}``)", inline=False)
            await loading.edit(embed=embed)

            view = discord.ui.View.from_message(interaction.message)
            view.disable_all_items()
            automod_embed.set_thumbnail(url="https://i.imgur.com/HXjGoNB.png")
            await interaction.message.edit(embed=automod_embed, view=view)

            channels = await db.get_value_from_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS")

            if channels:
                channels = json.loads(channels)
                moderation_log_channel = channels.get("moderation_log_channel")

                if moderation_log_channel:
                    channel = discord.utils.get(interaction.guild.channels, id=moderation_log_channel)
                    
                    if channel is None:
                        await db.update_value_in_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "CHANNELS", "moderation_log_channel", None)
                        return
                    
                    embed = await db.build_embed(interaction.guild, title="<a:Moderation:1153886511893332018> Member Banned", description=f"{member.mention} (``{member.id}``) has been banned.")
                    embed.set_thumbnail(url="")
                    embed.add_field(name="Reason", value=reason + f"\n(``Banned By {interaction.user.display_name}``)", inline=False)
                    await channel.send(embed=embed)

    class KickModal(discord.ui.Modal):
        def __init__(self, **kwargs):

            super().__init__(
                discord.ui.InputText(
                    label="Kick Reason",
                    style=discord.InputTextStyle.paragraph,
                    max_length=1000,
                    required=True
                ),
                **kwargs
            )

        async def callback(self, interaction: discord.Interaction) -> None:
            reason = self.children[0].value.lower()
            automod_embed = interaction.message.embeds[0]
            member = automod_embed.footer.text.split("➭")[1]
            member = interaction.guild.get_member(int(member))

            if member is None:
                embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description="This user is no longer in the server.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
            
                view = discord.ui.View.from_message(interaction.message)
                view.disable_all_items()
                return await interaction.message.edit(view=view)
        
            embed = await db.build_embed(interaction.guild, title="<a:loading:1247220769511964673> Kicking Member", description=f"The bot is currently kicking {member.mention}...")
            loading = await interaction.response.send_message(embed=embed, ephemeral=True)

            invoker_top_role_position = interaction.user.top_role.position
            user_top_role_position = member.top_role.position
            
            if user_top_role_position >= interaction.guild.me.top_role.position:
                embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description=f"The bot can not kick members with the {member.top_role.mention} role.")
                return await loading.edit(embed=embed)

            elif invoker_top_role_position <= user_top_role_position and not interaction.guild.owner:
                embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description=f"You can not kick members with the {member.top_role.mention} role.")
                return await loading.edit(embed=embed)

            elif member == interaction.user:
                embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description="You can not kick yourself.")
                return await loading.edit(embed=embed)
            
            elif member == interaction.guild.owner:
                embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description=f"The bot can not kick the server owner.")
                return await loading.edit(embed=embed)

            try:
                embed = await db.build_embed(interaction.guild, title="<:Warning:1184336931824341062> Server Notice", description=f"You were kicked from **{interaction.guild.name}**.")
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.timestamp = datetime.now()
                await member.send(embed=embed)
            except discord.Forbidden:
                pass

            await interaction.guild.kick(member, reason=reason + f"\n(``Kicked By {interaction.user.display_name}``)")

            embed = await db.build_embed(interaction.guild, title="<a:Moderation:1153886511893332018> Member Kicked",
                                        description=f"{member.mention} (``{member.id}``) has been kicked!")
            embed.add_field(name="Reason", value=reason + f"\n(``Kicked By {interaction.user.display_name}``)", inline=False)
            await loading.edit(embed=embed)

            view = discord.ui.View.from_message(interaction.message)
            view.disable_all_items()
            automod_embed.set_thumbnail(url="https://i.imgur.com/HXjGoNB.png")
            await interaction.message.edit(embed=automod_embed, view=view)

    @discord.ui.button(label="Ban Member", emoji="🚫", custom_id="automod_ban", style=discord.ButtonStyle.grey)
    async def automod_ban_button_callback(self, button, interaction: discord.Interaction):
        if interaction.user.guild_permissions.ban_members:
            await interaction.response.send_modal(self.BanModal(title="Ban Member", client=self.client))

    @discord.ui.button(label="Kick Member", emoji="<:Kicked:1176683231823806624>", custom_id="automod_kick", style=discord.ButtonStyle.grey)
    async def automod_kick_button_callback(self, button, interaction: discord.Interaction):
        if interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_modal(self.KickModal(title="Kick Member"))

    @discord.ui.button(label="Mark Resolved", emoji=f"{success_emoji}", custom_id="automod_resolved", style=discord.ButtonStyle.grey)
    async def automod_mark_button_callback(self, button, interaction: discord.Interaction):
        if interaction.user.guild_permissions.moderate_members or interaction.user.guild_permissions.ban_members:
            automod_embed = interaction.message.embeds[0]
            automod_embed.set_thumbnail(url="https://i.imgur.com/HXjGoNB.png")
            self.disable_all_items()
            await interaction.response.edit_message(embed=automod_embed, view=self)

        
class TOD(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.cooldown = commands.CooldownMapping.from_cooldown(1, 30, commands.BucketType.member)

    @discord.ui.button(label="Truth", custom_id="tod_truth", style=discord.ButtonStyle.success)
    async def truth_button_callback(self, button, interaction: discord.Interaction):

        bucket = self.cooldown.get_bucket(interaction.message)
        retry_after = bucket.update_rate_limit()

        if retry_after:
            embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description=f"You are on cooldown. Try again in {round(retry_after)} seconds.")
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        await interaction.message.edit(view=None)

        truth = random.choice(truths)
        embed = await db.build_embed(interaction.guild, title="", description=f"### {truth}")
        embed.set_author(name=f"Requested By {interaction.user.display_name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
        await interaction.response.send_message(embed=embed, view=self)
        interaction_cooldowns[interaction.user.id] = datetime.utcnow()

    @discord.ui.button(label="Dare", custom_id="tod_dare", style=discord.ButtonStyle.red)
    async def dare_button_callback(self, button, interaction: discord.Interaction):
        
        bucket = self.cooldown.get_bucket(interaction.message)
        retry_after = bucket.update_rate_limit()

        if retry_after:
            embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description=f"You are on cooldown. Try again in {round(retry_after)} seconds.")
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        await interaction.message.edit(view=None)
        
        dare = random.choice(dares)
        embed = await db.build_embed(interaction.guild, title="", description=f"### {dare}")
        embed.set_author(name=f"Requested By {interaction.user.display_name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
        await interaction.response.send_message(embed=embed, view=self)

    @discord.ui.button(label="Random", custom_id="tod_random", style=discord.ButtonStyle.blurple)
    async def random_button_callback(self, button, interaction: discord.Interaction):
        
        bucket = self.cooldown.get_bucket(interaction.message)
        retry_after = bucket.update_rate_limit()

        if retry_after:
            embed = await db.build_embed(interaction.guild, title=f"{error_emoji} Request Failed", description=f"You are on cooldown. Try again in {round(retry_after)} seconds.")
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        await interaction.message.edit(view=None)
        
        randoms = truths + dares
        result = random.choice(randoms)
        embed = await db.build_embed(interaction.guild, title="", description=f"### {result}")
        embed.set_author(name=f"Requested By {interaction.user.display_name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
        await interaction.response.send_message(embed=embed, view=self)


class cancel_ticket_timer(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Cancel", emoji=f"{error_emoji}", custom_id="cancel_ticket_timer", style=discord.ButtonStyle.grey)
    async def cancel_button_callback(self, button, interaction: discord.Interaction):

        existing_data = await db.get_value_from_table(interaction.guild.id, "ServerConfigurations", "Setting", "Feature", "TICKETS")

        if existing_data:
            existing_data = json.loads(existing_data)
            ticket_data = existing_data.get("ticket_data")

        role_id = ticket_data["category_roles"][str(interaction.channel.category.id)]
        role = interaction.guild.get_role(role_id)

        if (role in interaction.user.roles or interaction.user.guild_permissions.manage_channels):
            embed = await db.build_embed(interaction.guild, title="🕒 Ticket Closure Cancelled", description=f"The scheduled closure of this ticket has been **cancelled** by {interaction.user.mention}.")
            self.disable_all_items()
            await interaction.response.edit_message(embed=embed, view=self)
            if interaction.channel.id in timed_close_tickets:
                del timed_close_tickets[interaction.channel.id]


class RoleMembers(discord.ui.View):
    def __init__(self, role):
        super().__init__(timeout=60, disable_on_timeout=True)
        self.role = role
        self.max_users_per_page = 10

    async def on_timeout(self):
        try:
            self.disable_all_items()
            await self.message.edit(view=self)
        except:
            pass

    @discord.ui.button(label="View Members", emoji="📋", style=discord.ButtonStyle.grey)
    async def role_members_callback(self, button, interaction: discord.Interaction):
        role_members = self.role.members

        if len(role_members) == 0:
            embed = discord.Embed(title=f"{error_emoji} {self.role.name}'s Member List", description="There are no members with this role.", color=self.role.color)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        member_pages = [role_members[i : i + self.max_users_per_page] for i in range(0, len(role_members), self.max_users_per_page)]

        if len(self.role.members) <= 10:
            description = ""
            for member in self.role.members:
                description += f"{member.mention}\n"
            embed = discord.Embed(title=f"📋 {self.role.name}'s Member List", description=description, color=self.role.color)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        role_members_embeds = []
        for page_index, page_data in enumerate(member_pages, start=1):
            role_members_embed = discord.Embed(title=f"📋 {self.role.name}'s Member List", color=self.role.color)

            description = ""
            for position, member in enumerate(page_data, start=(page_index - 1) * self.max_users_per_page + 1):
                description += f"{member.mention}\n"

            role_members_embed.description = description
            role_members_embeds.append(role_members_embed)

        paginator = pages.Paginator(pages=role_members_embeds, disable_on_timeout=True, use_default_buttons=False, show_indicator=True, loop_pages=True, timeout=60)
        paginator.add_button(pages.PaginatorButton("prev", label="", emoji="<a:LeftArrow:1156039371624026112>", style=discord.ButtonStyle.grey))
        paginator.add_button(pages.PaginatorButton("page_indicator", style=discord.ButtonStyle.gray, disabled=True))
        paginator.add_button(pages.PaginatorButton("next", label="", emoji="<a:RightArrow:1156039369875001385>", style=discord.ButtonStyle.grey))
        await paginator.respond(interaction, ephemeral=True)


class CancelRaid(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=3600)

    async def on_timeout(self):
        try:
            self.disable_all_items()
            await self.message.edit(view=self)
        except:
            pass

    @discord.ui.button(label="Mark Resolved", emoji="✅", style=discord.ButtonStyle.grey)
    async def raid_resolved_callback(self, button, interaction: discord.Interaction):
        if interaction.guild.id in raided:
            del raided[interaction.guild.id]
        embed = await db.build_embed(interaction.guild, title=f"{success_emoji} Raid Protections Halted", description="Members can now join and create invites.")
        await interaction.response.send_message(embed=embed, ephemeral=True)