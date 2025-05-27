import discord
import aiohttp
import asyncio
import os

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
TWITCH_USERS = os.getenv("TWITCH_USERS", "").split(",")
KICK_USERS = os.getenv("KICK_USERS", "").split(",")

intents = discord.Intents.default()

class MyClient(discord.Client):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.already_live = set()

    async def setup_hook(self):
        self.bg_task = asyncio.create_task(self.check_streams())

    async def check_twitch(self, session, user):
        url = f"https://decapi.me/twitch/status/{user}"
        async with session.get(url) as resp:
            text = await resp.text()
            return "offline" not in text.lower()

    async def check_kick(self, session, user):
        url = f"https://kick.com/api/v1/channels/{user}"
        async with session.get(url) as resp:
            data = await resp.json()
            return data.get("livestream") is not None

    async def check_streams(self):
        await self.wait_until_ready()
        channel = self.get_channel(CHANNEL_ID)
        async with aiohttp.ClientSession() as session:
            while not self.is_closed():
                # Kick
                for user in KICK_USERS:
                    key = f"kick:{user}"
                    if await self.check_kick(session, user) and key not in self.already_live:
                        await channel.send(f"🟢 {user} в эфире на Kick! https://kick.com/{user}")
                        self.already_live.add(key)
                    elif not await self.check_kick(session, user) and key in self.already_live:
                        self.already_live.remove(key)

                # Twitch
                for user in TWITCH_USERS:
                    key = f"twitch:{user}"
                    if await self.check_twitch(session, user) and key not in self.already_live:
                        await channel.send(f"🔴 {user} запустил стрим на Twitch! https://twitch.tv/{user}")
                        self.already_live.add(key)
                    elif not await self.check_twitch(session, user) and key in self.already_live:
                        self.already_live.remove(key)

                await asyncio.sleep(60)

    async def on_ready(self):
        print(f"Logged in as {self.user}")

client = MyClient(intents=intents)
client.run(TOKEN)
