import math
from time import sleep
from discord.utils import get
from discord.ext import commands
import youtube_dl
from discord.utils import get
import threading
import discord
import random
import sys

TOKEN = '' #your discord token
bot = commands.Bot(command_prefix='-')
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}
Q = {}

@bot.event
async def on_ready():
    print('DogBot is launching...')
    print('Loading guilds:')
    for guild in bot.guilds:
        Q[guild.id] = Queue(guild.id)
        print('\t' + guild.name)
    print('DogBot has started!')

class Song:
    def __init__(self, url:str, playlist:bool, id):
        quiet = True
        self.playlist = playlist
        self.url = url
        self.URL = []
        self.title = []
        if self.playlist:
            info = youtube_dl.YoutubeDL({
                    'format': 'bestaudio',
                    'playlist_items': '1',
                    'quiet': quiet
                }).extract_info(self.url, download=False)['entries'][0]
            Q[id].push([[info['formats'][0]['url'], info['title']]])
            print('downloading playlist..')
            info = youtube_dl.YoutubeDL({
                'format': 'bestaudio',
                'playliststart': 2,
                'quiet': quiet
            }).extract_info(self.url, download=False)['entries']
            print('done')
            for inf in info:
                self.URL.append(inf['formats'][0]['url'])
                self.title.append(inf['title'])
        else:
            info = youtube_dl.YoutubeDL({
                    'default_search': 'auto',
                    'format': 'bestaudio',
                    'quiet': quiet
                }).extract_info(self.url, download=False)
            self.URL.append(info['formats'][0]['url'])
            self.title.append(info['title'])
        self.info = [list(a) for a in zip(self.URL, self.title)]

class Queue:
    def __init__(self, id):
        self.vc = get(bot.voice_clients, guild=bot.get_guild(id))
        self.kill_thread = False
        self.id = id
        self.arr = []
        self.size = 0
        self.will_play = False
        self.skip_next_callback = False
        self.T = threading.Thread(target=player, args=(id,))

    def push(self, info):
        for inf in info:
            self.arr.append(inf)
            self.size+=1
            if self.size == 1: self.play_current()

    def pop(self):
        if self.size > 0:
            del self.arr[0]
            self.size-=1
            if self.size == 0: self.kill_thread = True

    def front(self):
        return self.arr[0]
    
    def back(self):
        return self.arr[-1]
    
    def clear(self):
        self.kill_thread = True
        self.arr = []
        self.size = 0

    def play_current(self):
        self.skip_next_callback = False
        vc = get(bot.voice_clients, guild=bot.get_guild(self.id))
        if self.size > 0:
            vc.play(discord.FFmpegPCMAudio(self.front()[0], **FFMPEG_OPTIONS))
            if not self.T.is_alive():
                self.T = threading.Thread(target=player, args=(self.id,))
                self.T.start()

    def play_next(self):
        if self.size > 0:
            self.pop()
            self.play_current()
        else:
            self.kill_thread = True

def player(id):
    vc = get(bot.voice_clients, guild=bot.get_guild(id))
    while True:
        if Q[id].kill_thread:
            Q[id].kill_thread = False
            sys.exit()
        if vc.is_playing():
            sleep(1)
        elif Q[id].skip_next_callback:
            pass
        else:
            Q[id].play_next()

@bot.command(name="clean")
async def clear(ctx, amount=5):
	await ctx.channel.purge(limit=amount)                

@bot.command(name="sqrt")
async def sqrt(ctx, num):
	await ctx.send(str(math.sqrt(int(num))))              

@bot.command(name="play", aliases=["p", "ğ"])
async def play(ctx, url):
    try:
        user_channel = ctx.author.voice.channel
        if not user_channel:
            return await ctx.send('Gel şöyle boş bi odaya geçelim.')
        if ctx.voice_client and (ctx.voice_client.channel != user_channel):
            return await ctx.send('Başka biriyleyim!')
        if user_channel and not ctx.voice_client:
            await ctx.send('DogBot geliyor!')
            await user_channel.connect()
        song = Song(url, 'list=' in url, ctx.guild.id)
        Q[ctx.guild.id].push(song.info)
    except:
        return

@bot.command(name="join", aliases=["j"]) 
async def join(ctx):
    channel = ctx.author.voice.channel
    if channel:
        if not ctx.voice_client:
            await ctx.send('DogBot geliyor!')
            await channel.connect()
    else:
        await ctx.send('Boşa deniyorsun.')

@bot.command(name="leave", aliases=["l"])
async def leave(ctx):
    try:
        if ctx.author.voice.channel == ctx.voice_client.channel:
            Q[ctx.guild.id].clear()
            await ctx.send('C')
            await ctx.send('Y')
            await ctx.send('@')
            await ctx.voice_client.disconnect()
    except:
        return

@bot.command(name="stop")
async def stop(ctx):
    server = ctx.message.guild
    try:
        if ctx.author.voice.channel == server.voice_client.channel:
            Q[ctx.guild.id].skip_next_callback = True
            Q[ctx.guild.id].kill_thread = True
            server.voice_client.stop()
    except:
        return

@bot.command(name="clear", aliases=["reset"])
async def clear(ctx):
    server = ctx.message.guild
    try:
        if ctx.author.voice.channel == server.voice_client.channel:
            Q[ctx.guild.id].clear()
            server.voice_client.stop()
    except:
        return


@bot.command(name="skip", aliases=["s"])
async def skip(ctx):
    server = ctx.message.guild
    try:
        if ctx.author.voice.channel == server.voice_client.channel:
            server.voice_client.stop()
    except:
        return

@bot.command(name="pause")
async def pause(ctx):
    server = ctx.message.guild
    try:
        server = ctx.message.guild
        if ctx.author.voice.channel == server.voice_client.channel:
            Q[ctx.guild.id].skip_next_callback = True
            server.voice_client.pause()
    except:
        return

@bot.command(name="resume", aliases=["res"])
async def resume(ctx):
    server = ctx.message.guild
    try:
        if ctx.author.voice.channel == server.voice_client.channel:
            Q[ctx.guild.id].skip_next_callback = False
            server.voice_client.resume()
    except:
        return

@bot.command(name="queue", aliases=["q"])
async def queue(ctx):
    guild_q = '\n'.join([str(i+1) + '-) ' + Q[ctx.guild.id].arr[i][1] for i in range(len(Q[ctx.guild.id].arr))])
    if guild_q != '':
        await ctx.send('```' + guild_q + '```')
    else:
        await ctx.send('```---There are no songs in queue.---```')
    return

@bot.command(name="volume", aliases=["vol", "v"])
async def volume(ctx):
    await ctx.send("volume komutu yapım aşamasında")

bot.run(TOKEN)
