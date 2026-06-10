import asyncio
import logging
import os
import sys
import httpx

# Monkeypatch httpx to support proxies argument in top-level functions (needed for youtubesearchpython compatibility with new httpx)
def patch_httpx():
    orig_post = httpx.post
    orig_get = httpx.get

    def patched_post(*args, **kwargs):
        if 'proxies' in kwargs:
            proxies = kwargs.pop('proxies')
            if proxies:
                with httpx.Client(proxies=proxies) as client:
                    return client.post(*args, **kwargs)
        return orig_post(*args, **kwargs)

    def patched_get(*args, **kwargs):
        if 'proxies' in kwargs:
            proxies = kwargs.pop('proxies')
            if proxies:
                with httpx.Client(proxies=proxies) as client:
                    return client.get(*args, **kwargs)
        return orig_get(*args, **kwargs)

    httpx.post = patched_post
    httpx.get = patched_get

patch_httpx()

from pyrogram import Client, idle, StopPropagation
from pyrogram.types import BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeAllGroupChats
from pytgcalls import PyTgCalls
from config import Config
from database.db import db
from helpers.utils import convert_json_to_netscape
from helpers.styling import small_caps
import modules.music as music
from helpers.void_state import VoidState, trigger_void_event

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/bot.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

async def generate_session():
    print("\n--- Userbot Session Generation ---")
    phone_number = input("Enter your Phone Number (with country code): ")
    
    # Initialize a temporary client
    temp_client = Client(
        "temp_userbot",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        in_memory=True
    )
    
    await temp_client.connect()
    
    try:
        code_info = await temp_client.send_code(phone_number)
        phone_code = input("Enter the OTP sent to your Telegram: ")
        
        try:
            await temp_client.sign_in(phone_number, code_info.phone_code_hash, phone_code)
        except Exception as e:
            if "SESSION_PASSWORD_NEEDED" in str(e):
                password = input("Enter your 2FA Password: ")
                await temp_client.check_password(password)
            else:
                raise e
                
        session_string = await temp_client.export_session_string()
        
        # Save to .env
        with open(".env", "r") as f:
            lines = f.readlines()
        
        with open(".env", "w") as f:
            found = False
            for line in lines:
                if line.startswith("SESSION_STRING="):
                    f.write(f"SESSION_STRING={session_string}\n")
                    found = True
                else:
                    f.write(line)
            if not found:
                f.write(f"SESSION_STRING={session_string}\n")
        
        print("\nSession string generated and saved to .env!")
        print("Bot will now restart...")
        
        # Restart the script
        os.execv(sys.executable, ['python'] + sys.argv)
        
    except Exception as e:
        logger.error(f"Failed to generate session: {e}")
        await temp_client.disconnect()
        sys.exit(1)

async def init():
    # Add FFMPEG to PATH (Prepend to bypass any slow/broken system FFMPEG binaries)
    ffmpeg_path = os.path.abspath("FFMPEG")
    if os.path.exists(ffmpeg_path):
        os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ["PATH"]
        logger.info(f"Prepended FFMPEG to PATH: {ffmpeg_path}")
    else:
        logger.warning("FFMPEG directory not found!")

    # Check for Session String
    if not Config.SESSION_STRING or Config.SESSION_STRING == "":
        await generate_session()

    # Initialize Database
    await db.init()
    
    # Save Cookies from Env Variables if provided
    youtube_cookie_env = os.getenv("YOUTUBE_COOKIE")
    if youtube_cookie_env:
        try:
            os.makedirs("COOKIE", exist_ok=True)
            with open("COOKIE/Youtube_Cookie.txt", "w", encoding="utf-8") as f:
                f.write(youtube_cookie_env.strip())
            logger.info("Loaded YouTube cookie from environment variable.")
        except Exception as ce:
            logger.error(f"Failed to save YOUTUBE_COOKIE from env: {ce}")

    spotify_cookie_env = os.getenv("SPOTIFY_COOKIE")
    if spotify_cookie_env:
        try:
            os.makedirs("COOKIE", exist_ok=True)
            with open("COOKIE/Spotify_Cookie.txt", "w", encoding="utf-8") as f:
                f.write(spotify_cookie_env.strip())
            logger.info("Loaded Spotify cookie from environment variable.")
        except Exception as ce:
            logger.error(f"Failed to save SPOTIFY_COOKIE from env: {ce}")

    # Convert Cookies to Netscape Format
    convert_json_to_netscape("COOKIE/Youtube_Cookie.txt", "COOKIE/Youtube_Netscape.txt")
    convert_json_to_netscape("COOKIE/Spotify_Cookie.txt", "COOKIE/Spotify_Netscape.txt")
    
    # Initialize the Bot Client
    bot = Client(
        "MusicManagerBot",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN,
        plugins=dict(root="modules")
    )
    
    # Initialize the Userbot Client (Required for Voice Chat)
    userbot = Client(
        "MusicUserbot",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        session_string=Config.SESSION_STRING
    )
    
    # Initialize PyTgCalls with the Userbot
    call_py = PyTgCalls(userbot)
    music.pytgcalls = call_py
    music.userbot = userbot
    music.init_handlers(call_py) # Register events
    
    # Start the clients
    await bot.start()
    await userbot.start()
    await call_py.start()

    # Set Bot Commands programmatically
    try:
        group_commands = [
            BotCommand("start", "ꜱᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ"),
            BotCommand("help", "ɢᴇᴛ ᴛʜᴇ ʜᴇʟᴘ ᴍᴇɴᴜ"),
            BotCommand("play", "ᴘʟᴀʏ ᴀᴜᴅɪᴏ ɪɴ ɢʀᴏᴜᴘ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ"),
            BotCommand("vplay", "ᴘʟᴀʏ ᴠɪᴅᴇᴏ ɪɴ ɢʀᴏᴜᴘ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ"),
            BotCommand("queue", "**ꜱʜᴏᴡ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴛʀᴀᴄᴋ Qᴜᴇᴜᴇ**" if False else "ꜱʜᴏᴡ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴛʀᴀᴄᴋ Qᴜᴇᴜᴇ"), # No markdown tags
            BotCommand("pause", "ᴘᴀᴜꜱᴇ ᴛʜᴇ ꜱᴛʀᴇᴀᴍɪɴɢ ᴀᴜᴅɪᴏ/ᴠɪᴅᴇᴏ"),
            BotCommand("resume", "ʀᴇꜱᴜᴍᴇ ᴛʜᴇ ᴘᴀᴜꜱᴇᴅ ꜱᴛʀᴇᴀᴍ"),
            BotCommand("skip", "ꜱᴋɪᴘ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴛʀᴀᴄᴋ"),
            BotCommand("stop", "ꜱᴛᴏᴘ ꜱᴛʀᴇᴀᴍɪɴɢ ᴀɴᴅ ʟᴇᴀᴠᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ"),
            BotCommand("q", "ᴛᴜʀɴ ʀᴇᴘʟɪᴇᴅ ᴍᴇꜱꜱᴀɢᴇ(ꜱ) ɪɴᴛᴏ ᴀ Qᴜᴏᴛᴇ ꜱᴛɪᴄᴋᴇʀ"),
            BotCommand("quote", "ᴛᴜʀɴ ʀᴇᴘʟɪᴇᴅ ᴍᴇꜱꜱᴀɢᴇ(ꜱ) ɪɴᴛᴏ ᴀ Qᴜᴏᴛᴇ ꜱᴛɪᴄᴋᴇʀ"),
            BotCommand("info", "ᴠɪᴇᴡ ᴜꜱᴇʀ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ ᴀɴᴅ ᴅᴄ ɪᴅ"),
            BotCommand("id", "ɢᴇᴛ ᴜꜱᴇʀ, ᴄʜᴀᴛ, ᴏʀ ᴄʜᴀɴɴᴇʟ ɪᴅ"),
            BotCommand("ping", "<b>ᴄʜᴇᴄᴋ ʙᴏᴛ ʀᴇꜱᴘᴏɴꜱᴇ ʟᴀᴛᴇɴᴄʏ</b>" if False else "ᴄʜᴇᴄᴋ ʙᴏᴛ ʀᴇꜱᴘᴏɴꜱᴇ ʟᴀᴛᴇɴᴄʏ"),
            BotCommand("staff", "ᴠɪᴇᴡ ɢʀᴏᴜᴘ ᴀᴅᴍɪɴɪꜱᴛʀᴀᴛᴏʀꜱ ʟɪꜱᴛ"),
            BotCommand("bots", "ᴠɪᴇᴡ ʟɪꜱᴛ ᴏꜰ ʙᴏᴛꜱ ɪɴ ᴛʜᴇ ᴄʜᴀᴛ"),
            BotCommand("stickerid", "ɢᴇᴛ ᴛʜᴇ ᴛᴇʟᴇɢʀᴀᴍ ꜰɪʟᴇ ɪᴅ ᴏꜰ ᴀ ꜱᴛɪᴄᴋᴇʀ"),
            BotCommand("kang", "ᴀᴅᴅ ʀᴇᴘʟɪᴇᴅ ꜱᴛɪᴄᴋᴇʀ ᴏʀ ᴘʜᴏᴛᴏ ᴛᴏ ᴄᴜꜱᴛᴏᴍ ᴘᴀᴄᴋ"),
            BotCommand("font", "ꜱᴛʏʟɪᴢᴇ ᴛᴇxᴛ ᴜꜱɪɴɢ ᴜɴɪᴄᴏᴅᴇ ꜰᴏɴᴛꜱ"),
            BotCommand("wish", "ᴍᴀᴋᴇ ᴀ ᴡɪꜱʜ ᴛᴏ ᴛʜᴇ ᴄᴏꜱᴍɪᴄ ᴡɪꜱʜɪɴɢ ᴡᴇʟʟ"),
            BotCommand("sigma", "ɢᴇᴛ ʏᴏᴜʀ ᴅᴀɪʟʏ ꜱɪɢᴍᴀ ʟᴇᴠᴇʟ ʀᴀᴛɪɴɢ"),
            BotCommand("cute", "ɢᴇᴛ ʏᴏᴜʀ ᴅᴀɪʟʏ ᴄᴜᴛᴇɴᴇꜱꜱ ʟᴇᴠᴇʟ ʀᴀᴛɪɴɢ"),
            BotCommand("wallet", "ᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴇᴄᴏɴᴏᴍʏ ᴄᴏɪɴ ʙᴀʟᴀɴᴄᴇ"),
            BotCommand("bal", "ᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴇᴄᴏɴᴏᴍʏ ᴄᴏɪɴ ʙᴀʟᴀɴᴄᴇ"),
            BotCommand("daily", "<b>ᴄʟᴀɪᴍ ʏᴏᴜʀ ᴅᴀɪʟʏ ᴇᴄᴏɴᴏᴍʏ ᴄᴏɪɴꜱ</b>" if False else "ᴄʟᴀɪᴍ ʏᴏᴜʀ ᴅᴀɪʟʏ ᴇᴄᴏɴᴏᴍʏ ᴄᴏɪɴꜱ"),
            BotCommand("pay", "ᴛʀᴀɴꜱꜰᴇʀ ᴇᴄᴏɴᴏᴍʏ ᴄᴏɪɴꜱ ᴛᴏ ᴀɴᴏᴛʜᴇʀ ᴜꜱᴇʀ"),
            BotCommand("rob", "ᴀᴛᴛᴇᴍᴘᴛ ᴛᴏ ʀᴏʙ ᴄᴏɪɴꜱ ꜰʀᴏᴍ ᴀɴᴏᴛʜᴇʀ ᴜꜱᴇʀ"),
            BotCommand("toprich", "ᴠɪᴇᴡ ᴛʜᴇ ᴄʜᴀᴛ ᴇᴄᴏɴᴏᴍʏ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ"),
            BotCommand("topkills", "ᴠɪᴇᴡ ᴛʜᴇ ᴛᴏᴘ ᴋɪʟʟᴇʀꜱ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ"),
            BotCommand("ban", "ᴘᴇʀᴍᴀɴᴇɴᴛʟʏ ʙᴀɴ ᴀ ᴜꜱᴇʀ ꜰʀᴏᴍ ᴛʜᴇ ᴄʜᴀᴛ"),
            BotCommand("unban", "ᴜɴʙᴀɴ ᴀ ᴜꜱᴇʀ ꜰʀᴏᴍ ᴛʜᴇ ᴄʜᴀᴛ"),
            BotCommand("kick", "ᴋɪᴄᴋ ᴀ ᴜꜱᴇʀ ꜰʀᴏᴍ ᴛʜᴇ ᴄʜᴀᴛ"),
            BotCommand("mute", "ᴍᴜᴛᴇ ᴀ ᴜꜱᴇʀ'ꜱ ᴛᴇxᴛ ᴍᴇꜱꜱᴀɢᴇꜱ ɪɴ ᴛʜᴇ ᴄʜᴀᴛ"),
            BotCommand("unmute", "ᴜɴᴍᴜᴛᴇ ᴀ ᴜꜱᴇʀ ɪɴ ᴛʜᴇ ᴄʜᴀᴛ"),
            BotCommand("warn", "ɪꜱꜱᴜᴇ ᴀ ᴡᴀʀɴɪɴɢ ᴛᴏ ᴀ ᴜꜱᴇʀ"),
            BotCommand("warnings", "ᴄʜᴇᴄᴋ ᴡᴀʀɴɪɴɢꜱ ʜɪꜱᴛᴏʀʏ ᴏꜰ ᴀ ᴜꜱᴇʀ"),
            BotCommand("purge", "ᴅᴇʟᴇᴛᴇ ᴍᴇꜱꜱᴀɢᴇꜱ ꜰʀᴏᴍ ᴛʜᴇ ʀᴇᴘʟɪᴇᴅ ᴏɴᴇ ᴛᴏ ᴄᴜʀʀᴇɴᴛ"),
            BotCommand("pin", "ᴘɪɴ ᴛʜᴇ ʀᴇᴘʟɪᴇᴅ ᴍᴇꜱꜱᴀɢᴇ"),
            BotCommand("unpin", "ᴜɴᴘɪɴ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛʟʏ ᴘɪɴɴᴇᴅ ᴍᴇꜱꜱᴀɢᴇ"),
            BotCommand("promote", "ᴘʀᴏᴍᴏᴛᴇ ᴀ ᴜꜱᴇʀ ᴛᴏ ᴀᴅᴍɪɴɪꜱᴛʀᴀᴛᴏʀ"),
            BotCommand("demote", "ᴅᴇᴍᴏᴛᴇ ᴀɴ ᴀᴅᴍɪɴɪꜱᴛʀᴀᴛᴏʀ ᴛᴏ ᴀ ʀᴇɢᴜʟᴀʀ ᴜꜱᴇʀ"),
            BotCommand("tagall", "ᴍᴇɴᴛɪᴏɴ ᴀʟʟ ɢʀᴏᴜᴘ ᴍᴇᴍʙᴇʀꜱ"),
            BotCommand("vctag", "ɪɴᴠɪᴛᴇ ᴀʟʟ ɢʀᴏᴜᴘ ᴍᴇᴍʙᴇʀꜱ ᴛᴏ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ"),
            BotCommand("utag", "ᴍᴇɴᴛɪᴏɴ ᴀʟʟ ɢʀᴏᴜᴘ ᴍᴇᴍʙᴇʀꜱ ᴡɪᴛʜ ᴀ ᴄᴜꜱᴛᴏᴍ ᴍᴇꜱꜱᴀɢᴇ"),
            BotCommand("zombies", "ᴋɪᴄᴋ ᴀʟʟ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛꜱ ꜰʀᴏᴍ ᴛʜᴇ ᴄʜᴀᴛ")
        ]
        
        private_commands = [
            BotCommand("start", "**ꜱᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ**" if False else "ꜱᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ"),
            BotCommand("help", "ɢᴇᴛ ᴛʜᴇ ʜᴇʟᴘ ᴍᴇɴᴜ"),
            BotCommand("info", "ᴠɪᴇᴡ ᴜꜱᴇʀ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ ᴀɴᴅ ᴅᴄ ɪᴅ"),
            BotCommand("id", "ɢᴇᴛ ᴜꜱᴇʀ, ᴄʜᴀᴛ, ᴏʀ ᴄʜᴀɴɴᴇʟ ɪᴅ"),
            BotCommand("ping", "ᴄʜᴇᴄᴋ ʙᴏᴛ ʀᴇꜱᴘᴏɴꜱᴇ ʟᴀᴛᴇɴᴄʏ"),
            BotCommand("stickerid", "ɢᴇᴛ ᴛʜᴇ ᴛᴇʟᴇɢʀᴀᴍ ꜰɪʟᴇ ɪᴅ ᴏꜰ ᴀ ꜱᴛɪᴄᴋᴇʀ"),
            BotCommand("font", "ꜱᴛʏʟɪᴢᴇ ᴛᴇxᴛ ᴜꜱɪɴɢ ᴜɴɪᴄᴏᴅᴇ ꜰᴏɴᴛꜱ"),
            BotCommand("wish", "ᴍᴀᴋᴇ ᴀ ᴡɪꜱʜ ᴛᴏ ᴛʜᴇ ᴄᴏꜱᴍɪᴄ ᴡɪꜱʜɪɴɢ ᴡᴇʟʟ"),
            BotCommand("sigma", "ɢᴇᴛ ʏᴏᴜʀ ᴅᴀɪʟʏ ꜱɪɢᴍᴀ ʟᴇᴠᴇʟ ʀᴀᴛɪɴɢ"),
            BotCommand("cute", "ɢᴇᴛ ʏᴏᴜʀ ᴅᴀɪʟʏ ᴄᴜᴛᴇɴᴇꜱꜱ ʟᴇᴠᴇʟ ʀᴀᴛɪɴɢ"),
            BotCommand("wallet", "ᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴇᴄᴏɴᴏᴍʏ ᴄᴏɪɴ ʙᴀʟᴀɴᴄᴇ"),
            BotCommand("bal", "ᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴇᴄᴏɴᴏᴍʏ ᴄᴏɪɴ ʙᴀʟᴀɴᴄᴇ"),
            BotCommand("daily", "ᴄʟᴀɪᴍ ʏᴏᴜʀ ᴅᴀɪʟʏ ᴇᴄᴏɴᴏᴍʏ ᴄᴏɪɴꜱ"),
            BotCommand("pay", "ᴛʀᴀɴꜱꜰᴇʀ ᴇᴄᴏɴᴏᴍʏ ᴄᴏɪɴꜱ ᴛᴏ ᴀɴᴏᴛʜᴇʀ ᴜꜱᴇʀ"),
            BotCommand("rob", "ᴀᴛᴛᴇᴍᴘᴛ ᴛᴏ ʀᴏʙ ᴄᴏɪɴꜱ ꜰʀᴏᴍ ᴀɴᴏᴛʜᴇʀ ᴜꜱᴇʀ"),
            BotCommand("toprich", "ᴠɪᴇᴡ ᴛʜᴇ ᴄʜᴀᴛ ᴇᴄᴏɴᴏᴍʏ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ"),
            BotCommand("topkills", "ᴠɪᴇᴡ ᴛʜᴇ ᴛᴏᴘ ᴋɪʟʟᴇʀꜱ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ")
        ]

        await bot.set_bot_commands(group_commands, scope=BotCommandScopeAllGroupChats())
        await bot.set_bot_commands(private_commands, scope=BotCommandScopeAllPrivateChats())
        logger.info("Bot commands successfully registered for all group and private chats.")
    except Exception as cmd_err:
        logger.error(f"Failed to set bot commands: {cmd_err}")

    # Global Chat Registration & State Enforcement Middleware
    @bot.on_message(group=-1)
    async def global_middleware(client, message):
        if not message: return
        
        # 0. Void Event Intercepts & Tracking
        user_id = message.from_user.id if message.from_user else None
        
        # Ghost Watch Mirroring
        if message.chat:
            for owner_id, watched_chat_id in list(VoidState.ghost_watches.items()):
                if message.chat.id == watched_chat_id:
                    try:
                        sender_name = message.from_user.first_name if message.from_user else "System"
                        chat_name = message.chat.title or "Group"
                        text_content = message.text or message.caption or "[Media/Sticker]"
                        mirror_text = f"<blockquote><b>[GHOST WATCH: {chat_name}]</b>\n" \
                                      f"<b>{sender_name}</b>: {text_content}</blockquote>"
                        await client.send_message(owner_id, mirror_text)
                    except Exception:
                        pass

        # Trigger Void Events (Observe & Blackbox)
        if message.chat:
            chat_title = message.chat.title or "Private"
            sender_mention = message.from_user.mention if message.from_user else "System"
            
            if message.new_chat_members:
                names = ", ".join(u.first_name for u in message.new_chat_members)
                await trigger_void_event(client, "join", f"{names} joined {chat_title} (<code>{message.chat.id}</code>)")
            elif message.left_chat_member:
                await trigger_void_event(client, "leave", f"{message.left_chat_member.first_name} left {chat_title} (<code>{message.chat.id}</code>)")
            elif message.text and message.text.startswith("/"):
                await trigger_void_event(client, "command", f"{sender_mention} ran <code>{message.text[:60]}</code> in {chat_title} (<code>{message.chat.id}</code>)")

        # Phantom Mode Command Deletion
        if VoidState.phantom_active and user_id == Config.OWNER_ID:
            if message.text and message.text.startswith("/"):
                try:
                    await message.delete()
                except Exception:
                    pass

        # 1. Registration
        if message.chat:
            await db.add_served_chat(message.chat.id)
        if message.from_user:
            await db.add_served_user(message.from_user.id)
            
        # 2. State Enforcement (Shadowban & Maintenance)
        user_id = message.from_user.id if message.from_user else None
        if not user_id: return

        # Shadowban Check
        is_shadow = await db.get_setting(f"shadowban_{user_id}")
        if is_shadow == "true":
            raise StopPropagation()
            
        # Maintenance Check (Owner and Sudoers bypass)
        is_maint = await db.get_setting("maintenance")
        if is_maint == "true":
            sudoers_list = await db.get_sudoers()
            if user_id != Config.OWNER_ID and user_id not in sudoers_list:
                # Optional: Notify user about maintenance
                if message.text and message.text.startswith("/"):
                    try:
                        await message.reply_text(small_caps("ʙᴏᴛ ɪꜱ ᴜɴᴅᴇʀ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ. ᴘʟᴇᴀꜱᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ."))
                    except: pass
                raise StopPropagation()
    
    logger.info("Bot, Userbot, and Voice Client started successfully.")
    
    # Keep the bot running
    await idle()
    
    # Stop the clients
    await call_py.stop()
    await userbot.stop()
    await bot.stop()

if __name__ == "__main__":
    try:
        asyncio.run(init())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Error occurred: {e}")
