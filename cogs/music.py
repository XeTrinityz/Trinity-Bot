# Discord Imports
from discord.ext import commands
from discord import Option
import discord

# Standard / Third-Party Library Imports
from spotipy import SpotifyClientCredentials
from typing import Union
import lavalink
import datetime
import spotipy
import asyncio
import time
import re

# Local Module Imports
from utils.database import Database
from utils.musichelper import RemoveSongButton
from Bot import is_blocked
from utils.lists import *
db = Database()

RURL = re.compile(r'https?://(?:www\.)?.+')
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id="4e59b0972e8c4516b510bca810141eae", client_secret="cab59863bd8e47abb4717dd82bf76c92"))

class SongSelectView(discord.ui.View):
    def __init__(self, select):
        super().__init__(timeout=30)
        self.add_item(select)
        self.select = select

    async def on_timeout(self):
        if not self.select.success:
            try:
                await self.message.edit(content=f"{error_emoji} Request Timed Out", view=None, delete_after=20)
            except:
                pass

async def create_embed(guild: discord.Guild, track: lavalink.AudioTrack, position: int):
    pos = datetime.timedelta(seconds=position / 1000)
    
    requester: discord.Member = guild.get_member(track.requester)
    embed = await db.build_embed(guild, f"<a:Music:1166148239641296986> Now Playing", description=f"[**{track.title}**]({track.uri}) by {track.author}")

    if track.duration:
        dur = datetime.timedelta(seconds=int(track.duration / 1000))
        duration = dur - pos
        en = datetime.datetime.utcnow() + duration
        endsat = round(en.timestamp())
        embed.add_field(name="Ending", value=f"<t:{endsat}:R>", inline=True)

    embed.set_footer(
        text=f"Requested By {requester.display_name}", icon_url=requester.display_avatar.url)
    return embed


async def cleanup(player: lavalink.DefaultPlayer):
    player.queue = []
    await player.skip()


class Player(discord.VoiceClient):

    def __init__(self, client: discord.Client, channel: Union[discord.VoiceChannel, discord.StageChannel]):
        super().__init__(client, channel)
        self.client = client
        self.channel = channel
        if hasattr(self.client, 'lavalink'):
            self.lavalink = self.client.lavalink

    async def on_voice_server_update(self, data):
        lavalink_data = {'t': 'VOICE_SERVER_UPDATE', 'd': data}
        await self.lavalink.voice_update_handler(lavalink_data)

    async def on_voice_state_update(self, data):
        lavalink_data = {'t': 'VOICE_STATE_UPDATE', 'd': data}
        await self.lavalink.voice_update_handler(lavalink_data)

    async def connect(self, *, timeout: float, reconnect: bool, self_deaf: bool = False, self_mute: bool = False) -> None:
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=self.channel, self_mute=self_mute, self_deaf=self_deaf)

    async def disconnect(self, *, force: bool = False) -> None:
        player = self.lavalink.player_manager.get(self.channel.guild.id)
        
        if not force and not player.is_connected:
            return
        
        await self.channel.guild.change_voice_state(channel=None)
        player.channel_id = None
        self.cleanup()


class SongSelect(discord.ui.Select):
    def __init__(self, client, tracks, requester):
        self.client = client
        self.tracks = tracks
        self.requester = requester
        self.keys = {}
        self.success = False

        options = []
        for track in self.tracks:
            options.append(discord.SelectOption(label=f"{track.title}", description=f"By {track.author}", emoji="<:MusicNotes:1166162229893283952>", value=track.identifier))
            self.keys[f'{track.identifier}'] = track

        super().__init__(placeholder="Select a song...", min_values=1, max_values=5, options=options, select_type=discord.ComponentType.string_select)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.requester:
            return await interaction.response.send_message("Invalid user!", ephemeral=True)
        selection = self.values
        titles = []
        for track in selection:
            song = self.keys[f"{track}"]
            info = song["info"]
            titles.append(info["title"])

        titlesn = ", ".join(titles)
        player: lavalink.DefaultPlayer = self.client.lavalink.player_manager.get(interaction.guild.id)

        for track in selection:
            song = self.keys[f"{track}"]
            player.add(track=song, requester=self.requester.id)

        if not player.is_playing:
            await player.play()

        if len(self.client.active_players) == 0:
            bview = Buttons(self.client, interaction)
            embed = await create_embed(guild=interaction.guild, track=player.current, position=player.position)
            await interaction.response.edit_message(embed=embed, view=bview)
            message = await interaction.original_response()
            
            bview.message = message
            self.client.active_players.append(message.id)

            await interaction.followup.send(f"### {success_emoji} {titlesn} has been added to the queue.", ephemeral=True)
            self.success = True

        else:
            await interaction.response.edit_message(content=f"### {success_emoji} {titlesn} has been added to the queue.", view=None)
            await interaction.channel.send(content=f"### {success_emoji} {interaction.user.mention} ➭ Added ➭ {titlesn}", delete_after=60, allowed_mentions=discord.AllowedMentions(users=False))
            self.success = True


class Queue(discord.ui.View):

    def __init__(self, client, queue, length):
        super().__init__()
        self.client = client
        self.queue = queue
        self.length = length
        self.position = 0
        self.max = len(queue[::10]) - 1

    async def build_queue(self, guild):
        page = 10 * self.position
        songlist = []
        count = 1
        for song in self.queue[page:page + 10]:
            songlist.append(f"**{count + page}.** `{song}`")
            count += 1
        embed = await db.build_embed(guild, "<a:Folder:1247220756547502160> Coming Up", description=f"\n".join(songlist))
        embed.set_footer(text=f"Total ➭ {len(self.queue)} | Time ➭ {self.length}")
        return embed

    @discord.ui.button(label="", emoji="<a:LeftArrow:1156039371624026112>", style=discord.ButtonStyle.grey)
    async def queue_prev(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.position -= 1
        if self.position == 0:
            button.disabled = True
        if self.children[1].disabled:
            self.children[1].disabled = False
        embed = await self.build_queue(interaction.guild)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="", emoji="<a:RightArrow:1156039369875001385>", style=discord.ButtonStyle.grey)
    async def queue_next(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.position += 1
        if self.position == self.max:
            button.disabled = True
        if self.children[0].disabled:
            self.children[0].disabled = False
        embed = await self.build_queue(interaction.guild)
        await interaction.response.edit_message(embed=embed, view=self)


class Buttons(discord.ui.View):

    def __init__(self, client, interaction):
        super().__init__(timeout=None)
        self.client = client
        self.looped = False
        self.check_buttons(interaction)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if (
            not interaction.user.voice
            or not interaction.guild.me.voice
            or not interaction.user.voice.channel
            or not interaction.guild.me.voice.channel):
            return
        return True

    async def on_timeout(self) -> None:
        try:
            self.disable_all_items()
            # message = self.client.get_message(self.message)
            message = self.client.get_message(self.message.id)
            embed = message.embeds[0]
            embed.set_author(name="This player has timed out.")
            await self.message.edit(embed=embed, view=self)
            self.client.active_players.remove(self.message.id)
        except:
            pass

    def controller(self, interaction):
        player = self.client.lavalink.player_manager.get(interaction.guild.id)
        return player

    def check_buttons(self, interaction):
        player = self.client.lavalink.player_manager.get(interaction.guild.id)
        if player.paused:
            self.children[1].disabled = True
        else:
            self.children[0].disabled = True

    @staticmethod
    def compilequeue(queue):
        titles = []
        lengths = []
        for song in queue:
            titles.append(song.title)
            lengths.append(int(song.duration / 1000))
        return titles, lengths

    @discord.ui.button(emoji="<:play:1176355295056887889>", label="Play", style=discord.ButtonStyle.gray, row=1)
    async def button_play(self, button: discord.ui.Button, interaction: discord.Interaction):
        player = self.controller(interaction)
        embed = await create_embed(guild=interaction.guild,
                             track=player.current, position=player.position)
        if player.paused:
            await player.set_pause(pause=False)
            self.children[1].disabled = False
            button.disabled = True
            await interaction.response.edit_message(embed=embed, view=self)
            await interaction.followup.send(f"### {success_emoji} {interaction.user.mention} ➭ Song Resumed", delete_after=10.0, allowed_mentions=discord.AllowedMentions(users=False))

    @discord.ui.button(emoji="<:pause:1176355299658055770>", label="Pause", style=discord.ButtonStyle.gray, row=1)
    async def button_pause(self, button: discord.ui.Button, interaction: discord.Interaction):
        player = self.controller(interaction)
        embed = await create_embed(guild=interaction.guild,
                             track=player.current, position=player.position)
        if not player.paused:
            await player.set_pause(pause=True)
            self.children[0].disabled = False
            button.disabled = True
            await interaction.response.edit_message(embed=embed, view=self)
            await interaction.followup.send(f"### {success_emoji} {interaction.user.mention} ➭ Song Paused", delete_after=10.0, allowed_mentions=discord.AllowedMentions(users=False))

    @discord.ui.button(emoji="<:skip:1176355298424918127>", label="Skip", style=discord.ButtonStyle.gray, row=1)
    async def button_forward(self, button: discord.ui.Button, interaction: discord.Interaction):
        player = self.controller(interaction)
        await player.skip()
        embed = await create_embed(guild=interaction.guild,
                             track=player.current, position=player.position)
        await interaction.response.edit_message(embed=embed, view=self)
        await interaction.followup.send(f"### {success_emoji} {interaction.user.mention} ➭ Song Skipped",
                                        delete_after=10.0, allowed_mentions=discord.AllowedMentions(users=False))

    @discord.ui.button(emoji="<:Stop:1166167950005383218>", label="Stop", style=discord.ButtonStyle.gray, row=1)
    async def button_stop(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(f"### {error_emoji} You are not allowed to stop the player.", ephemeral=True)
            return

        player = self.controller(interaction)
        await interaction.response.send_message(f"### {success_emoji} {interaction.user.mention} ➭ Player Stopped", allowed_mentions=discord.AllowedMentions(users=False))
        await cleanup(player)

    @discord.ui.button(emoji="<:shuffle:1176355296290029608>", label="Shuffle", style=discord.ButtonStyle.gray, row=2)
    async def button_shuffle(self, button: discord.ui.Button, interaction: discord.Interaction):
        player = self.controller(interaction)
        embed = await create_embed(guild=interaction.guild,
                             track=player.current, position=player.position)
        await interaction.response.edit_message(embed=embed, view=self)
        if not player.shuffle:
            player.set_shuffle(shuffle=True)
            await interaction.followup.send(f"### {success_emoji} {interaction.user.mention} ➭ Queue Shuffle ➭ Enabled", delete_after=10.0)
        else:
            player.set_shuffle(shuffle=False)
            await interaction.followup.send(f"### {success_emoji} {interaction.user.mention} ➭ Queue Shuffle ➭ Disabled", delete_after=10.0)

    @discord.ui.button(emoji="<:repeat:1176355301490950256>", label="Repeat", style=discord.ButtonStyle.gray, row=2)
    async def button_loop(self, button: discord.ui.Button, interaction: discord.Interaction):
        player = self.controller(interaction)
        embed = await create_embed(guild=interaction.guild, track=player.current, position=player.position)
        await interaction.response.edit_message(embed=embed, view=self)

        if not self.looped:
            player.set_loop(2)
            await interaction.channel.send(f"### {success_emoji} {interaction.user.mention} ➭ Queue Loop ➭ Enabled", delete_after=10.0)
            self.looped = True
        else:
            player.set_loop(0)
            await interaction.channel.send(f"### {success_emoji} {interaction.user.mention} ➭ Queue Loop ➭ Disabled", delete_after=10.0)
            self.looped = False

    @discord.ui.button(emoji="<:queue:1176355758007390208>", label="Queue", style=discord.ButtonStyle.gray, row=2)
    async def button_queue(self, button: discord.ui.Button, interaction: discord.Interaction):
        player = self.controller(interaction)
        queue, length = self.compilequeue(player.queue)
        songlist = []
        for idx, song in enumerate(queue[:10]):
            songlist.append(f"**{idx + 1}.** `{song}`")
        totallength = time.strftime('%H Hours, %M Minutes, %S Seconds', time.gmtime(sum(length)))
        embed = await db.build_embed(interaction.guild, "Current Queue", description=f"\n".join(songlist))
        embed.set_footer(text=f"Total ➭ {len(queue)} | Total Time ➭ {totallength}")
        view = Queue(self.client, queue, totallength)
        view.add_item(RemoveSongButton())

        ex = view.children[1:] if len(queue) > 10 else view.children[2:]

        view.disable_all_items(exclusions=ex)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(emoji="<:VolDown:1166535125304098816>", label="", style=discord.ButtonStyle.grey, row=3)
    async def button_volume_down(self, button: discord.ui.Button, interaction: discord.Interaction):
        player = self.controller(interaction)
        await player.set_volume(player.volume + -5)
        await interaction.response.send_message(f"### {success_emoji} {interaction.user.mention} ➭ Current Volume ➭ {player.volume}", delete_after=5.0)

    @discord.ui.button(emoji="<:VolUp:1166535123173392384>", label="", style=discord.ButtonStyle.grey, row=3)
    async def button_volume_up(self, button: discord.ui.Button, interaction: discord.Interaction):
        player = self.controller(interaction)
        await player.set_volume(player.volume + 5)
        await interaction.response.send_message(f"### {success_emoji} {interaction.user.mention} ➭ Current Volume ➭ {player.volume}", delete_after=5.0)


class Music(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.client.guild_nodes = {}
        self.client.active_players = []
        client.loop.create_task(self.connect_nodes())

    musicSubCommands = discord.SlashCommandGroup("music", "Play.")

    async def connect_nodes(self):
        await self.client.wait_until_ready()
        if not hasattr(self, "lavalink"):
            lavaclient = lavalink.Client(self.client.user.id)
            lavaclient.add_node('78.108.218.88', 25565, 'mysparkedserver', 'us', 'music-node-1')
            lavaclient.add_event_hooks(self)
            self.client.lavalink = lavaclient


    def cog_unload(self):
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.client.lavalink._event_hooks.clear()
    
    @lavalink.listener(lavalink.events.QueueEndEvent)
    async def queue_ending(self, event: lavalink.QueueEndEvent):
        try:
            players = self.client.active_players
            for player in players:
                message: discord.Message = self.client.get_message(player)
                embed = message.embeds[0]
                embed.title = "<a:Mute:1153887708196913304> Queue Ended"
                embed.description = "There are no more songs in the queue. Leaving voice channel."
                embed.fields[0].name = "Ended"
                embed.fields[0].value = f"<t:{round(time.time())}:R>"
                await message.edit(embed=embed)

            player: lavalink.DefaultPlayer = event.player
            if not player.is_playing:
                guild: discord.Guild = self.client.get_guild(int(event.player.guild_id))
                voice = guild.voice_client
                
                if voice:
                    await voice.disconnect(force=True)
                    
                self.client.active_players = []

                for player in players:
                    message: discord.Message = self.client.get_message(player)
                    view = discord.ui.View.from_message(message)
                    view.disable_all_items()
                    await message.edit(view=view)
        except:
            pass


    @lavalink.listener(lavalink.events.TrackStartEvent)
    async def track_started(self, event: lavalink.TrackStartEvent):
        players = self.client.active_players
        
        try:
            for player in players:
                message: discord.Message = self.client.get_message(player)
                if int(event.player.guild_id) == message.guild.id:
                    await message.edit(embed=await create_embed(guild=message.guild, track=event.track, position=event.track.position))
                    await message.channel.send(content=f"### {success_emoji} Now Playing ➭ **{event.track.title}** by {event.track.author}", delete_after=60)
        except:
            pass


    @lavalink.listener(lavalink.events.TrackStuckEvent)
    async def track_stuck(self, event: lavalink.TrackStuckEvent):
        await event.player.skip()


    @staticmethod
    def is_privileged(user: discord.Member, track: lavalink.AudioTrack):
        return True


    @staticmethod
    def get_spotify_tracks(query):
        songlist = []
        
        match_result = re.findall(r'/track/|/album/|/playlist/', query)
        
        if match_result:
            match_type = match_result[0]

            if match_type == '/track/':
                track = sp.track(query)
                songlist.append(f"{track['album']['artists'][0]['name']} - {track['name']}")
            elif match_type == '/album/':
                tracks = sp.album(query)
                for track in tracks['tracks']['items']:
                    songlist.append(f"{track['artists'][0]['name']} - {track['name']}")
            elif match_type == '/playlist/':
                tracks = sp.playlist(query)
                for track in tracks['tracks']['items']:
                    actualtrack = track['track'] 
                    songlist.append(f"{actualtrack['album']['artists'][0]['name']} - {actualtrack['name']}")
            else:
                pass
        
        return songlist


    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if hasattr(self, "lavalink"):
            voice = discord.utils.get(self.client.voice_clients, guild=member.guild)
            player = self.client.lavalink.player_manager.get(member.guild.id)
            if not voice:
                if player:
                    await cleanup(player)
                return
            elif voice.channel != before.channel:
                return
            elif member.bot:
                return
            if after.channel != before.channel:
                memberlist = []
                for m in before.channel.members:
                    if m.bot:
                        continue
                    memberlist.append(m)
                if not memberlist:
                    if player.is_playing:
                        await cleanup(player)
                    if voice:
                        await voice.disconnect(force=True)
                    self.client.active_players = []


    @musicSubCommands.command(name="play", description="Play music from your favourite streaming services.")
    @commands.check(is_blocked)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def music(self, ctx: discord.ApplicationContext, search: Option(str, description="Song, Artist, Spotify Link.", max_length=256, required=False)):

        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.respond(f"### {error_emoji} You need to be in a voice channel first.", ephemeral=True)
        
        player = self.client.lavalink.player_manager.create(ctx.guild.id)

        try:
            player.store('channel', ctx.channel.id)
            await channel.connect(cls=Player)
            await ctx.guild.change_voice_state(channel=channel, self_deaf=True)
        except discord.ClientException:
            await ctx.guild.voice_client.move_to(channel)

        if search:
            if player.is_playing:
                if len(player.queue) >= 250:
                    return await ctx.respond(f"### {error_emoji} The queue is currently full.", ephemeral=True)
                
            search = f'ytsearch:{search}' if not RURL.match(search) else search
            results = await player.node.get_tracks(search)
            tracks = results.tracks
            total = len(player.queue)
            match results.load_type:
                case lavalink.LoadType.PLAYLIST:
                    await ctx.defer()
                    count = 0
                    for track in tracks:
                        if total + count < 250:
                            player.add(track=track, requester=ctx.author.id)
                            count += 1

                    if len(self.client.active_players) == 0:
                        await ctx.interaction.followup.send(f"### Added **{count}** songs to the queue.")
                        bview = Buttons(self.client, ctx.interaction)
                        embed = await create_embed(
                            guild=ctx.guild, track=player.current, position=player.position)
                        mplayer = await ctx.interaction.followup.send(embed=embed, view=bview)
                        bview.message = mplayer
                        self.client.active_players.append(mplayer.id)

                    else:
                        await ctx.respond(content=f"### Added **{count}** songs to the queue.", delete_after=30)

                    if not player.is_playing:
                        await player.play()
                case lavalink.LoadType.TRACK:
                    song = tracks[0]
                    if len(self.client.active_players) == 0:
                        await ctx.respond(content=f"### Adding {song.title} to the queue.")
                        bview = Buttons(self.client, ctx.interaction)
                        embed = await create_embed(
                            guild=ctx.guild, track=player.current, position=player.position)
                        mplayer = await ctx.interaction.followup.send(embed=embed, view=bview)
                        bview.message = mplayer
                        self.client.active_players.append(mplayer.id)
                    else:
                        await ctx.respond(content=f"### Adding {song.title} to the queue.", delete_after=30)

                    player.add(track=song, requester=ctx.author.id)
                    if not player.is_playing:
                        await player.play()
                case lavalink.LoadType.SEARCH:
                    view = SongSelectView(SongSelect(
                        self.client, tracks[:5], ctx.author))

                    if len(self.client.active_players) == 0:
                        await ctx.respond(view=view)

                    else:
                        await ctx.respond(view=view, ephemeral=True)

                case _:
                    if 'open.spotify.com' or 'spotify:' in search:
                        if len(self.client.active_players) == 0:
                            await ctx.defer()
                        else:
                            await ctx.defer(ephemeral=True)

                        spotifysongs = self.get_spotify_tracks(query=search)
                        if not spotifysongs:
                            return await ctx.respond(f"### {error_emoji} I could not find the provided song.", ephemeral=True)
                        
                        s_results = await asyncio.wait_for(asyncio.gather(*[player.node.get_tracks(f'ytsearch:{song}') for song in spotifysongs]), timeout=30)
                        count = 0

                        for track in s_results:
                            if total + count < 250:
                                player.add(track=track.tracks[0], requester=ctx.author.id)
                                count += 1

                        if len(self.client.active_players) == 0:
                            await ctx.respond(content=f"Added {count} spotify song(s) to the queue")
                            bview = Buttons(self.client, ctx.interaction)
                            embed = await create_embed(guild=ctx.guild, track=player.current, position=player.position)
                            mplayer = await ctx.interaction.followup.send(embed=embed, view=bview)
                            bview.message = mplayer
                            self.client.active_players.append(mplayer.id)

                        else:
                            await ctx.respond(content=f"Added {count} spotify song(s) to the queue.", delete_after=30)

                            if not player.is_playing:
                                await player.play()
                    else:
                        return await ctx.respond(f"### {error_emoji} I could not find the provided song.", ephemeral=True)
        else:
            if not player.is_playing:
                return await ctx.respond(f"### {error_emoji} There is no music currently playing.", ephemeral=True)
            
            bview = Buttons(self.client, ctx.interaction)
            embed = await create_embed(guild=ctx.guild, track=player.current, position=player.position)
            mplayer = await ctx.respond(embed=embed, view=bview, ephemeral=True)
            bview.message = await mplayer.original_response()

def setup(bot):
    bot.add_cog(Music(bot))