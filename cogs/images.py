# Discord Imports
from discord.ext import commands
from discord import Option
import discord

# Standard / Third-Party Library Imports
import textwrap
import qrcode
import aiohttp
import random
import io

# Local Module Imports
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from utils.database import Database
from utils.functions import Utils
from utils.views import Views
from Bot import is_blocked
from utils.lists import *
db = Database()

# COG CLASS
# ---------
class images(commands.Cog):
    def __init__(self, client):
        self.client = client

    imageSubCommands = discord.SlashCommandGroup("image", "Meme, Jail, WWW, SadCat, QR Code, Car, Generate, Biden, Drake, Drip, Ship.")
    imageManipulationSubCommands = imageSubCommands.create_subgroup(name="manipulation", description="Manipulate an image.")

    @imageSubCommands.command(name="qrcode", description="Generate a QR code.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def qrcode(self, ctx: discord.ApplicationContext, data: Option(str, "The data the QR code will display.")):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Generating Image", description="The image is being generated...")
        await ctx.respond(embed=embed)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )

        qr.add_data(data)
        qr.make(fit=True)

        # Create an instance of the QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")

        # Save the QR code image to a bytes buffer
        qr_buffer = io.BytesIO()
        qr_image.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)

        # Send the QR code image
        embed = await db.build_embed(ctx.guild, title="")
        qr_file = discord.File(qr_buffer, filename="QRCode.png")
        embed.set_image(url="attachment://QRCode.png")
        await ctx.edit(embed=embed, file=qr_file)


    @imageManipulationSubCommands.command(name="jail", description="Put a user in jail.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def jail(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to jail.")):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Generating Image", description="The image is being generated...")
        await ctx.respond(embed=embed)

        avatar_url = member.avatar.with_format('png')

        async with aiohttp.ClientSession() as session:
            async with session.get(str(avatar_url)) as response:
                if response.status == 200:
                    avatar_data = await response.read()
                    avatar_image = Image.open(io.BytesIO(avatar_data)).convert("RGBA")

                    # Load the overlay image
                    overlay_path = "images/Jail.png"  # Replace with your own overlay image
                    overlay_image = Image.open(overlay_path).convert("RGBA")

                    # Resize overlay to fit the avatar
                    overlay_image = overlay_image.resize(avatar_image.size)

                    # Merge the images
                    merged_image = Image.alpha_composite(avatar_image, overlay_image)

                    # Adjust the opacity
                    opacity = 1  # Set your desired opacity value between 0 and 1
                    final_image = Image.blend(avatar_image, merged_image, opacity)

                    # Save the final image to a bytes buffer
                    final_image_buffer = io.BytesIO()
                    final_image.save(final_image_buffer, format="PNG")
                    final_image_buffer.seek(0)

                    # Send the final image
                    file = discord.File(final_image_buffer, filename="Jail.png")
                    embed = await db.build_embed(ctx.author.guild, title=f"")
                    embed.set_image(url="attachment://Jail.png")
                    await ctx.edit(embed=embed, file=file)


    @imageSubCommands.command(name="generate", description="Generate an image from text.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 600, commands.BucketType.user)
    async def genimage(self, ctx: discord.ApplicationContext, prompt: Option(str, "The text to generate the image from.", max_length=100)):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Generating Image", description="The image is being generated...")
        await ctx.respond(embed=embed)

        try:
            api_key = ""
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.openai.com/v1/images/generations',
                    headers={
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        "model": "dall-e-3",
                        "prompt": prompt,
                        "n": 1,
                        "size": "1024x1024"
                    }
                ) as resp:
                    response = await resp.json()
                    embed = await db.build_embed(ctx.guild, title="")
                    embed.set_image(url=response['data'][0]['url'])
                    await ctx.edit(embed=embed)
        except:
            ctx.command.reset_cooldown(ctx)
            embed = await db.build_embed(ctx.guild, title=f"{error_emoji} Request Failed", description=response['error']['message'])
            await ctx.edit(embed=embed)


    @imageManipulationSubCommands.command(name="sharpen", description="Sharpen an image.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def sharpenimage(self, ctx: discord.ApplicationContext, image: Option(discord.Attachment, "The image to sharpen.")):
        
        if image.content_type not in ["image/png", "image/jpg", "image/jpeg", "image/gif"]:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The image should be a png or jpg/jpeg.")
            await ctx.respond(embed=embed, ephemeral=True)
            return

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Sharpening Image", description="The image is being sharpened...")
        await ctx.respond(embed=embed)

        async with aiohttp.ClientSession() as session:
            async with session.get(image.url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    image_pil = Image.open(io.BytesIO(image_data))
                    sharpened_image = image_pil.filter(ImageFilter.SHARPEN)

                    final_image_buffer = io.BytesIO()
                    sharpened_image.save(final_image_buffer, format="PNG")
                    final_image_buffer.seek(0)

                    file = discord.File(final_image_buffer, filename="sharpened_image.png")
                    embed = await db.build_embed(ctx.author.guild, title=f"")
                    embed.set_image(url="attachment://sharpened_image.png")
                    await ctx.edit(embed=embed, file=file)

                else:
                    embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"An error occurred while processing the image.")
                    await ctx.edit(embed=embed)
                    return


    @imageManipulationSubCommands.command(name="colorize", description="Convert a black & white image to color.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def colorizeimage(self, ctx: discord.ApplicationContext, image: Option(discord.Attachment, "The image to colorize.")):

        if image.content_type not in ["image/png", "image/jpg", "image/jpeg", "image/gif"]:
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The image should be a png or jpg/jpeg.")
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Colorizing Image", description="The image is being colorized...")
        await ctx.respond(embed=embed)

        data = {
            "image": image.url
        }
        headers = {
            "api-key": ""
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"https://api.deepai.org/api/torch-srgan", data=data, headers=headers) as response:
                if response.status == 200:
                    response = await response.json()
                    image_url = response["output_url"]
                else:
                    embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"An error occured while generating the image.")
                    await ctx.edit(embed=embed)
                    return

            async with session.get(image_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    image_file = io.BytesIO(image_data)
                    image_attachment = discord.File(image_file, filename="image.png")

                    embed = await db.build_embed(ctx.author.guild, title=f"")
                    embed.set_image(url=f"attachment://image.png")
                    await ctx.edit(embed=embed, file=image_attachment)
                else:
                    embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"An error occured while generating the image.")
                    await ctx.edit(embed=embed)
                    return


    @imageManipulationSubCommands.command(name="sadcat", description="Generate a sad cat meme.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def sadcat(self, ctx: discord.ApplicationContext, text: Option(str, "The text to use on the image.")):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Generating Image", description="The image is being generated...")
        await ctx.respond(embed=embed)

        base_image_path = "images/SadCat.png"  # Replace with the path to your base image
        base_image = Image.open(base_image_path)

        # Set up drawing context
        draw = ImageDraw.Draw(base_image)

        # Set up font
        font_path = "images/arial.ttf"  # Replace with the path to your font file
        font_size = 40
        font = ImageFont.truetype(font_path, font_size)

        # Set text position
        text_x = 440  # Adjust the X position as needed
        text_y = 663  # Adjust the Y position as needed

        # Set text color
        text_color = (255, 255, 255)  # White color

        lines = textwrap.wrap(text, width=10)
        for line in lines:
            width, height = draw.textsize(line, font=font)
            draw.text((text_x, text_y), line, fill=text_color, font=font, align="center")
            text_y += height

        # Save the modified image to a bytes buffer
        final_image_buffer = io.BytesIO()
        base_image.save(final_image_buffer, format="PNG")
        final_image_buffer.seek(0)

        file = discord.File(final_image_buffer, filename="sadcat.png")
        embed = await db.build_embed(ctx.author.guild, title="")
        embed.set_image(url="attachment://sadcat.png")
        await ctx.edit(embed=embed, file=file)
        

    @imageManipulationSubCommands.command(name="oogway", description="Generate an Oogway quote.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def oogway(self, ctx: discord.ApplicationContext, text: Option(str, "The text to use on the image.")):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Generating Image", description="The image is being generated...")
        await ctx.respond(embed=embed)

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.popcat.xyz/oogway?text={text}") as response:
                if response.status == 200:
                    image_data = await response.read()
                    image_file = io.BytesIO(image_data)
                    image_attachment = discord.File(image_file, filename="image.png")
   
                    embed = await db.build_embed(ctx.author.guild, title=f"")
                    embed.set_image(url="attachment://image.png")
                    await ctx.edit(embed=embed, file=image_attachment)


    @imageManipulationSubCommands.command(name="communism", description="Apply a communist overlay to a members avatar.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def communism(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to apply the overlay to.")):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Generating Image", description="The image is being generated...")
        await ctx.respond(embed=embed)

        avatar_url = member.display_avatar.with_format('png')

        async with aiohttp.ClientSession() as session:
            async with session.get(str(avatar_url)) as response:
                if response.status == 200:
                    avatar_data = await response.read()
                    avatar_image = Image.open(io.BytesIO(avatar_data)).convert("RGBA")

                    # Load the overlay image
                    overlay_path = "images/Communism.png"  # Replace with your own overlay image
                    overlay_image = Image.open(overlay_path).convert("RGBA")

                    # Resize overlay to fit the avatar
                    overlay_image = overlay_image.resize(avatar_image.size)

                    # Merge the images
                    merged_image = Image.alpha_composite(avatar_image, overlay_image)

                    # Adjust the opacity
                    opacity = 0.5  # Set your desired opacity value between 0 and 1
                    final_image = Image.blend(avatar_image, merged_image, opacity)

                    # Save the final image to a bytes buffer
                    final_image_buffer = io.BytesIO()
                    final_image.save(final_image_buffer, format="PNG")
                    final_image_buffer.seek(0)

                    # Send the final image
                    file = discord.File(final_image_buffer, filename="Communism.png")
                    embed = await db.build_embed(ctx.author.guild, title=f"")
                    embed.set_image(url="attachment://Communism.png")
                    await ctx.edit(embed=embed, file=file)


    @imageSubCommands.command(name="car", description="Get a random car image.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def car(self, ctx: discord.ApplicationContext):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Generating Image", description="The image is being generated...")
        await ctx.respond(embed=embed)

        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.popcat.xyz/car") as response:
                if response.status == 200:
                    data = await response.json()
                    embed = await db.build_embed(ctx.author.guild, title=f"")
                    embed.set_image(url=data["image"])
                    await ctx.edit(embed=embed)
                else:
                    embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The API is currently down, please try again later.")
                    await ctx.respond(embed=embed, ephemeral=True)


    @imageManipulationSubCommands.command(name="pooh", description="Generate a pooh meme.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def pooh(self, ctx: discord.ApplicationContext, text_1: Option(str, "The first text to use on the image."), text_2: Option(str, "The second text to use on the image.")):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Generating Image", description="The image is being generated...")
        await ctx.respond(embed=embed)

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.popcat.xyz/pooh?text1={text_1}&text2={text_2}") as response:
                if response.status == 200:
                    image_data = await response.read()
                    image_file = io.BytesIO(image_data)
                    image_attachment = discord.File(image_file, filename="image.png")
   
                    embed = await db.build_embed(ctx.author.guild, title=f"")
                    embed.set_image(url="attachment://image.png")
                    await ctx.edit(embed=embed, file=image_attachment)
                else:
                    embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The API is currently down, please try again later.")
                    await ctx.respond(embed=embed, ephemeral=True)

    @imageManipulationSubCommands.command(name="drake", description="Generate a drake meme.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def drake(self, ctx: discord.ApplicationContext, text_1: Option(str, "The first text to use on the image."), text_2: Option(str, "The second text to use on the image.")):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Generating Image", description="The image is being generated...")
        await ctx.respond(embed=embed)

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.popcat.xyz/drake?text1={text_1}&text2={text_2}") as response:
                if response.status == 200:
                    image_data = await response.read()
                    image_file = io.BytesIO(image_data)
                    image_attachment = discord.File(image_file, filename="image.png")
   
                    embed = await db.build_embed(ctx.author.guild, title=f"")
                    embed.set_image(url="attachment://image.png")
                    await ctx.edit(embed=embed, file=image_attachment)
                else:
                    embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description="The API is currently down, please try again later.")
                    await ctx.respond(embed=embed, ephemeral=True)

    @imageManipulationSubCommands.command(name="wanted", description="Generate a wanted poster.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def wanted(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to use on the image.")):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Generating Image", description="The image is being generated...")
        await ctx.respond(embed=embed)

        base_image_path = "images/Wanted.png"  # Replace with the path to your base image
        base_image = Image.open(base_image_path)

        user_1_av = member.display_avatar.with_size(256)

        async with aiohttp.ClientSession() as session:
            async with session.get(str(user_1_av)) as response:
                if response.status == 200:
                    image_data = await response.read()
                    avatar_image = Image.open(io.BytesIO(image_data))
                    avatar_image = avatar_image.resize((414, 414))  # Resize the avatar

                    # Paste the avatar onto the base image
                    base_image.paste(avatar_image, (161, 303))

                    # Save the modified image to a bytes buffer
                    final_image_buffer = io.BytesIO()
                    base_image.save(final_image_buffer, format="PNG")
                    final_image_buffer.seek(0)

                    file = discord.File(final_image_buffer, filename="wanted.png")
                    embed = await db.build_embed(ctx.author.guild, title="")
                    embed.set_image(url="attachment://wanted.png")
                    await ctx.edit(embed=embed, file=file)


    @imageManipulationSubCommands.command(name="drip", description="Give a user some drip.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def drip(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to use on the image.")):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Generating Image", description="The image is being generated...")
        await ctx.respond(embed=embed)

        user_1_av = member.display_avatar.url

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.popcat.xyz/drip?image={user_1_av}") as response:
                if response.status == 200:
                    image_data = await response.read()
                    image_file = io.BytesIO(image_data)
                    image_attachment = discord.File(image_file, filename="image.png")
   
                    embed = await db.build_embed(ctx.author.guild, title=f"")
                    embed.set_image(url="attachment://image.png")
                    await ctx.edit(embed=embed, file=image_attachment)


    @imageManipulationSubCommands.command(name="clown", description="This user is a clown.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def clown(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to use on the image.")):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Generating Image", description="The image is being generated...")
        await ctx.respond(embed=embed)

        user_1_av = member.display_avatar.url

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.popcat.xyz/clown?image={user_1_av}") as response:
                if response.status == 200:
                    image_data = await response.read()
                    image_file = io.BytesIO(image_data)
                    image_attachment = discord.File(image_file, filename="image.png")
   
                    embed = await db.build_embed(ctx.author.guild, title=f"")
                    embed.set_image(url="attachment://image.png")
                    await ctx.edit(embed=embed, file=image_attachment)


    @imageManipulationSubCommands.command(name="colorify", description="Overlay an avatar with colors.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def colorify(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to use on the image."), color: Option(str, "The color to overlay")):

        if not Utils.is_valid_hex_color(color):
            embed = await db.build_embed(ctx.author.guild, title=f"{error_emoji} Request Failed", description=f"The color should use the following format - #FFFFFF.")
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Generating Image", description="The image is being generated...")
        await ctx.respond(embed=embed)
        
        user_1_av = member.display_avatar.url

        if color.startswith("#"):
            color = color[1:]

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.popcat.xyz/colorify?image={user_1_av}&color={color}") as response:
                if response.status == 200:
                    image_data = await response.read()
                    image_file = io.BytesIO(image_data)
                    image_attachment = discord.File(image_file, filename="image.png")
   
                    embed = await db.build_embed(ctx.author.guild, title=f"")
                    embed.set_image(url="attachment://image.png")
                    await ctx.edit(embed=embed, file=image_attachment)


    @imageManipulationSubCommands.command(name="biden", description="Generate a Biden tweet.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def biden(self, ctx: discord.ApplicationContext, text: Option(str, "The text to use on the image.")):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Generating Image", description="The image is being generated...")
        await ctx.respond(embed=embed)

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.popcat.xyz/biden?text={text}") as response:
                if response.status == 200:
                    image_data = await response.read()
                    image_file = io.BytesIO(image_data)
                    image_attachment = discord.File(image_file, filename="image.png")
   
                    embed = await db.build_embed(ctx.author.guild, title=f"")
                    embed.set_image(url="attachment://image.png")
                    await ctx.edit(embed=embed, file=image_attachment)


    @imageManipulationSubCommands.command(name="pikachu", description="Generate a surprised Pikachu meme.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def pikachu(self, ctx: discord.ApplicationContext, text: Option(str, "The text to use on the image.")):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Generating Image", description="The image is being generated...")
        await ctx.respond(embed=embed)

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.popcat.xyz/pikachu?text={text}") as response:
                if response.status == 200:
                    image_data = await response.read()
                    image_file = io.BytesIO(image_data)
                    image_attachment = discord.File(image_file, filename="image.png")
   
                    embed = await db.build_embed(ctx.author.guild, title=f"")
                    embed.set_image(url="attachment://image.png")
                    await ctx.edit(embed=embed, file=image_attachment)


    @imageManipulationSubCommands.command(name="whowouldwin", description="Generate a who would win image.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def whowouldwin(self, ctx: discord.ApplicationContext, member_1: Option(discord.Member, "The first member to use on the image."), member_2: Option(discord.Member, "The second member to use on the image.")):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Generating Image", description="The image is being generated...")
        await ctx.respond(embed=embed)

        user_1_av = member_1.display_avatar.url
        user_2_av = member_2.display_avatar.url

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.popcat.xyz/whowouldwin?image2={user_1_av}&image1={user_2_av}") as response:
                if response.status == 200:
                    image_data = await response.read()
                    image_file = io.BytesIO(image_data)
                    image_attachment = discord.File(image_file, filename="image.png")

                    embed = await db.build_embed(ctx.author.guild, title=f"")
                    embed.set_image(url="attachment://image.png")
                    await ctx.edit(embed=embed, view=Views.www(member_1.display_name, member_2.display_name), file=image_attachment)


    @imageManipulationSubCommands.command(name="ship", description="Ship two people together.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def ship(self, ctx: discord.ApplicationContext, member_1: Option(discord.Member, "The first member to use on the image."), member_2: Option(discord.Member, "The second member to use on the image.")):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Generating Image", description="The image is being generated...")
        await ctx.respond(embed=embed)

        user_1_av = member_1.display_avatar.url
        user_2_av = member_2.display_avatar.url

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.aggelos-007.xyz/ship?avatar1={user_1_av}&avatar2={user_2_av}&number={random.randint(1, 100)}") as response:
                if response.status == 200:
                    image_data = await response.read()
                    image_file = io.BytesIO(image_data)
                    image_attachment = discord.File(image_file, filename="image.png")

                    embed = await db.build_embed(ctx.author.guild, title=f"")
                    embed.set_image(url="attachment://image.png")
                    await ctx.edit(embed=embed, file=image_attachment)


    @imageManipulationSubCommands.command(name="sus", description="Someone is sus.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def sus(self, ctx: discord.ApplicationContext, imposter: Option(discord.Member, "The first member to use on the image."), crewmate: Option(discord.Member, "The second member to use on the image.")):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Generating Image", description="The image is being generated...")
        await ctx.respond(embed=embed)

        user_1_av = imposter.display_avatar.url
        user_2_av = crewmate.display_avatar.url

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.aggelos-007.xyz/sus?impostor={user_1_av}&crewmate={user_2_av}") as response:
                if response.status == 200:
                    image_data = await response.read()
                    image_file = io.BytesIO(image_data)
                    image_attachment = discord.File(image_file, filename="image.png")

                    embed = await db.build_embed(ctx.author.guild, title=f"")
                    embed.set_image(url="attachment://image.png")
                    await ctx.edit(embed=embed, file=image_attachment)


    @imageManipulationSubCommands.command(name="rip", description="Place someones avatar on a grave.")
    @commands.check(is_blocked)
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def rip(self, ctx: discord.ApplicationContext, member: Option(discord.Member, "The member to use on the image.")):

        embed = await db.build_embed(ctx.guild, title="<a:Loading:1247220769511964673> Generating Image", description="The image is being generated...")
        await ctx.respond(embed=embed)

        user_1_av = member.display_avatar.url

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.aggelos-007.xyz/rip?avatar={user_1_av}") as response:
                if response.status == 200:
                    image_data = await response.read()
                    image_file = io.BytesIO(image_data)
                    image_attachment = discord.File(image_file, filename="image.png")

                    embed = await db.build_embed(ctx.author.guild, title=f"")
                    embed.set_image(url="attachment://image.png")
                    await ctx.edit(embed=embed, file=image_attachment)

def setup(client):
    client.add_cog(images(client))