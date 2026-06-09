import asyncio
import logging
import os
import sys
from pyrogram import Client, idle, StopPropagation
from pytgcalls import PyTgCalls
from config import Config
from database.db import db
from helpers.utils import convert_json_to_netscape
from helpers.styling import small_caps
import modules.music as music

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
        
        print("\n✅ Session string generated and saved to .env!")
        print("Bot will now restart...")
        
        # Restart the script
        os.execv(sys.executable, ['python'] + sys.argv)
        
    except Exception as e:
        logger.error(f"Failed to generate session: {e}")
        await temp_client.disconnect()
        sys.exit(1)

async def init():
    # Add FFMPEG to PATH
    ffmpeg_path = os.path.abspath("FFMPEG")
    if os.path.exists(ffmpeg_path):
        os.environ["PATH"] += os.pathsep + ffmpeg_path
        logger.info(f"Added FFMPEG to PATH: {ffmpeg_path}")
    else:
        logger.warning("FFMPEG directory not found!")

    # Check for Session String
    if not Config.SESSION_STRING or Config.SESSION_STRING == "":
        await generate_session()

    # Initialize Database
    await db.init()
    
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

    # Global Chat Registration & State Enforcement Middleware
    @bot.on_message(group=-1)
    async def global_middleware(client, message):
        if not message: return
        
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
