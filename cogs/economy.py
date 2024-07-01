# Discord Imports
from discord.utils import basic_autocomplete
from discord.ext import commands
from discord import Option
import discord

# Standard / Third-Party Library Imports
import random
import json

# Local Module Imports
from utils.database import Database
from utils.views import Blackjack
from utils.functions import Utils
from utils.lists import *
from Bot import is_blocked

db = Database()

class economy(commands.Cog):
    def __init__(self, client):
        self.client = client

    shopSubCommands = discord.SlashCommandGroup("shop", "View, Purchase")
    shopadminCommands = shopSubCommands.create_subgroup("role", "Role Add, Role Remove, View, Purchase.", default_member_permissions=discord.Permissions(manage_roles=True))

    @commands.slash_command(name="balance", description="Shows a user's balance.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def e_balance(self, ctx: discord.ApplicationContext, user: Option(discord.Member, "The user to get the balance from.")):
            
        await ctx.defer()
        try:
            if user.bot:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"Bots do not have any money.")
                await ctx.respond(embed=embed, ephemeral=True)
                return 

            cash = await db.get_leaderboard_data(user, "cash")

            if cash is None:
                cash = 0

            embed = await db.build_embed(ctx.author.guild, title=f"<a:Cash:1247220739220701184> Account Balance", description=f"{user.mention} currently has **${cash}**.")
            await ctx.respond(embed=embed)

        except Exception as e:
            print("[e_balance]: ", e)


    @commands.slash_command(name="work", description="Earn money by working.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def e_work(self, ctx: discord.ApplicationContext):
        
        try:
            cash = await db.get_leaderboard_data(ctx.author, "cash")

            if cash is None:
                cash = 0

            jobs = ["Bot Developer", "Stripper", "Janitor", "Cashier", "Pilot"]
            job = random.choice(jobs)

            earnings = random.randint(5, 50)
            
            # Update user's balance with the new earnings
            await db.update_leaderboard_stat(ctx.author, "cash", earnings)

            embed = await db.build_embed(ctx.author.guild, title=f"<a:Cash:1247220739220701184> Work", description=f"You worked as a **{job}** and earned **${earnings}**. Your new balance is **${cash + earnings}**.")
            await ctx.respond(embed=embed)

        except Exception as e:
            print("[e_work]: ", e)


    @commands.slash_command(name="daily", description="Collect your daily earnings.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def e_daily(self, ctx: discord.ApplicationContext):
        try:
            cash_balance = await db.get_leaderboard_data(ctx.author, "cash")

            if cash_balance is None:
                cash_balance = 0

            if cash_balance == 0:
                await db.update_leaderboard_stat(ctx.author, "cash", 100)
                embed = await db.build_embed(ctx.author.guild, title=f"<a:Cash:1247220739220701184> Daily Reward", description=f"You have received your **$100** daily reward.")
                return await ctx.respond(embed=embed)

            await db.update_leaderboard_stat(ctx.author, "cash", 100)

            embed = await db.build_embed(ctx.author.guild, title=f"<a:Cash:1247220739220701184> Daily Reward", description=f"You have received your **$100** daily reward.")
            await ctx.respond(embed=embed)

        except Exception as e:
            print("[e_daily]: ", e)


    @commands.slash_command(name="weekly", description="Collect your weekly earnings.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 604800, commands.BucketType.user)
    async def e_weekly(self, ctx: discord.ApplicationContext):
       
        try:
            # Get user's balance using get_leaderboard_data
            cash_balance = await db.get_leaderboard_data(ctx.author, "cash")

            if cash_balance is None:
                cash_balance = 0

            if cash_balance == 0:
                await db.update_leaderboard_stat(ctx.author, "cash", 1000)
                embed = await db.build_embed(ctx.author.guild, title=f"<a:Cash:1247220739220701184> Weekly Reward", description=f"You have received your **$1000** weekly reward.")
                return await ctx.respond(embed=embed)

            await db.update_leaderboard_stat(ctx.author, "cash", 1000)

            embed = await db.build_embed(ctx.author.guild, title=f"<a:Cash:1247220739220701184> Weekly Reward", description=f"You have received your **$1000** weekly reward.")
            await ctx.respond(embed=embed)

        except Exception as e:
            print("[e_weekly]: ", e)


    @commands.slash_command(name="coinflip", description="Play a game of coinflip.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def e_coinflip(self, ctx: discord.ApplicationContext, bet: Option(int, "The amount to bet.", min_value=1, required=True), side: Option(str, "The side to bet on.", choices=["Heads", "Tails"], required=True)):
        await ctx.defer()
        try:
            cash_balance = await db.get_leaderboard_data(ctx.author, "cash")

            if cash_balance is None:
                cash_balance = 0

            if cash_balance < bet:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You lack the required funds to place this bet.")
                await ctx.respond(embed=embed)
                return 

            coin_sides = ["Heads", "Tails"]
            result = random.choice(coin_sides)

            if result == side:
                earnings = bet
                embed = await db.build_embed(ctx.author.guild, title=f"<a:Coin:1247223148135448629> Coinflip", description=f"The coin landed on **{result}**.\n\nYou won **${bet}**!")
            else:
                earnings = -bet
                embed = await db.build_embed(ctx.author.guild, title=f"<a:Coin:1247223148135448629> Coinflip", description=f"The coin landed on **{result}**.\n\nYou lost **${bet}**.")

            await db.update_leaderboard_stat(ctx.author, "cash", earnings)
            await ctx.respond(embed=embed)

        except Exception as e:
            print(f"[e_coinflip]: ", e)


    @commands.slash_command(name="slots", description="Play a game of slots.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(5, 300, commands.BucketType.user)
    async def e_slots(self, ctx: discord.ApplicationContext, bet: Option(int, "The amount to bet.", min_value=1, required=True)):
        
        try:
            # Get user's cash balance using get_leaderboard_data
            cash_balance = await db.get_leaderboard_data(ctx.author, "cash")

            if cash_balance is None:
                cash_balance = 0

            if cash_balance < bet:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You lack the required funds to place this bet.")
                return await ctx.respond(embed=embed)

            symbols = ["🍒", "🍋", "🍊", "🔔", "7️⃣"]

            payouts = {
                "🍒": 3,
                "🍋": 6,
                "🍊": 9,
                "🔔": 15,
                "7️⃣": 21,
            }

            combination = [random.choice(symbols) for _ in range(3)]
            unique_symbols = set(combination)
            payout = 0

            for symbol in unique_symbols:
                if combination.count(symbol) >= 2:
                    payout += payouts[symbol] * combination.count(symbol)

            combination_str = " | ".join(combination)

            if payout > 0:
                earnings = bet + payout
                embed = await db.build_embed(ctx.author.guild, title=f"<a:Slots:1247220812038279259> Slots", description=f"{combination_str}\n\nCongratulations! You won **${earnings}**!")
            else:
                earnings = -bet
                embed = await db.build_embed(ctx.author.guild, title=f"<a:Slots:1247220812038279259> Slots", description=f"{combination_str}\n\nSorry, you lost **${bet}**.")

            await db.update_leaderboard_stat(ctx.author, "cash", earnings)
            await ctx.respond(embed=embed)

        except Exception as e:
            print("[e_slots]: ", e)


    @commands.slash_command(name="beg", description="Beg for money.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def e_beg(self, ctx: discord.ApplicationContext):
            
            try:
                cash_balance = await db.get_leaderboard_data(ctx.author, "cash")
    
                if cash_balance is None:
                    cash_balance = 0
    
                earnings = random.randint(1, 10)
    
                await db.update_leaderboard_stat(ctx.author, "cash", earnings)
    
                embed = await db.build_embed(ctx.author.guild, title=f"<a:Cash:1247220739220701184> Beg", description=f"You begged and received **${earnings}**.")
                await ctx.respond(embed=embed)
    
            except Exception as e:
                print("[e_beg]: ", e)


    @commands.slash_command(name="transfer", description="Transfer money to another user.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def e_transfer(self, ctx: discord.ApplicationContext, user: Option(discord.Member, "The user to transfer the funds to.", required=True), amount: Option(int, "The amount to transfer.", required=True)):
        
        try:
            if ctx.author == user:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"You can not transfer money to yourself.")
                return await ctx.respond(embed=embed)
            elif user.bot:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"You can not transfer money to a bot.")
                return await ctx.respond(embed=embed)

            # Get the sender's and receiver's cash balances
            sender_balance = await db.get_leaderboard_data(ctx.author, "cash")
            receiver_balance = await db.get_leaderboard_data(user, "cash")

            if sender_balance is None:
                sender_balance = 0

            if receiver_balance is None:
                receiver_balance = 0

            # Check if the sender has enough funds to transfer
            if sender_balance < amount:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"You do not have enough funds to transfer **${amount}**.")
                return await ctx.respond(embed=embed)

            # Update the sender's and receiver's balances
            await db.update_leaderboard_stat(ctx.author, "cash", -amount)
            await db.update_leaderboard_stat(user, "cash", amount)

            embed = await db.build_embed(ctx.author.guild, title=f"<a:Cash:1247220739220701184> Transaction Complete", description=f"You transferred **${amount}** to {user.mention}.")
            await ctx.respond(embed=embed)

        except Exception as e:
            print(f"[e_transfer]: ", e)


    @commands.slash_command(name="rob", description="Rob money from another user.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 18000, commands.BucketType.user)
    async def e_rob(self, ctx: discord.ApplicationContext, user: Option(discord.Member, "The user to rob.", required=True)):
        
        try:
            if ctx.author == user:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"You can not rob yourself.")
                return await ctx.respond(embed=embed, ephemeral=True)
            elif user.bot:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"You can not rob a bot.")
                return await ctx.respond(embed=embed, ephemeral=True)

            # Get the sender's and receiver's cash balances
            sender_balance = await db.get_leaderboard_data(ctx.author, "cash")
            receiver_balance = await db.get_leaderboard_data(user, "cash")

            if sender_balance is None:
                await db.update_leaderboard_stat(ctx.author, "cash", 0)
                sender_balance = 0

            if receiver_balance is None:
                await db.update_leaderboard_stat(user, "cash", 0)
                receiver_balance = 0

            # Check if the receiver has enough money to rob
            if receiver_balance < 10:
                embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"{user.mention} does not have enough money to rob.")
                return await ctx.respond(embed=embed, ephemeral=True)

            one_third_range = receiver_balance // 3

            rob_amount = random.randint(1, one_third_range)

            await db.update_leaderboard_stat(ctx.author, "cash", rob_amount)
            await db.update_leaderboard_stat(user, "cash", -rob_amount)

            embed = await db.build_embed(ctx.author.guild, title=f"<a:Rob:1247220804903763998> Rob Funds", description=f"You robbed **${rob_amount}** from {user.mention}.")
            await ctx.respond(embed=embed)

        except Exception as e:
            print(f"[e_rob]: ", e)


    @commands.slash_command(name="blackjack", description="Play a game of blackjack.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(5, 300, commands.BucketType.user)
    async def blackjack(self, ctx, bet: Option(int, "The amount of money to bet.", min_value=1, required=True)):

        cash_balance = await db.get_leaderboard_data(ctx.author, "cash")

        if cash_balance is None:
            cash_balance = 0

            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You lack the required funds to play.")
            return await ctx.respond(embed=embed)

        if cash_balance < bet:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You lack the required funds to place this bet.")
            return await ctx.respond(embed=embed)

        user_hand = [random.randint(1, 11), random.randint(1, 11)]
        dealer_hand = [random.randint(1, 11), random.randint(1, 11)]

        def calculate_hand_value(hand):
            value = sum(hand)
            if value > 21 and 11 in hand:
                hand.remove(11)
                hand.append(1)
                value = sum(hand)
            return value

        try:
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
                
                11: "♠ A",
                11: "♥ A",
                11: "♦ A",
            }

            user_value = calculate_hand_value(user_hand)
            dealer_value = calculate_hand_value(dealer_hand)
            second_card_value = dealer_hand[1]

            def hand_to_emoji(hand):
                return " ".join([card_emojis[card] for card in hand])

            embed = await db.build_embed(ctx.author.guild, title=f"<a:Cards:1247220738117865553> Blackjack")
            embed.add_field(name=f"Dealers Hand", value=f"❓ {card_emojis.get(second_card_value)} | {dealer_hand[1]}", inline=True)
            embed.add_field(name=f"Your Hand", value=f"{hand_to_emoji(user_hand)} | {user_value}", inline=True)
            return await ctx.respond(embed=embed, view=Blackjack(user_hand, dealer_hand, bet, ctx))
        
        except Exception as e:
            print("[blackjack] ", e)


    @shopSubCommands.command(name="view", description="View the server's shop.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def e_shop(self, ctx: discord.ApplicationContext):
        try:
            shop = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "SHOP")
            if shop:
                shop = json.loads(shop)

                if not shop:
                    embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="The shop is not configured on this server.")
                    return await ctx.respond(embed=embed, ephemeral=True)

                desc = ""
                for item_name, item_details in shop.items():
                    item_price = item_details.get("price")
                    role = item_details.get("role")
                    role = ctx.guild.get_role(role)
                    if role is not None:
                        desc += f"{role.mention} ➭ ${item_price}\n"
                    else:
                        await db.remove_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "SHOP", item_name)

                embed = await db.build_embed(ctx.guild, title=f"<a:Cash:1247220739220701184> {ctx.guild.name}'s Role Shop", description=desc)
                await ctx.respond(embed=embed)

            else:
                embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="The shop is not configured on this server.")
                return await ctx.respond(embed=embed)

        except Exception as e:
            print(f"[e_shop]: ", e)


    @shopadminCommands.command(name="add", description="Add a role to your shop.")
    @commands.bot_has_permissions(manage_roles=True)
    @discord.default_permissions(manage_roles=True)
    @commands.has_guild_permissions(manage_roles=True)
    @commands.check(is_blocked)
    @commands.guild_only()
    async def shop_add(self, ctx: discord.ApplicationContext, 
                    role: Option(discord.Role, "The role to give the buyer.", required=True),
                    price: Option(str, "The price of the role.", required=True)):

        feature = "SHOP"
        data = {
            "price": price,
            "role": role.id
        }

        try:
            shop = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "SHOP")
            if shop:
                shop = json.loads(shop)

                if role.name in shop:
                    embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"{role.mention} is already available in the shop.")
                    return await ctx.respond(embed=embed)

            await db.update_value_in_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", feature, role.name, data)
            embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Shop Updated",
                                        description=f"The {role.mention} role has been added to your shop.")
            await ctx.respond(embed=embed)

        except commands.BadArgument as bad_arg:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=str(bad_arg))
            await ctx.respond(embed=embed, ephemeral=True)

        except Exception as e:
            print("[shop_add]: ", e)
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="An error occurred and the developer was informed.")
            await ctx.respond(embed=embed, ephemeral=True)


    @shopadminCommands.command(name="remove", description="Remove an item to your shop.")
    @commands.has_guild_permissions(manage_roles=True)
    @discord.default_permissions(manage_roles=True)
    @commands.check(is_blocked)
    @commands.guild_only()
    async def shop_remove(self, ctx: discord.ApplicationContext, item: Option(str, "The name of the item to remove.", autocomplete=basic_autocomplete(Utils.get_shop_items), required=True)):

        try:
            shop = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "SHOP")

            if shop:
                shop = json.loads(shop)
                selected_item = shop.get(item)

                if selected_item:
                    await db.remove_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "SHOP", item)
                    embed = await db.build_embed(ctx.author.guild, title=f"{success_emoji} Shop Updated", description=f"The **{item}** role has been removed to your shop.")
                    await ctx.respond(embed=embed)
                else:
                    embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The **{item}** role is not in the shop.")
                    return await ctx.respond(embed=embed, ephemeral=True)
                
        except commands.BadArgument as bad_arg:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=str(bad_arg))
            await ctx.respond(embed=embed, ephemeral=True)

        except Exception as e:
            print("[Configure > Embed]: ", e)
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="An error occurred and the developer was informed.")
            await ctx.respond(embed=embed, ephemeral=True)


    @shopSubCommands.command(name="purchase", description="Purchase a role from the shop.")
    @commands.bot_has_permissions(manage_roles=True)
    @commands.check(is_blocked)
    @commands.guild_only()
    async def purchase(self, ctx: discord.ApplicationContext, item: Option(str, "The item to purchase.", autocomplete=basic_autocomplete(Utils.get_shop_items))):
        try:
            shop = await db.get_value_from_table(ctx.guild.id, "ServerConfigurations", "Setting", "Feature", "SHOP")

            if shop:
                shop = json.loads(shop)
                selected_item = shop.get(item)

                if not selected_item:
                    embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Item Not Found", description=f"The item '{item}' is not available in the shop.")
                    return await ctx.respond(embed=embed)

                price = int(selected_item.get("price"))
                item_type = selected_item.get("type")

                cash_balance = await db.get_leaderboard_data(ctx.author, "cash")

                if cash_balance < price:
                    embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Purchase Failed", description="Insufficient funds. You do not have enough cash to purchase this item.")
                    return await ctx.respond(embed=embed)

                await db.update_leaderboard_stat(ctx.author, "cash", -price)

                role_id = selected_item.get("role")
                role = ctx.guild.get_role(role_id)
                if role:
                    await ctx.author.add_roles(role)

                embed = await db.build_embed(ctx.guild, title=f"{success_emoji} Purchase Successful", description=f"You have purchased the {role.mention} role for **${price}**.")
                await ctx.respond(embed=embed)

        except Exception as e:
            print(f"[purchase]: ", e)


def setup(client):
    client.add_cog(economy(client))