import discord
import aiohttp
import asyncio
import os

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
TWITCH_USERS = os.getenv("TWITCH_USERS", "").split(",")
KICK_USERS = os.getenv("KICK_USERS", "").split(",")

intents = discord.Intents.default()
client = discord.Client(intents=intents)

already_live = set()

async def check_twitch(session, user):
    url = f"https://decapi.me/twitch/status/{user}"
    async with session.get(url) as resp:
        text = await resp.text()
        return "offline" not in text.lower()

async def check_kick(session, user):
    url = f"https://kick.com/api/v1/channels/{user}"
    async with session.get(url) as resp:
        data = await resp.json()
        return data.get("livestream") is not None

async def check_streams():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    async with aiohttp.ClientSession() as session:
        while not client.is_closed():
            # Приоритет: сначала Kick
            for user in KICK_USERS:
                key = f"kick:{user}"
                if await check_kick(session, user) and key not in already_live:
                    await channel.send(f"🟢 {user} в эфире на Kick! https://kick.com/{user}")
                    already_live.add(key)
                elif not await check_kick(session, user) and key in already_live:
                    already_live.remove(key)

            # Затем Twitch
            for user in TWITCH_USERS:
                key = f"twitch:{user}"
                if await check_twitch(session, user) and key not in already_live:
                    await channel.send(f"🔴 {user} запустил стрим на Twitch! https://twitch.tv/{user}")
                    already_live.add(key)
                elif not await check_twitch(session, user) and key in already_live:
                    already_live.remove(key)

            await asyncio.sleep(60)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

client.loop.create_task(check_streams())
client.run(TOKEN)