import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import datetime
import feedparser
import os

from myserver import server_on

LATEST_VIDEO_FILE = "latest_video_id.txt"
latest_video_id = None
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='-', intents=intents, help_command=None)

PROTECTED_USER_IDS = [1300017174886350899,914141419688591361,905399402724728833]
TIMEOUT_DURATION = 5
ALLOWED_CHANNEL_IDS = [1380891908376760401,1381039725791674490]

KEYWORD_AUTO_REPLIES = {
    "get": "If you mean the script, go to https://discord.com/channels/1328392700294070313/1374422401147998319.",
    "free": "If you mean the script, then there is definitely no free one.",
    "drop": "Coughing garbage",
    "<@1300017174886350899>": "<:79627innocent:1380543606489612441>",
    "<@914141419688591361>": "<:79627innocent:1380543606489612441>",
    "<@905399402724728833>": "<:79627innocent:1380543606489612441>",
}

WHITELIST_USER_IDS = []

BANNER_URL = 'https://media.discordapp.net/attachments/1378599490902298654/1380901765372973156/Banner.png?ex=6845907c&is=68443efc&hm=865a9ce85dee2225552441fa2d48298745c60c8da1447716b5ab57e5cb31eab8&=&format=webp&quality=lossless&width=1536&height=864'

BAD_WORDS = ['fuck','worst','bad','suck','shit','source','drop','free','leak']

AUTO_RESPONSES = {
    'free': "Sorry, there is no free script. Please go to https://xecrethub.com/purchase.",
    'free script': "Sorry, there is no free script. Please go to https://xecrethub.com/purchase.",
    'free download': "Sorry, there is no free download. Please visit https://xecrethub.com/purchase.",
    'free cheat': "Sorry, there is no free cheat. Please purchase at https://xecrethub.com/purchase.",
    'how much': "View pricing at https://xecrethub.com/purchase.",
    'get': "View pricing at https://xecrethub.com/purchase and get script in                             v                      https://discord.com/channels/1328392700294070313/1374422401147998319.",
    'price': "View pricing at https://xecrethub.com/purchase.",
    'cost': "View pricing at https://xecrethub.com/purchase.",
    'buy': "Please visit https://xecrethub.com/purchase to buy.",
    'video': "Go to https://discord.com/channels/1328392700294070313/1328406450489393253.",
    'vid': "Go to https://discord.com/channels/1328392700294070313/1328406450489393253.",
    'show': "Go to https://discord.com/channels/1328392700294070313/1328406450489393253.",
    'showcase': "Go to https://discord.com/channels/1328392700294070313/1328406450489393253.",
    'example': "example Video Here: https://discord.com/channels/1328392700294070313/1328406450489393253.",
    'purchase': "Please visit https://xecrethub.com/purchase to purchase.",
    'payment': "You can purchase here: https://xecrethub.com/purchase.",
    'supported games': "You can check supported games here: https://xecrethub.com/supported-games.",
    'games list': "You can check supported games here: https://xecrethub.com/supported-games.",
    'game support': "Supported games are listed here: https://xecrethub.com/supported-games.",
    'game': "Supported games are listed here: https://xecrethub.com/supported-games.",
    'supported executors': "You can check supported executors here: https://xecrethub.com/executors.",
    'executors list': "You can check supported executors here: https://xecrethub.com/executors.",
    'executor support': "Supported executors are listed here: https://xecrethub.com/executors.",
    'executor': "Supported executors are listed here: https://xecrethub.com/executors.",
    'login': "Login here: https://xecrethub.com/loginsignup.",
    'sign up': "Sign up here: https://xecrethub.com/loginsignup.",
    'register': "Register here: https://xecrethub.com/loginsignup.",
    'account': "Manage your account here: https://xecrethub.com/loginsignup.",
    'help': "Go to https://discord.com/channels/1328392700294070313/1348578938024104006 or use -help command.",
    'website': "Visit https://xecrethub.com.",
    'site': "Visit https://xecrethub.com.",
    'web': "Visit https://xecrethub.com.",
    'official site': "Visit https://xecrethub.com.",
    'official website': "Visit https://xecrethub.com.",
    'support': "For support, please visit https://xecrethub.com or use -help command.",
    'discord': "Join our Discord here: https://discord.gg/xecrethub.",
    'discord link': "Join our Discord here: https://discord.gg/xecrethub.",
    'error': "If you encounter an error, please contact support via https://discord.com/channels/1328392700294070313/1348578938024104006.",
    'not working': "If something is not working, please contact support via https://discord.com/channels/1328392700294070313/1348578938024104006.",
    'how to use': "You can read how to use at https://xecrethub.com and use -help command.",
    'update': "Go to https://discord.com/channels/1328392700294070313/1335520199205585000.",
    'version': "Go to https://discord.com/channels/1328392700294070313/1335520199205585000.",
    'refund': "We do not accept refunds.",
}

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    print(f'Bot is now online: {bot.user}')
    await bot.change_presence(
        status=discord.Status.dnd,
        activity=discord.Activity(type=discord.ActivityType.watching, name="https://xecrethub.com")
    )

    channel = bot.get_channel(1381039725791674490)
    bot.loop.create_task(youtube_feed_check_loop())
    print(f"Channel fetched: {channel}")  
    try:
        guild = discord.Object(id=1328392700294070313)  
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    if channel:
        try:
            messages = await channel.history(limit=20).flatten()
            already_sent = False
            for msg in messages:
                if msg.author == bot.user and msg.embeds:
                    embed = msg.embeds[0]
                    if embed.title == "How to use the question?":
                        already_sent = True
                        print("How-to-use message already exists. Skipping send.")
                        break

            if not already_sent:
                embed = discord.Embed(title="How to use the question?", color=0xFFFFFF)
                embed.add_field(
                    name="/question",
                    value="Ask a question and get an automatic reply.\nExample: `/question how much`",
                    inline=False
                )
                embed.set_footer(text=f"https://xecrethub.com | Sent at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                embed.image(url=BANNER_URL)
                await channel.send(embed=embed)
                print("Sent how-to-use message to #1381039725791674490")

        except Exception as e:
            print(f"Failed to send how-to-use message: {e}")
    else:
        print("Could not find channel. Check permissions or guild.")

def load_latest_video_id():
    if os.path.exists(LATEST_VIDEO_FILE):
        with open(LATEST_VIDEO_FILE, "r") as f:
            return f.read().strip()
    return None

def save_latest_video_id(video_id):
    with open(LATEST_VIDEO_FILE, "w") as f:
        f.write(video_id)

async def youtube_feed_check_loop():
    global latest_video_id
    latest_video_id = load_latest_video_id() 

    await bot.wait_until_ready()

    channel = bot.get_channel(1328406450489393253)
    feed_url = 'https://www.youtube.com/feeds/videos.xml?channel_id=UC5abJGhz74y-cw88wFqX0Jw'

    while not bot.is_closed():
        try:
            feed = feedparser.parse(feed_url)
            print(f"[YouTube Feed Check] Found {len(feed.entries)} entries.") 

            if feed.entries:
                latest_entry = feed.entries[0]

                try:
                    video_id = latest_entry.yt_videoid
                except AttributeError:
                    if "youtube.com/watch?v=" in latest_entry.link:
                        video_id = latest_entry.link.split("v=")[1].split("&")[0]
                    elif "youtu.be/" in latest_entry.link:
                        video_id = latest_entry.link.split("youtu.be/")[1].split("?")[0]
                    else:
                         video_id = None

                video_title = latest_entry.title
                video_url = f"https://www.youtube.com/watch?v={video_id}"

                if latest_video_id != video_id:
                    latest_video_id = video_id
                    save_latest_video_id(video_id) 

                    if channel:
                        await channel.send(f"📢 **New Video Posted on XecretHub!**\n{video_url}")
                        print(f"[YouTube Feed Check] Posted new video: {video_title} ({video_url})")
                    else:
                        print("❌ Could not find the target Discord channel.")
                else:
                    print(f"[YouTube Feed Check] Latest video already posted: {video_id}")

        except Exception as e:
            print(f"Error checking YouTube feed: {e}")

        await asyncio.sleep(300)

@bot.command()
async def send_buttons(ctx):
    if ctx.channel.id not in ALLOWED_CHANNEL_IDS:
        await ctx.send("You can use this command only in the allowed channel.")
        return

    embed = discord.Embed(
        title="Xecret Hub Control Panel",
        description="Select an option below to view information or perform an action.",
        color=0xFFFFFF
    )
    embed.set_image(url=BANNER_URL)

    view = discord.ui.View(timeout=None)

    view.add_item(discord.ui.Button(label="Visit Website", url="https://xecrethub.com"))
    view.add_item(discord.ui.Button(label="Supported Games", url="https://xecrethub.com/supported-games"))
    view.add_item(discord.ui.Button(label="Supported Executors", url="https://xecrethub.com/executors"))
    view.add_item(discord.ui.Button(label="Purchase", url="https://xecrethub.com/purchase"))
    view.add_item(discord.ui.Button(label="Login / Sign Up", url="https://xecrethub.com/loginsignup"))

    await ctx.send(embed=embed, view=view)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.attachments:
        await bot.process_commands(message)
        return

    if message.embeds:
        await bot.process_commands(message)
        return

    gif_domains = ["https://tenor.com", "https://media.tenor.com", "https://giphy.com", "https://media.giphy.com"]
    if any(domain in message.content for domain in gif_domains):
        await bot.process_commands(message)
        return

    lower_msg = message.content.lower()
    for keyword, reply_text in KEYWORD_AUTO_REPLIES.items():
        if keyword in lower_msg:
            try:
                reply_msg = await message.reply(reply_text, mention_author=False)
                print(f"[Auto Reply] Triggered keyword '{keyword}'")

                async def delete_reply_later(msg):
                    await asyncio.sleep(5)
                    try:
                        await msg.delete()
                    except Exception as e:
                        print(f"[Auto Reply - {keyword}] Failed to delete message: {e}")

                bot.loop.create_task(delete_reply_later(reply_msg))

            except Exception as e:
                print(f"[Auto Reply - {keyword}] Error: {e}")
            break 

    if any(user.id in PROTECTED_USER_IDS for user in message.mentions):
        try:
            await message.delete()
            await message.channel.send(
                f"<@{message.author.id}>, you are not allowed to ping this user. You have been timed out for {TIMEOUT_DURATION} seconds.",
                delete_after=5
            )
            timed_out_until = discord.utils.utcnow() + datetime.timedelta(seconds=TIMEOUT_DURATION)
            await message.author.edit(timed_out_until=timed_out_until, reason="Pinged protected user")
            try:
                await message.author.send(
                    f"You Ping, the person who is working, are so annoying. Go die. You have been timed out for {TIMEOUT_DURATION} seconds."
                )
            except:
                pass
        except:
            pass

    if message.author.id not in WHITELIST_USER_IDS and any(bad_word in message.content.lower() for bad_word in BAD_WORDS):
        try:
            await message.delete()
            await message.channel.send(
                f"<@{message.author.id}>, I hate these words. You have been timed out for {TIMEOUT_DURATION} seconds.",
                delete_after=5
            )
            timed_out_until = discord.utils.utcnow() + datetime.timedelta(seconds=TIMEOUT_DURATION)
            await message.author.edit(timed_out_until=timed_out_until, reason="Used bad language")
            try:
                await message.author.send(
                    f"You say bad words, trash words, just like your face. You have been timed out for {TIMEOUT_DURATION} seconds."
                )
            except:
                pass
        except:
            pass

    if message.channel.id in ALLOWED_CHANNEL_IDS:
        content = message.content.strip()

        if content.startswith('-'):
            await bot.process_commands(message)
            return

        if content.startswith('/question'):
            try:
                await message.delete()
                print(f"Deleted invalid /question message: {content}")
            except Exception as e:
                print(f"Failed to delete invalid /question message: {e}")
            return

        if content.startswith('/'):
            return

        try:
            await message.delete()
            print(f"Deleted message: {content}")
        except Exception as e:
            print(f"Failed to delete message: {e}")
        return

    if message.content.startswith('-') and message.channel.id not in ALLOWED_CHANNEL_IDS:
        if not (
            message.content.startswith('-send') or 
            message.content.startswith('-add_whitelist') or 
            message.content.startswith('-remove_whitelist')
        ):
            try:
                await message.reply(
                    "Use the command at https://discord.com/channels/1328392700294070313/1380891908376760401.",
                    mention_author=False,
                    delete_after=5
                )
                await asyncio.sleep(5)
                await message.delete()
            except:
                pass
            return

        await bot.process_commands(message)
        return

    await bot.process_commands(message)


@bot.command()
async def website(ctx):
    embed = discord.Embed(
        title="Visit our Website",
        description="Click the button below to visit:",
        color=0xFFFFFF
    )
    embed.set_image(url=BANNER_URL)
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(label="xecrethub.com", url="https://xecrethub.com"))
    await ctx.send(embed=embed, view=view)

@bot.command()
async def supported_games(ctx):
    embed = discord.Embed(
        title="Supported Games",
        description="https://xecrethub.com/supported-games",
        color=0xFFFFFF
    )
    embed.set_image(url=BANNER_URL)
    await ctx.send(embed=embed)

@bot.command()
async def supported_executors(ctx):
    embed = discord.Embed(
        title="Supported Executors",
        description="https://xecrethub.com/executors",
        color=0xFFFFFF
    )
    embed.set_image(url=BANNER_URL)
    await ctx.send(embed=embed)

@bot.command()
async def purchase(ctx):
    embed = discord.Embed(
        title="Purchase",
        description="https://xecrethub.com/purchase",
        color=0xFFFFFF
    )
    embed.set_image(url=BANNER_URL)
    await ctx.send(embed=embed)

@bot.command()
async def loginsignup(ctx):
    embed = discord.Embed(
        title="Login / Sign Up",
        description="[Login / Sign Up](https://xecrethub.com/loginsignup)",
        color=0xFFFFFF
    )
    embed.set_image(url=BANNER_URL)
    await ctx.send(embed=embed)

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Bot Commands", color=0x3498db)
    embed.add_field(name="-website", value="Send website link with button", inline=False)
    embed.add_field(name="-supported_games", value="Get list of supported games", inline=False)
    embed.add_field(name="-supported_executors", value="Get list of supported executors", inline=False)
    embed.add_field(name="-purchase", value="How to purchase", inline=False)
    embed.add_field(name="-loginsignup", value="Login / Sign Up", inline=False)
    embed.add_field(name="-send_buttons", value="Send command buttons", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def send(ctx, *, message: str):
    await ctx.send(message)
    try:
        await ctx.message.delete()
    except:
        pass

@bot.command()
@commands.has_permissions(administrator=True)
async def add_whitelist(ctx, user_id: int):
    if user_id not in WHITELIST_USER_IDS:
        WHITELIST_USER_IDS.append(user_id)
        reply = await ctx.send(f"User {user_id} has been added to whitelist.")
    else:
        reply = await ctx.send(f"User {user_id} is already in whitelist.")

    try:
        await ctx.message.delete()
    except:
        pass

    await asyncio.sleep(5)
    try:
        await reply.delete()
    except:
        pass

@bot.command()
@commands.has_permissions(administrator=True)
async def remove_whitelist(ctx, user_id: int):
    if user_id in WHITELIST_USER_IDS:
        WHITELIST_USER_IDS.remove(user_id)
        reply = await ctx.send(f"User {user_id} has been removed from whitelist.")
    else:
        reply = await ctx.send(f"User {user_id} is not in whitelist.")

    try:
        await ctx.message.delete()
    except:
        pass

    await asyncio.sleep(5)
    try:
        await reply.delete()
    except:
        pass

@bot.tree.command(name="question", description="Ask a question and get automatic reply")
@app_commands.describe(query="Your question")
async def question(interaction: discord.Interaction, query: str):
    if interaction.channel_id != 1381039725791674490:
        await interaction.response.send_message(
            "You can use this command only in <#1381039725791674490>.", ephemeral=True
        )
        return

    lower_content = query.lower()
    for trigger_word, response_text in AUTO_RESPONSES.items():
        if trigger_word in lower_content:
            await interaction.response.send_message(response_text)
            await asyncio.sleep(5)
            try:
                msg = await interaction.original_response()
                await asyncio.sleep(0.5)
                await msg.delete()
            except Exception as e:
                print(f"Failed to delete message: {e}")
            return

    await interaction.response.send_message("No matching FAQ found.")
    await asyncio.sleep(5)
    try:
        msg = await interaction.original_response()
        await asyncio.sleep(0.5)
        await msg.delete()
    except Exception as e:
        print(f"Failed to delete message: {e}")

server_on()

bot.run(os.getenv('TOKEN'))
