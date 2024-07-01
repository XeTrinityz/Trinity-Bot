# Discord Imports
from discord.ext import commands
from discord import Option
import discord

# Standard / Third-Party Library Imports
from PIL import Image, ImageFilter
import aiohttp
import random
import art
import re
import io

# Local Module Imports
from utils.views import Views, TicTacToe, RockPaperScissors, Connect4, Hangman, GuessTheWord, TOD, AkinatorGame
from utils.lists import wyr_questions
from utils.database import Database
from Bot import is_blocked
from utils.lists import *

db = Database()

class games(commands.Cog):
    def __init__(self, client):
        self.client = client

    gameSubCommands = discord.SlashCommandGroup("games", "Akinator, TickTacToe, Connect 4, Hangman, Rock Paper Scissors, Would You Rather, Truth or Dare.")
    todSubCommands = gameSubCommands.create_subgroup("tod", "Truth, Dare.")

    textSubCommands = discord.SlashCommandGroup("text", "ASCII, Encode, Decode, Reverse, Emojify, Mock, Morse.")
    interactionSubCommands = discord.SlashCommandGroup("interact", "Hug, Kiss, Slap")

    @commands.message_command(name="Mock Message", description="Mock a members message.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def mock_message(self, ctx: discord.ApplicationContext, message: discord.Message):

        if message.embeds:
            embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description="I can not mock an embed.")
            await ctx.respond(embed=embed, ephemeral=True)
            return 
        
        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Mocking Message", description=f"Mocking {message.author.mention}'s message...")
        await ctx.respond(embed=embed, ephemeral=True)
        
        mocked_message = ''.join(random.choice((str.upper, str.lower))(char) for char in message.content)

        await message.reply(mocked_message)
        embed = await db.build_embed(ctx.author.guild, title=f"😆 Message Mocked", description=f"{message.author.mention}'s message has been mocked.")
        await ctx.edit(embed=embed)


    @gameSubCommands.command(name="wyr", description="Play would you rather.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def wyr(self, ctx: discord.ApplicationContext):

        question = random.choice(wyr_questions)
        question = re.sub(r'^Would you rather', '', question).strip()
        options = [option.strip() for option in re.split(r'\sor\s', question, flags=re.IGNORECASE)]
        question_1, question_2 = options

        embed = await db.build_embed(ctx.author.guild, title=f"❓ Would you rather...",
            description=f"{question_1.capitalize()}?\n"
            +
            " ---------------------- **OR** ---------------------- \n"
            +
            f"{question_2.capitalize()}")
        
        await ctx.respond(embed=embed, view=Views.www("Option 2", "Option 1"))


    @gameSubCommands.command(name="akinator", description="Play with Akinator.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def akinator(self, ctx: discord.ApplicationContext):

        game = AkinatorGame(ctx, ctx.author)
        await game.akinator_game()


    @todSubCommands.command(name="dare", description="Gives you a dare to complete.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def tod(self, ctx: discord.ApplicationContext):

        dare = random.choice(dares)
        embed = await db.build_embed(ctx.author.guild, title="", description=f"### {dare}")
        await ctx.respond(embed=embed, view=TOD())

    
    @todSubCommands.command(name="truth", description="Gives you a truth to answer.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def truth(self, ctx: discord.ApplicationContext):
            
            truth = random.choice(truths)
            embed = await db.build_embed(ctx.author.guild, title="", description=f"### {truth}")
            await ctx.respond(embed=embed, view=TOD())

    
    @gameSubCommands.command(name="8ball", description="Ask the magic 8ball a question.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def eight_ball(self, ctx: discord.ApplicationContext, question: Option(str, "The question to ask.")):

        embed = await db.build_embed(ctx.author.guild, title=f"🎱 Magic 8 Ball", description=f"**Question** ➭ {question}\n**Answer** ➭ {random.choice(eight_ball_answers)}")
        await ctx.respond(embed=embed)

    
    @gameSubCommands.command(name="hangman", description="Play a game of hangman.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def hangman(self, ctx: discord.ApplicationContext, word: Option(str, "The word to guess.", min_length=3, max_length=30, required=False)):
        
        if word:
            word = word.replace(" ", "")
            word = word.lower()
            word_length = len(word)
            placeholder = "🟦" * word_length
        else:
            random_word = random.choice(hangman_words)
            random_word = random_word.lower()
            word_length = len(random_word)
            placeholder = "🟦" * word_length
                    
        embed = await db.build_embed(ctx.author.guild, title=f"🎮 Hangman", description="Use the buttons below to play!")
        embed.add_field(name="Word", value=placeholder, inline=True)
        embed.add_field(name="Guesses", value="10", inline=True)

        if word:
            await ctx.respond("Game Started", ephemeral=True)
            await ctx.channel.send(embed=embed, view=Hangman(ctx, word))
        else:
            await ctx.respond(embed=embed, view=Hangman(ctx, random_word))


    @gameSubCommands.command(name="guess-the-word", description="Play a game of guess the word.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def gtw(
        self, ctx: discord.ApplicationContext, 
        word: Option(str, "The word to guess."),
        image: Option(discord.Attachment, "The image to help describe the word.", required=False),
        pixel_level: Option(int, "The level of pixelation. (Lower = More Pixelation)", min_value=1, max_value=100, default=45, required=False),
    ):
        if image and image.content_type not in ["image/png", "image/jpg", "image/jpeg", "image/gif"]:
            embed = await db.build_embed(
                ctx.author.guild, 
                title=f"{error_emoji} Request Failed", 
                description=f"The image should be a png, jpg/jpeg, or gif."
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        try:
            word = word.lower()
            placeholder = "".join(["🟦" if char.isalpha() else " " for char in word])

            embed = await db.build_embed(
                ctx.author.guild, 
                title=f"🎮 Guess The Word", 
                description="Use the button below to guess!"
            )
            embed.add_field(name="Word", value=placeholder, inline=True)

            if image:
                image_data = await image.read()
                image_bytes = io.BytesIO(image_data)

                # Open the image using Pillow
                img = Image.open(image_bytes)

                # Resize the image smoothly down to 16x16 pixels
                img_small = img.resize((pixel_level, pixel_level), resample=Image.BILINEAR)

                # Scale back up using NEAREST to original size
                img_pixelated = img_small.resize(img.size, resample=Image.NEAREST)

                # Save the pixelated image to a new BytesIO buffer
                pixelated_buffer = io.BytesIO()
                img_pixelated.save(pixelated_buffer, format="PNG")
                pixelated_buffer.seek(0)

                file = discord.File(pixelated_buffer, filename="pixelated_image.png")
                embed.set_image(url=f"attachment://pixelated_image.png")

                await ctx.channel.send(embed=embed, file=file, view=GuessTheWord(ctx, word, has_image=image))
            else:
                await ctx.channel.send(embed=embed, view=GuessTheWord(ctx, word, has_image=None))
            await ctx.respond("Game Started", ephemeral=True)
        except Exception as e:
            print(e)

    
    @gameSubCommands.command(name="rps", description="Play rock paper scissors.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def rps(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to play with.")):

        if member == ctx.author:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You can not play on your own.")
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        elif member.bot:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You can not play with a bot.")
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        embed = await db.build_embed(ctx.author.guild, title=f"🎮 Rock Paper Scissors", description="Use the buttons below to play!")
        embed.add_field(name=ctx.author.display_name, value="ﾠﾠ❔ﾠﾠ", inline=True)
        embed.add_field(name="VS", value="⚡", inline=True)
        embed.add_field(name=member.display_name, value="ﾠﾠ❔ﾠﾠ", inline=True)
        await ctx.respond(content=f"{ctx.author.mention} wants to play RPC with {member.mention}.",embed=embed, view=RockPaperScissors(ctx.author, member))


    @gameSubCommands.command(name="tictactoe", description="Play a game of TicTacToe.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def game_tictac(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to play with.")):

        if member == ctx.author:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You can not play on your own.")
            await ctx.respond(embed=embed, ephemeral=True)
            return
        elif member.bot:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You can not play with a bot.")
            await ctx.respond(embed=embed, ephemeral=True)
            return

        embed = await db.build_embed(ctx.author.guild, title=f"🎮 TicTacToe", description="The first to match 3 in a row wins!")
        embed.add_field(name="Turn", value=f"{ctx.author.mention} [**X**]", inline=True)
        await ctx.respond(f"{ctx.author.mention} wants to play TicTacToe with {member.mention}", embed=embed, view=TicTacToe(player1=ctx.author, player2=member))


    @gameSubCommands.command(name="connect4", description="Play a game of Connect 4.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def game_cnct4(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to play with.")):

        if member == ctx.author:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You can not play on your own.")
            await ctx.respond(embed=embed, ephemeral=True)
            return
        elif member.bot:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="You can not play with a bot.")
            await ctx.respond(embed=embed, ephemeral=True)
            return

        embed = await db.build_embed(ctx.author.guild, title=f"🎮 Connect 4", description="The first to match 4 in a row wins!")
        await ctx.respond(f"{ctx.author.mention} wants to play Connect 4 with {member.mention}", embed=embed, view=Connect4(player1=ctx.author, player2=member))


    @textSubCommands.command(name="ascii", description="Converts text to ascii art.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def ascii(self, ctx: discord.ApplicationContext, text: Option(str, "The text to convert.")):

        ascii = art.text2art(text)
        lines = ascii.split('\n')
        truncated_lines = [line[:61] for line in lines]
        ascii = '\n'.join(truncated_lines)

        embed = await db.build_embed(ctx.author.guild, title=f"🎨 ASCII Art", description=f"```{ascii}```")
        await ctx.respond(embed=embed)


    @textSubCommands.command(name="lulcat", description="Converts text to lulcat.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def lulcat(self, ctx: discord.ApplicationContext, text: Option(str, "The text to convert.")):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Converting Text", description="Converting your text to Lul Cat speak...")
        await ctx.respond(embed=embed)

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.popcat.xyz/lulcat?text={text}") as a:
                data = await a.json(content_type="application/json")

        embed = await db.build_embed(ctx.author.guild, title=f"😸 Lul Cat Converter", description=data["text"])
        await ctx.edit(embed=embed)


    @textSubCommands.command(name="emojify", description="Converts text to emojis.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def emojify(self, ctx: discord.ApplicationContext, text: Option(str, "The text to convert.")):
        try:
            emoji_dict = {
                'a': ':regional_indicator_a:', 'b': ':regional_indicator_b:', 'c': ':regional_indicator_c:',
                'd': ':regional_indicator_d:', 'e': ':regional_indicator_e:', 'f': ':regional_indicator_f:',
                'g': ':regional_indicator_g:', 'h': ':regional_indicator_h:', 'i': ':regional_indicator_i:',
                'j': ':regional_indicator_j:', 'k': ':regional_indicator_k:', 'l': ':regional_indicator_l:',
                'm': ':regional_indicator_m:', 'n': ':regional_indicator_n:', 'o': ':regional_indicator_o:',
                'p': ':regional_indicator_p:', 'q': ':regional_indicator_q:', 'r': ':regional_indicator_r:',
                's': ':regional_indicator_s:', 't': ':regional_indicator_t:', 'u': ':regional_indicator_u:',
                'v': ':regional_indicator_v:', 'w': ':regional_indicator_w:', 'x': ':regional_indicator_x:',
                'y': ':regional_indicator_y:', 'z': ':regional_indicator_z:',
                ' ': ' '
            }

            emojified_text = ''.join([emoji_dict.get(c.lower(), c) for c in text])
            await ctx.respond(emojified_text)
        except Exception as e:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"```{e}```")
            await ctx.respond(embed=embed, ephemeral=True)


    @textSubCommands.command(name="encode", description="Encode text to binary.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def encode(self, ctx: discord.ApplicationContext, text: Option(str, "The text to convert.")):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Encoding Text", description="Encoding your text...")
        await ctx.respond(embed=embed)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.popcat.xyz/encode?text={text}") as a:
                data = await a.json(content_type="application/json")

        embed = await db.build_embed(ctx.author.guild, title=f"🔐 Text Encoded", description=data["binary"])
        await ctx.edit(embed=embed)


    @textSubCommands.command(name="decode", description="Decode binary to text.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def decode(self, ctx: discord.ApplicationContext, text: Option(str, "The text to convert.")):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Decoding Text", description="Decoding your encoded text...")
        await ctx.respond(embed=embed)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.popcat.xyz/decode?binary={text}") as a:
                data = await a.json(content_type="application/json")

        embed = await db.build_embed(ctx.author.guild, title=f"🔓 Text Decoded", description=data["text"])
        await ctx.edit(embed=embed)


    @textSubCommands.command(name="reverse", description="Reverse text.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def reverse(self, ctx: discord.ApplicationContext, text: Option(str, "The text to convert.")):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Reversing Text", description="Reversing your text...")
        await ctx.respond(embed=embed)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.popcat.xyz/reverse?text={text}") as a:
                data = await a.json(content_type="application/json")

        embed = await db.build_embed(ctx.author.guild, title=f"⏪ Text Reversed", description=data["text"])
        await ctx.edit(embed=embed)


    @textSubCommands.command(name="morse", description="Convert text to morse code.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def morse(self, ctx: discord.ApplicationContext, text: Option(str, "The text to convert.")):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Converting Text", description="Converting your text to morse code...")
        await ctx.respond(embed=embed)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.popcat.xyz/texttomorse?text={text}") as a:
                data = await a.json(content_type="application/json")

        embed = await db.build_embed(ctx.author.guild, title=f"👨‍💻 Morse Code", description=data["morse"])
        await ctx.edit(embed=embed)


    @textSubCommands.command(name="mock", description="Mock a users message.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def mock(self, ctx: discord.ApplicationContext, message_id: Option(str, "The message ID of the message.")):

        try:
            channel = ctx.channel
            message = await channel.fetch_message(int(message_id))
        except:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="I could not find the message.")
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Mocking Message", description=f"Mocking {message.author.mention}'s message...")
        await ctx.respond(embed=embed, ephemeral=True)
        
        mocked_message = ''.join(random.choice((str.upper, str.lower))(char) for char in message.content)

        await message.reply(mocked_message)
        embed = await db.build_embed(ctx.author.guild, title=f"😆 Message Mocked", description=f"{message.author.mention}'s message has been mocked.")
        await ctx.edit(embed=embed, ephemeral=True)


    @commands.slash_command(name="pickupline", description="Generate a random pickup line.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def pickupline(self, ctx: discord.ApplicationContext):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Generating Text", description="Generating a random pickup line...")
        await ctx.respond(embed=embed)
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.popcat.xyz/pickuplines") as a:
                data = await a.json(content_type="application/json")

        embed = await db.build_embed(ctx.author.guild, title=f"♥ Pickup Line", description=data["pickupline"])
        await ctx.edit(embed=embed)


    @commands.slash_command(name="showerthoughts", description="Generate a random shower thought.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def showerthoughts(self, ctx: discord.ApplicationContext):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Generating Text", description="Generating a random shower thought...")
        await ctx.respond(embed=embed)
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.popcat.xyz/showerthoughts") as a:
                data = await a.json(content_type="application/json")

        embed = await db.build_embed(ctx.author.guild, title=f"🤔 Shower Thought", description=data["result"])
        await ctx.edit(embed=embed)

 
    @commands.slash_command(name="fact", description="Generate a random fact.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def random_fact(self, ctx: discord.ApplicationContext):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Generating Text", description="Generating a random fact...")
        await ctx.respond(embed=embed)
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.popcat.xyz/fact") as a:
                data = await a.json(content_type="application/json")

        embed = await db.build_embed(ctx.author.guild, title=f"🧠 Random Fact", description=data["fact"])
        await ctx.edit(embed=embed)


    @commands.slash_command(name="joke", description="Generate a random joke.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def joke(self, ctx: discord.ApplicationContext):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Generating Text", description="Generating a random joke...")
        await ctx.respond(embed=embed)
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.popcat.xyz/joke") as a:
                data = await a.json(content_type="application/json")

        embed = await db.build_embed(ctx.author.guild, title=f"🤣 Random Joke", description=data["joke"])
        await ctx.edit(embed=embed)


    @interactionSubCommands.command(name="pet", description="Pet a member.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def pet(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to pet.")):

        url = next(pats)

        if url == "api":
            embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Petting", description=f"Petting {member.mention}...")
            await ctx.respond(embed=embed)
            image = member.avatar.url if member.avatar else member.default_avatar.url
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.popcat.xyz/pet?image={image}") as response:
                    if response.status == 200:
                        image_data = await response.read()
                        image_file = io.BytesIO(image_data)
                        image_attachment = discord.File(image_file, filename="image.gif")

                        embed = await db.build_embed(ctx.author.guild, title=f"🖐 Pet", description=f"{ctx.author.mention} petted {member.mention}.")
                        embed.set_image(url=f"attachment://image.gif")
                        await ctx.edit(embed=embed, file=image_attachment)
                    else:
                        embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="I could not generate a pet image.")
                        await ctx.edit(embed=embed)
        else:
            embed = await db.build_embed(ctx.author.guild, title=f"🖐 Pet", description=f"{ctx.author.mention} petted {member.mention}.")
            embed.set_image(url=url)
            await ctx.respond(embed=embed)

    
    @interactionSubCommands.command(name="hug", description="Hug a member.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def hug(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to hug.")):
        
        embed = await db.build_embed(ctx.author.guild, title=f"🤗 Hug", description=f"{ctx.author.mention} hugged {member.mention}.")
        embed.set_image(url=next(hugs))
        await ctx.respond(embed=embed)

    
    @interactionSubCommands.command(name="kiss", description="Kiss a member.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def kiss(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to kiss.")):

        embed = await db.build_embed(ctx.author.guild, title=f"😘 Kiss", description=f"{ctx.author.mention} kissed {member.mention}.")
        embed.set_image(url=next(kisses))
        await ctx.respond(embed=embed)


    @interactionSubCommands.command(name="slap", description="Slap a member.")
    @commands.check(is_blocked)
    @commands.guild_only()
    async def slap(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to slap.")):

        embed = await db.build_embed(ctx.author.guild, title=f"👋 Slap", description=f"{ctx.author.mention} slapped {member.mention}.")
        embed.set_image(url=next(slaps))
        await ctx.respond(embed=embed)


def setup(client):
    client.add_cog(games(client))