from telethon import events,functions,errors
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from config import Config
import asyncio
import threading
import requests
import re

def cronjob():
    threading.Timer(60*5, cronjob).start()
    requests.get(Config.DOMAIN)
    
if "heroku" in Config.DOMAIN:
    cronjob()

client = TelegramClient(
            StringSession(),
            Config.API_ID,
            Config.API_HASH,
            # proxy=("socks5","127.0.0.1",9050)
            ).start(bot_token=Config.TOKEN)

username_bot = client.get_me().username

def get_file_name(message):
    if message.file.name:
        return message.file.name.replace(" ","-")
    ext = message.file.ext or ""
    return f"file{ext}"

@client.on(events.NewMessage)
async def download(event):
    if (pv := event.is_private) or event.is_group :
        if pv:
            await event.reply("You are not allowed, bye")
    return
                        
                    
client.run_until_disconnected()
