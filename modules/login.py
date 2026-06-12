import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PasswordHashInvalid
from config import Config
from helpers.styling import small_caps, fraktur
import modules.music as music

class LoginState:
    client = None
    phone_number = None
    phone_code_hash = None

state = LoginState()

@Client.on_message(filters.command("login") & filters.private & filters.user(Config.OWNER_ID))
async def login_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            f"<blockquote>{fraktur('Login Usage')} ❞\n\n"
            f"{small_caps('ᴜѕᴀɢᴇ: /ʟᴏɢɪɴ <ᴘʜᴏɴᴇ_ɴᴜᴍʙᴇʀ> (ɪɴᴄʟᴜᴅɪɴɢ ᴄᴏᴜɴᴛʀʏ ᴄᴏᴅᴇ)')}</blockquote>"
        )
    
    phone = message.text.split(None, 1)[1].strip().replace(" ", "")
    await message.reply_text(f"<blockquote>{small_caps('Initiating connection...')}</blockquote>")
    
    # Disconnect existing temporary login client if active
    if state.client:
        try:
            await state.client.disconnect()
        except:
            pass
            
    state.client = Client(
        "temp_login_userbot",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        in_memory=True
    )
    
    try:
        await state.client.connect()
        code_info = await state.client.send_code(phone)
        state.phone_number = phone
        state.phone_code_hash = code_info.phone_code_hash
        
        await message.reply_text(
            f"<blockquote>{fraktur('OTP Sent')} ❞\n\n"
            f"{small_caps('ᴘʟᴇᴀѕᴇ ѕᴇɴᴅ ᴛʜᴇ ᴏᴛᴘ ᴄᴏᴅᴇ ᴜѕɪɴɢ /ᴏᴛᴘ <code>')}</blockquote>"
        )
    except Exception as err:
        await message.reply_text(
            f"<blockquote>{fraktur('Login Error')} ❞\n\n"
            f"<code>{str(err)}</code></blockquote>"
        )

@Client.on_message(filters.command("otp") & filters.private & filters.user(Config.OWNER_ID))
async def otp_command(client: Client, message: Message):
    if not state.client or not state.phone_number or not state.phone_code_hash:
        return await message.reply_text(
            f"<blockquote>{fraktur('No Active Login')} ❞\n\n"
            f"{small_caps('ᴘʟᴇᴀѕᴇ ѕᴛᴀʀᴛ ᴛʜᴇ ʟᴏɢɪɴ ᴘʀᴏᴄᴇѕѕ ꜰɪʀѕᴛ ᴜѕɪɴɢ /ʟᴏɢɪɴ.')}</blockquote>"
        )
        
    if len(message.command) < 2:
        return await message.reply_text(
            f"<blockquote>{fraktur('OTP Usage')} ❞\n\n"
            f"{small_caps('ᴜѕᴀɢᴇ: /ᴏᴛᴘ <code>')}</blockquote>"
        )
        
    code = message.text.split(None, 1)[1].strip()
    await message.reply_text(f"<blockquote>{small_caps('Verifying OTP...')}</blockquote>")
    
    try:
        try:
            await state.client.sign_in(state.phone_number, state.phone_code_hash, code)
        except SessionPasswordNeeded:
            return await message.reply_text(
                f"<blockquote>{fraktur('2FA Password Required')} ❞\n\n"
                f"{small_caps('ᴛʜɪѕ ᴀᴄᴄᴏᴜɴᴛ ʀᴇQᴜɪʀᴇѕ ᴀ ᴛᴡᴏ-ꜰᴀᴄᴛᴏʀ ᴘᴀѕѕᴡᴏʀᴅ.')}\n\n"
                f"{small_caps('ᴘʟᴇᴀѕᴇ ѕᴇɴᴅ ɪᴛ ᴜѕɪɴɢ /ᴘᴡᴅ <ᴘᴀѕѕᴡᴏʀᴅ>')}</blockquote>"
            )
            
        await finish_login(message)
    except PhoneCodeInvalid:
        await message.reply_text(
            f"<blockquote>{fraktur('Invalid OTP')} ❞\n\n"
            f"{small_caps('ᴛʜᴇ ᴏᴛᴘ ᴄᴏᴅᴇ ʏᴏᴜ ᴇɴᴛᴇʀᴇᴅ ɪѕ ɪɴᴠᴀʟɪᴅ. ᴘʟᴇᴀѕᴇ ᴛʀʏ ᴀɢᴀɪɴ.')}</blockquote>"
        )
    except Exception as err:
        await message.reply_text(
            f"<blockquote>{fraktur('Verification Error')} ❞\n\n"
            f"<code>{str(err)}</code></blockquote>"
        )

@Client.on_message(filters.command("pwd") & filters.private & filters.user(Config.OWNER_ID))
async def pwd_command(client: Client, message: Message):
    if not state.client or not state.phone_number:
        return await message.reply_text(
            f"<blockquote>{fraktur('No Active Login')} ❞\n\n"
            f"{small_caps('ᴘʟᴇᴀѕᴇ ѕᴛᴀʀᴛ ᴛʜᴇ ʟᴏɢɪɴ ᴘʀᴏᴄᴇѕѕ ꜰɪʀѕᴛ ᴜѕɪɴɢ /ʟᴏɢɪɴ.')}</blockquote>"
        )
        
    if len(message.command) < 2:
        return await message.reply_text(
            f"<blockquote>{fraktur('Password Usage')} ❞\n\n"
            f"{small_caps('ᴜѕᴀɢᴇ: /ᴘᴡᴅ <ᴘᴀѕѕᴡᴏʀᴅ>')}</blockquote>"
        )
        
    password = message.text.split(None, 1)[1].strip()
    await message.reply_text(f"<blockquote>{small_caps('Verifying 2FA password...')}</blockquote>")
    
    try:
        await state.client.check_password(password)
        await finish_login(message)
    except PasswordHashInvalid:
        await message.reply_text(
            f"<blockquote>{fraktur('Invalid Password')} ❞\n\n"
            f"{small_caps('ᴛʜᴇ 𝟸ꜰᴀ ᴘᴀѕѕᴡᴏʀᴅ ɪѕ ɪɴᴠᴀʟɪᴅ. ᴘʟᴇᴀѕᴇ ᴛʀʏ ᴀɢᴀɪɴ.')}</blockquote>"
        )
    except Exception as err:
        await message.reply_text(
            f"<blockquote>{fraktur('Verification Error')} ❞\n\n"
            f"<code>{str(err)}</code></blockquote>"
        )

async def finish_login(message: Message):
    session_string = await state.client.export_session_string()
    
    # Save locally
    Config.SESSION_STRING = session_string
    
    def update_env():
        env_file = ".env"
        if os.path.exists(env_file):
            try:
                with open(env_file, "r") as f:
                    lines = f.readlines()
                
                with open(env_file, "w") as f:
                    found = False
                    for line in lines:
                        if line.startswith("SESSION_STRING="):
                            f.write(f"SESSION_STRING={session_string}\n")
                            found = True
                        else:
                            f.write(line)
                    if not found:
                        f.write(f"SESSION_STRING={session_string}\n")
            except Exception as file_err:
                print(f"Failed to update .env: {file_err}")
                
    await asyncio.to_thread(update_env)
            
    try:
        # Disconnect temporary client
        try:
            await state.client.disconnect()
        except:
            pass
            
        state.client = None
        state.phone_number = None
        state.phone_code_hash = None
        
        # Stop existing instances if running
        try:
            await music.pytgcalls.stop()
        except:
            pass
        try:
            await music.userbot.disconnect()
        except:
            pass
            
        # Reconnect with new session by creating a new Client and PyTgCalls instance
        music.userbot = Client(
            "MusicUserbot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            session_string=session_string
        )
        await music.userbot.start()
        
        from pytgcalls import PyTgCalls
        music.pytgcalls = PyTgCalls(music.userbot)
        music.init_handlers(music.pytgcalls)
        await music.pytgcalls.start()
        
        music.userbot_connected = True
        
        from helpers.utils import sync_served_chats_from_userbot
        asyncio.create_task(sync_served_chats_from_userbot(music.userbot))
        
        await message.reply_text(
            f"<blockquote>{fraktur('Authentication Successful')} ❞\n\n"
            f"{small_caps('ѕᴇѕѕɪᴏɴ ѕᴛʀɪɴɢ ʜᴀѕ ʙᴇᴇɴ ᴜᴘᴅᴀᴛᴇᴅ ᴀɴᴅ ᴠᴏɪᴄᴇ ᴄʟɪᴇɴᴛ ѕᴛᴀʀᴛᴇᴅ.')}\n\n"
            f"<b>{small_caps('ᴄᴏᴘʏ ᴛʜɪѕ ѕᴇѕѕɪᴏɴ ѕᴛʀɪɴɢ ᴀɴᴅ ᴀᴅᴅ ɪᴛ ᴛᴏ ʏᴏᴜʀ ʀᴀɪʟᴡᴀʏ ᴅᴀѕʜʙᴏᴀʀᴅ ᴀѕ')} <code>SESSION_STRING</code>:</b>\n\n"
            f"<code>{session_string}</code></blockquote>"
        )
    except Exception as start_err:
        music.userbot_connected = False
        await message.reply_text(
            f"<blockquote>{fraktur('Startup Failed')} ❞\n\n"
            f"{small_caps('ѕᴇѕѕɪᴏɴ ѕᴀᴠᴇᴅ, ʙᴜᴛ ᴜѕᴇʀʙᴏᴛ ꜰᴀɪʟᴇᴅ ᴛᴏ ѕᴛᴀʀᴛ:')}\n"
            f"<code>{str(start_err)}</code></blockquote>"
        )
