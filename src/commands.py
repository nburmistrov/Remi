import itertools

from yandex_music import Client
from discord.ext.commands import Bot, Cog, command, before_invoke, after_invoke

from .extended.checks import *
from .music.audio import YandexAudioSource
from .music.player import YandexAudioPlayer, YandexAudioPlayerPool


class BotCommands(Cog):
    def __init__(self, bot: Bot, yandex_client: Client = None):
        self.bot = bot

        if yandex_client is None:
            yandex_client = Client()

        self.yandex_client = yandex_client
        self.players = YandexAudioPlayerPool()

    @command(aliases=['j'])
    @author_in_any_channel()
    async def join(self, ctx, *args):
        voice_channel = ctx.author.voice.channel

        if not ctx.voice_client:
            voice_client = await voice_channel.connect()
        else:
            await ctx.voice_client.move_to(voice_channel)

        await ctx.send(f'Successfully connected to {voice_channel}')

    @command(aliases=['l', 'exit'])
    @check_all(author_in_any_channel(),
               bot_in_any_channel(),
               in_same_channel())
    async def leave(self, ctx, *args):
        voice_channel = ctx.author.voice.channel

        await ctx.voice_client.disconnect()
        await ctx.send(f'Successfully disconnected from {voice_channel}')

    @command()
    @check_all(author_in_any_channel(),
               bot_in_any_channel(),
               in_same_channel())
    async def volume(self, ctx, volume: float = None, *args):
        player = self.players.find(ctx.voice_client) \
            or self.players.register(ctx.voice_client)

        if volume is None:
            return await ctx.send(f'The volume is {player.volume}%')

        player.volume = volume

        await ctx.send(f'Changed the volume to {volume}%')

    @command(aliases=['p'])
    @before_invoke(join.callback)
    @check_all(author_in_any_channel(),
               bot_in_another_channel())
    async def play(self, ctx, *query):
        player = self.players.find(ctx.voice_client) \
            or self.players.register(ctx.voice_client)

        search_str = ' '.join(query)
        search_result = self.yandex_client.search(search_str, type_='track')
        track = search_result.tracks.results[0]
        audio = YandexAudioSource(track)
        player.play(audio)

        await ctx.send(f'{audio.full_title} is playing now')

    @command()
    @before_invoke(join.callback)
    @check_all(author_in_any_channel(),
               bot_in_another_channel())
    async def playlist(self, ctx, profile: str, kind: int = 3, *args):
        player = self.players.find(ctx.voice_client) \
            or self.players.register(ctx.voice_client)

        playlist = self.yandex_client.users_playlists_list(
            profile)[0]

        short_tracks = self.yandex_client.users_playlists(
            kind, playlist.uid)[0].tracks

        tracks_id = [st.track_id for st in short_tracks]
        tracks = self.yandex_client.tracks(tracks_id)
        audio = [YandexAudioSource(t) for t in tracks]
        player.playlist(audio)

        await ctx.send(
            f'{len(tracks)} tracks added to the queue\n{audio[0].full_title} is playing now')

    @command()
    @check_all(author_in_any_channel(),
               bot_in_any_channel(),
               in_same_channel())
    async def pause(self, ctx, *args):
        player = self.players.find(ctx.voice_client) \
            or self.players.register(ctx.voice_client)
        player.pause()

        await ctx.send('Paused')

    @command(aliases=['r'])
    @check_all(author_in_any_channel(),
               bot_in_any_channel(),
               in_same_channel())
    async def resume(self, ctx, *args):
        player = self.players.find(ctx.voice_client) \
            or self.players.register(ctx.voice_client)
        player.resume()

        await ctx.send('Resumed')

    @command()
    @check_all(author_in_any_channel(),
               bot_in_any_channel(),
               in_same_channel())
    async def stop(self, ctx, *args):
        player = self.players.find(ctx.voice_client) \
            or self.players.register(ctx.voice_client)
        player.stop()

        await ctx.send('Stopped')

    @command(aliases=['n', 'next'])
    @check_all(author_in_any_channel(),
               bot_in_any_channel(),
               in_same_channel())
    async def skip(self, ctx, *args):
        player = self.players.find(ctx.voice_client) \
            or self.players.register(ctx.voice_client)
        player.skip()

        await ctx.send('Next track')

    @command(aliases=['mix'])
    @check_all(author_in_any_channel(),
               bot_in_any_channel(),
               in_same_channel())
    async def shuffle(self, ctx, *args):
        player = self.players.find(ctx.voice_client) \
            or self.players.register(ctx.voice_client)
        player.shuffle()

        queue, iter = player.queue(10), itertools.count(1)
        titles = '\n'.join(f'{next(iter)}. {i.full_title}' for i in queue)

        await ctx.send(
            'Tracks are mixed, here are the next 10 tracks:\n'+titles)

    @command()
    @check_all(author_in_any_channel(),
               bot_in_any_channel(),
               in_same_channel())
    async def queue(self, ctx, amount: int = 10, *args):
        player = self.players.find(ctx.voice_client) \
            or self.players.register(ctx.voice_client)

        queue, iter = player.queue(amount), itertools.count(1)

        if not queue:
            await ctx.send('The queue is empty')

        titles = '\n'.join(f'{next(iter)}. {i.full_title}' for i in queue)

        await ctx.send(f'Next {len(queue)} tracks:\n'+titles)

    @command(aliases=['c', 'clr'])
    @check_all(author_in_any_channel(),
               bot_in_any_channel(),
               in_same_channel())
    async def clear(self, ctx, *args):
        player = self.players.find(ctx.voice_client) \
            or self.players.register(ctx.voice_client)
        player.clear()

        await ctx.send('The queue cleared')
