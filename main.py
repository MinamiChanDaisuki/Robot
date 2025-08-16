import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import datetime
import feedparser
import os
import json
import time

try:
    from myserver import server_on
except ImportError:
    def server_on():
        pass

LATEST_VIDEO_FILE = "latest_video_id.txt"
SENT_VIDEOS_FILE = "sent_videos.json"
BANNER_URL = 'https://i.ibb.co/Wvbbk0bx/Xecret-banner-1.png'
TARGET_BOT_ID = 1296471355994144891
ALLOWED_CHANNEL_IDS = [1380891908376760401, 1381039725791674490]
PROTECTED_USER_IDS = {1300017174886350899, 1209783415759704085}
PING_RELAY_COOLDOWN = 60

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)
_last_relay = {}

def _load_text(path):
    return open(path, "r").read().strip() if os.path.exists(path) else None

def _save_text(path, data):
    with open(path, "w") as f:
        f.write(data)

def load_sent_videos():
    if os.path.exists(SENT_VIDEOS_FILE):
        with open(SENT_VIDEOS_FILE, "r") as f:
            return json.load(f)
    return {"UC5abJGhz74y-cw88wFqX0Jw": [], "UCoLxgTtHYNA8AjOJB1rU-2g": []}

def save_sent_videos(sent_videos):
    with open(SENT_VIDEOS_FILE, "w") as f:
        json.dump(sent_videos, f)

def is_video_already_sent(channel_id, video_id, sent_videos):
    return video_id in sent_videos.get(channel_id, [])

def add_sent_video(channel_id, video_id, sent_videos):
    if channel_id not in sent_videos:
        sent_videos[channel_id] = []
    if video_id not in sent_videos[channel_id]:
        sent_videos[channel_id].append(video_id)
        if len(sent_videos[channel_id]) > 50:
            sent_videos[channel_id] = sent_videos[channel_id][-50:]

async def _relay_protected_pings(channel, author, ids):
    now = time.time()
    to_ping = []
    for uid in ids:
        last = _last_relay.get(uid, 0)
        if now - last >= PING_RELAY_COOLDOWN:
            to_ping.append(uid)
            _last_relay[uid] = now
    if not to_ping:
        try:
            warn = await channel.send(f"{author.mention} Ping relay is on cooldown.")
            await asyncio.sleep(5)
            await warn.delete()
        except:
            pass
        return
    mentions = " ".join(f"<@{uid}>" for uid in to_ping)
    try:
        await channel.send(f"{mentions} — requested by {author.mention}")
    except:
        pass

async def youtube_feed_check_loop():
    latest_video_id = _load_text(LATEST_VIDEO_FILE)
    sent_videos = load_sent_videos()
    await bot.wait_until_ready()
    channel = bot.get_channel(1328406450489393253)
    feed_data = [
        {'url': os.getenv('Xecret_Hub_Englsih_Channel'), 'id': 'UC5abJGhz74y-cw88wFqX0Jw'},
        {'url': os.getenv('Xecret_Hub_Thailand_Channel'), 'id': 'UCoLxgTtHYNA8AjOJB1rU-2g'}
    ]
    while not bot.is_closed():
        try:
            for feed_info in feed_data:
                feed = feedparser.parse(feed_info['url'])
                channel_id = feed_info['id']
                if not feed.entries:
                    continue
                latest_entry = feed.entries[0]
                try:
                    video_id = latest_entry.yt_videoid
                except AttributeError:
                    link = getattr(latest_entry, "link", "")
                    if "youtube.com/watch?v=" in link:
                        video_id = link.split("v=")[1].split("&")[0]
                    elif "youtu.be/" in link:
                        video_id = link.split("youtu.be/")[1].split("?")[0]
                    else:
                        video_id = None
                if video_id and not is_video_already_sent(channel_id, video_id, sent_videos):
                    video_title = latest_entry.title
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                    video_description = getattr(latest_entry, 'summary', 'No description available')
                    if channel:
                        embed = discord.Embed(title=video_title, url=video_url, description=video_description, color=0xFFA500)
                        embed.set_image(url=thumbnail_url)
                        try:
                            await channel.send(content="<@&1383766143939903528>", embed=embed)
                        except:
                            pass
                    add_sent_video(channel_id, video_id, sent_videos)
                    save_sent_videos(sent_videos)
        except:
            pass
        await asyncio.sleep(60)

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    await bot.change_presence(status=discord.Status.dnd, activity=discord.Activity(type=discord.ActivityType.watching, name="https://xecrethub.com"))
    bot.loop.create_task(youtube_feed_check_loop())
    channel = bot.get_channel(1381039725791674490)
    try:
        guild = discord.Object(id=1328392700294070313)
        await bot.tree.sync(guild=guild)
    except:
        pass
    try:
        if channel:
            messages = [m async for m in channel.history(limit=20)]
            already = any(m.author == bot.user and m.embeds and m.embeds[0].title == "How to use the question?" for m in messages)
            if not already:
                embed = discord.Embed(title="How to use the question?", color=0xFFA500)
                embed.add_field(name="/question", value="Ask a question and get an automatic reply.\nExample: `/question how much`", inline=False)
                embed.set_footer(text=f"https://xecrethub.com | Sent at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                embed.set_image(url=BANNER_URL)
                await channel.send(embed=embed)
    except:
        pass

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.attachments or message.embeds:
        await bot.process_commands(message)
        return
    if any(d in message.content for d in ("https://tenor.com", "https://media.tenor.com", "https://giphy.com", "https://media.giphy.com")):
        await bot.process_commands(message)
        return
    if message.channel.id == 1381039725791674490:
        content = message.content.strip()
        if content.startswith('.') or content.startswith('/question'):
            await bot.process_commands(message)
            return
        if content.startswith('/'):
            try:
                await message.delete()
            except:
                pass
            return
        try:
            await message.delete()
        except:
            pass
        return
    if message.channel.id == 1380891908376760401:
        content = message.content.strip()
        if content.startswith('.'):
            await bot.process_commands(message)
            return
        if content.startswith('/'):
            return
        try:
            await message.delete()
        except:
            pass
        return
    if message.content.startswith('.') and message.channel.id not in ALLOWED_CHANNEL_IDS:
        command_name = message.content.split()[0].lower()
        basic_commands = ['.purchase', '.website', '.supported_games', '.supported_executors', '.terms', '.showcase']
        if command_name in basic_commands or message.content.startswith('.send'):
            await bot.process_commands(message)
            return
        else:
            return
    if message.mention_everyone or message.role_mentions:
        perms = getattr(message.author, "guild_permissions", None)
        if not (perms and perms.manage_messages):
            try:
                await message.delete()
            except:
                pass
            try:
                warn = await message.channel.send(f"{message.author.mention} Mass pings are not allowed.")
                await asyncio.sleep(5)
                await warn.delete()
            except:
                pass
            return
    mentioned_ids = {u.id for u in message.mentions} & PROTECTED_USER_IDS
    if mentioned_ids:
        perms = getattr(message.author, "guild_permissions", None)
        if not (perms and perms.manage_messages):
            try:
                await message.delete()
            except:
                pass
            await _relay_protected_pings(message.channel, message.author, mentioned_ids)
            return
    await bot.process_commands(message)

@bot.command()
async def send_buttons(ctx):
    embed = discord.Embed(title="Xecret Hub Control Panel", description="Select an option below to view information or perform an action.", color=0xFFA500)
    embed.set_image(url=BANNER_URL)
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(label="Visit Website", url="https://xecrethub.com"))
    view.add_item(discord.ui.Button(label="Supported Games", url="https://xecrethub.com/games"))
    view.add_item(discord.ui.Button(label="Supported Executors", url="https://xecrethub.com/executors"))
    view.add_item(discord.ui.Button(label="Purchase", url="https://xecrethub.com/purchase"))
    view.add_item(discord.ui.Button(label="Terms", url="https://xecrethub.com/terms"))
    await ctx.send(embed=embed, view=view)

@bot.command()
async def website(ctx):
    embed = discord.Embed(title="Visit our Website", description="Click the button below to visit our official website.", color=0xFFA500)
    embed.set_image(url=BANNER_URL)
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(label="xecrethub.com", url="https://xecrethub.com"))
    await ctx.send(embed=embed, view=view)

@bot.command()
async def supported_games(ctx):
    embed = discord.Embed(title="Supported Games", description="https://xecrethub.com/games", color=0xFFA500)
    embed.set_image(url=BANNER_URL)
    await ctx.send(embed=embed)

@bot.command()
async def supported_executors(ctx):
    embed = discord.Embed(title="Supported Executors", description="https://xecrethub.com/executors", color=0xFFA500)
    embed.set_image(url=BANNER_URL)
    await ctx.send(embed=embed)

@bot.command()
async def purchase(ctx):
    embed = discord.Embed(title="Purchase", description="https://xecrethub.com/purchase", color=0xFFA500)
    embed.set_image(url=BANNER_URL)
    await ctx.send(embed=embed)

@bot.command()
async def terms(ctx):
    embed = discord.Embed(title="Terms", description="https://xecrethub.com/terms", color=0xFFA500)
    embed.set_image(url=BANNER_URL)
    await ctx.send(embed=embed)

@bot.command()
async def showcase(ctx):
    try:
        feed_data = [
            {'url': os.getenv('Xecret_Hub_Englsih_Channel'), 'id': 'UC5abJGhz74y-cw88wFqX0Jw'},
            {'url': os.getenv('Xecret_Hub_Thailand_Channel'), 'id': 'UCoLxgTtHYNA8AjOJB1rU-2g'}
        ]
        latest_video = None
        latest_published = None
        for feed_info in feed_data:
            feed = feedparser.parse(feed_info['url'])
            if feed.entries:
                entry = feed.entries[0]
                published = entry.published_parsed
                if latest_published is None or published > latest_published:
                    latest_video = entry
                    latest_published = published
        if latest_video:
            try:
                video_id = latest_video.yt_videoid
            except AttributeError:
                link = getattr(latest_video, "link", "")
                if "youtube.com/watch?v=" in link:
                    video_id = link.split("v=")[1].split("&")[0]
                elif "youtu.be/" in link:
                    video_id = link.split("youtu.be/")[1].split("?")[0]
                else:
                    video_id = None
            video_title = latest_video.title
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            video_description = getattr(latest_video, 'summary', 'No description available')
            embed = discord.Embed(title=video_title, url=video_url, description=video_description, color=0xFFA500)
            embed.set_image(url=thumbnail_url)
            await ctx.send(content="<@&1383766143939903528>", embed=embed)
        else:
            await ctx.send("No videos found in the YouTube feeds.")
    except Exception as e:
        await ctx.send(f"Error fetching YouTube feeds: {str(e)}")

@bot.command()
async def loginsignup(ctx):
    embed = discord.Embed(title="Terms", description="[Terms](https://xecrethub.com/terms)", color=0xFFA500)
    embed.set_image(url=BANNER_URL)
    await ctx.send(embed=embed)

@bot.command()
async def send_questions(ctx):
    channel = bot.get_channel(1381039725791674490)
    if channel:
        embed = discord.Embed(title="How to use the question?", color=0xFFA500)
        embed.add_field(name="/question", value="Ask a question and get an automatic reply.\nExample: `/question how much`", inline=False)
        embed.set_footer(text=f"https://xecrethub.com | Sent at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        embed.set_image(url=BANNER_URL)
        await channel.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def send(ctx, *, args: str):
    parts = args.split()
    if not parts:
        await ctx.send("Usage: `.send [message] [channel_link_or_id]` or `.send [message]`")
        return
    potential_channel = parts[-1] if len(parts) >= 2 else None
    if potential_channel and potential_channel.startswith("https://discord.com/channels/"):
        try:
            channel_id = int(potential_channel.split('/')[-1])
            target_channel = bot.get_channel(channel_id)
            if target_channel:
                message = ' '.join(parts[:-1])
                await target_channel.send(message)
                confirmation = await ctx.send(f"Message sent to {target_channel.mention}")
                await asyncio.sleep(3)
                try:
                    await confirmation.delete()
                except:
                    pass
            else:
                await ctx.send("Channel not found from the provided link.")
        except:
            await ctx.send("Invalid Discord channel link format.")
    elif potential_channel and potential_channel.isdigit() and len(potential_channel) >= 15:
        try:
            channel_id = int(potential_channel)
            target_channel = bot.get_channel(channel_id)
            if target_channel:
                message = ' '.join(parts[:-1])
                await target_channel.send(message)
                confirmation = await ctx.send(f"Message sent to {target_channel.mention}")
                await asyncio.sleep(3)
                try:
                    await confirmation.delete()
                except:
                    pass
            else:
                await ctx.send("Channel not found.")
        except:
            await ctx.send("Invalid channel ID.")
    else:
        message = ' '.join(parts)
        await ctx.channel.send(message)
        confirmation = await ctx.send(f"Message sent to {ctx.channel.mention}")
        await asyncio.sleep(3)
        try:
            await confirmation.delete()
        except:
            pass
    try:
        await ctx.message.delete()
    except:
        pass

@bot.tree.command(name="question", description="Ask a question and get automatic reply")
@app_commands.describe(query="Your question")
async def question(interaction: discord.Interaction, query: str):
    if interaction.channel_id != 1381039725791674490:
        await interaction.response.send_message("You can use this command only in <#1381039725791674490>.", ephemeral=True)
        return
    lower_content = query.lower()
    AUTO_RESPONSES = {
        'free': "Sorry, there is no free script. Please go to https://xecrethub.com/purchase.",
        'free script': "Sorry, there is no free script. Please go to https://xecrethub.com/purchase.",
        'free download': "Sorry, there is no free download. Please visit https://xecrethub.com/purchase.",
        'free cheat': "Sorry, there is no free cheat. Please purchase at https://xecrethub.com/purchase.",
        'any free': "Sorry, there is no free version. Please visit https://xecrethub.com/purchase.",
        'is it free': "No, it's not free. Visit https://xecrethub.com/purchase.",
        'can i get it free': "No free access available. Purchase at https://xecrethub.com/purchase.",
        'can i download free': "No free download available. Please visit https://xecrethub.com/purchase.",
        'can i use free': "No free version available. Please visit https://xecrethub.com/purchase.",
        'can i use it free': "No free version available. Please visit https://xecrethub.com/purchase.",
        'can i use free script': "No free script available. Please visit https://xecrethub.com/purchase.",
        'can i use free cheat': "No free cheat available. Please visit https://xecrethub.com/purchase.",
        'how much': "View pricing at https://xecrethub.com/purchase.",
        'get': "View pricing at https://xecrethub.com/purchase and get script in https://discord.com/channels/1328392700294070313/1374422401147998319.",
        'price': "View pricing at https://xecrethub.com/purchase.",
        'cost': "View pricing at https://xecrethub.com/purchase.",
        'buy': "Please visit https://xecrethub.com/purchase to buy.",
        'purchase': "Please visit https://xecrethub.com/purchase to purchase.",
        'payment': "You can purchase here: https://xecrethub.com/purchase.",
        'paid': "Please visit https://xecrethub.com/purchase to purchase.",
        'where to buy': "You can buy it here: https://xecrethub.com/purchase.",
        'how to buy': "Purchase guide available at https://xecrethub.com/purchase.",
        'how to purchase': "Purchase guide available at https://xecrethub.com/purchase.",
        'video': "Go to https://discord.com/channels/1328392700294070313/1328406450489393253.",
        'vid': "Go to https://discord.com/channels/1328392700294070313/1328406450489393253.",
        'show': "Go to https://discord.com/channels/1328392700294070313/1328406450489393253.",
        'showcase': "Go to https://discord.com/channels/1328392700294070313/1328406450489393253.",
        'example': "Example video here: https://discord.com/channels/1328392700294070313/1328406450489393253.",
        'demo': "Demo available here: https://discord.com/channels/1328392700294070313/1328406450489393253.",
        'how to use': "You can read how to use at https://xecrethub.com.",
        'supported games': "You can check supported games here: https://xecrethub.com/games.",
        'games list': "You can check supported games here: https://xecrethub.com/games.",
        'game support': "Supported games are listed here: https://xecrethub.com/games.",
        'game': "Supported games are listed here: https://xecrethub.com/games.",
        'what games': "You can check supported games here: https://xecrethub.com/games.",
        'which games': "You can check supported games here: https://xecrethub.com/games.",
        'supported executors': "You can check supported executors here: https://xecrethub.com/executors.",
        'executors list': "You can check supported executors here: https://xecrethub.com/executors.",
        'executor support': "Supported executors are listed here: https://xecrethub.com/executors.",
        'executor': "Supported executors are listed here: https://xecrethub.com/executors.",
        'which executor': "Check supported executors: https://xecrethub.com/executors.",
        'which executors': "Check supported executors: https://xecrethub.com/executors.",
        'term': "Here: https://xecrethub.com/terms.",
        'terms': "You can find our terms here: https://xecrethub.com/terms.",
        'tos': "Terms of Service: https://xecrethub.com/terms.",
        'help': "Go to https://discord.com/channels/1328392700294070313/1348578938024104006.",
        'support': "For support, please visit https://xecrethub.com.",
        'i need help': "Contact support here: https://discord.com/channels/1328392700294070313/1348578938024104006.",
        'issue': "Report issue here: https://discord.com/channels/1328392700294070313/1348578938024104006.",
        'contact support': "For support, please visit https://discord.com/channels/1328392700294070313/1348578938024104006.",
        'website': "Visit https://xecrethub.com.",
        'site': "Visit https://xecrethub.com.",
        'web': "Visit https://xecrethub.com.",
        'official site': "Visit https://xecrethub.com.",
        'official website': "Visit https://xecrethub.com.",
        'official': "Visit https://xecrethub.com.",
        'xecret': "Visit https://xecrethub.com.",
        'discord': "Join our Discord here: https://discord.gg/xecrethub.",
        'dc': "Join our Discord here: https://discord.gg/xecrethub.",
        'discord link': "Join our Discord here: https://discord.gg/xecrethub.",
        'how to join discord': "Join our Discord here: https://discord.gg/xecrethub.",
        'how to join': "Join our Discord here: https://discord.gg/xecrethub.",
        'error': "If you encounter an error, please contact support via https://discord.com/channels/1328392700294070313/1348578938024104006.",
        'not working': "If something is not working, please contact support via https://discord.com/channels/1328392700294070313/1348578938024104006.",
        'crash': "If it crashes, please report the issue at https://discord.com/channels/1328392700294070313/1348578938024104006.",
        'lag': "If it lag, please report the issue at https://discord.com/channels/1328392700294070313/1348578938024104006.",
        'broken': "If something's broken, reach out via https://discord.com/channels/1328392700294070313/1348578938024104006.",
        'bug': "If something's broken, reach out via https://discord.com/channels/1328392700294070313/1348578938024104006.",
        'usage': "Instructions on usage are here: https://xecrethub.com.",
        'guide': "Find the usage guide here: https://xecrethub.com/guide.",
        'instructions': "Instructions on usage are here: https://xecrethub.com.",
        'update': "Go to https://discord.com/channels/1328392700294070313/1335520199205585000.",
        'version': "Go to https://discord.com/channels/1328392700294070313/1335520199205585000.",
        'latest version': "Check latest version here: https://discord.com/channels/1328392700294070313/1335520199205585000.",
        'latest update': "Check latest update here: https://discord.com/channels/1328392700294070313/1335520199205585000.",
        'refund': "We do not accept refunds.",
        'can i refund': "We do not provide refunds as per our terms."
    }
    for trigger, response in AUTO_RESPONSES.items():
        if trigger in lower_content:
            await interaction.response.send_message(response)
            await asyncio.sleep(5)
            try:
                msg = await interaction.original_response()
                await asyncio.sleep(0.5)
                await msg.delete()
            except:
                pass
            return
    await interaction.response.send_message("No matching FAQ found.")
    await asyncio.sleep(5)
    try:
        msg = await interaction.original_response()
        await asyncio.sleep(0.5)
        await msg.delete()
    except:
        pass

server_on()
bot.run(os.getenv('TOKEN'))
