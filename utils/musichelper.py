import discord
import lavalink
from utils.lists import error_emoji, success_emoji

class RemoveSongButton(discord.ui.Button):
    def __init__(self):
        super().__init__(emoji="<:Remove:1180990477445648434>", label="Remove Song", style=discord.ButtonStyle.gray, row=2)

    async def callback(self, interaction: discord.Interaction):
        player = interaction.client.lavalink.player_manager.get(
            interaction.guild.id)
        queue = player.queue

        if len(queue) == 0:
            return await interaction.response.send_message(f"### {error_emoji} The queue is currently empty.", ephemeral=True)

        songlist = queue[:25]

        options = []

        for index, song in enumerate(songlist):
            options.append(discord.SelectOption(
                label=song.title, description=f"By {song.author}", value=str(index), emoji="<:Remove:1180990477445648434>"))

        view = discord.ui.View(timeout=None)
        view.add_item(SongRemove(options))
        view.add_item(SongRemoveFromLast())
        await interaction.response.send_message(view=view, ephemeral=True)


class SongRemove(discord.ui.Select):
    def __init__(self, options: list, reversed: bool = False):
        super().__init__(placeholder="Select a song to remove...")
        self.options = options
        self.reversed = reversed

    async def callback(self, interaction: discord.Interaction):
        index = int(self.values[0])

        player: lavalink.DefaultPlayer = interaction.client.lavalink.player_manager.get(
            interaction.guild.id)

        if self.reversed:
            index = -index

        try:
            item = player.queue.pop(index)
            await interaction.response.edit_message(content=f"### {success_emoji} Successfully Removed `{item.title}` from the queue.", view=None)

        except:
            await interaction.response.edit_message(content=f"### {error_emoji} Something went wrong, please try again.", view=None)


class SongRemoveFromLast(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Newest ➭ Oldest", emoji="<:Repeat:1176355301490950256>")

    async def callback(self, interaction: discord.Interaction):
        player = interaction.client.lavalink.player_manager.get(
            interaction.guild.id)
        queue = player.queue.copy()

        if len(queue) == 0:
            return await interaction.response.send_message(f"### {error_emoji} The queue is currently empty.", ephemeral=True)

        queue.reverse()
        songlist = queue[:25]

        options = []

        for index, song in enumerate(songlist):
            options.append(discord.SelectOption(
                label=song.title, description=f"By {song.author}", value=str(index), emoji="<:Remove:1180990477445648434>"))

        view = discord.ui.View(timeout=None)
        view.add_item(SongRemove(options, True))
        await interaction.response.edit_message(content=f"### <a:Folder:1209072590719553556> Newest ➭ Oldest", view=view)