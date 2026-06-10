import os
import asyncio
import httpx
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality
from helpers.styling import small_caps, fraktur
from config import Config
from database.db import db
import modules.music as music

# Config variables from central config
API_ID = Config.API_ID
API_HASH = Config.API_HASH
BOT_TOKEN = Config.BOT_TOKEN
SESSION_STRING = Config.SESSION_STRING

# Consumet API public instances for fetching anime streams
CONSUMET_INSTANCES = [
    "https://api.consumet.org",
    "https://consumet-api-production.up.railway.app",
    "https://api-consumet.onrender.com"
]

async def fetch_hindi_anime_stream(anime_query: str, episode: str):
    """
    Placeholder for Hindi anime scraper API (like Tatakai API) or a database scraper
    that targets dual-audio MKV files.
    
    If developers use dual-audio MKV files with multiple embedded languages:
    We can pass the -map parameter in ffmpeg_parameters to switch the audio track.
    
    Example:
    ffmpeg_parameters="-map 0:v:0 -map 0:a:1"
    -map 0:v:0: selects the first video stream (default video)
    -map 0:a:1: selects the second audio stream (e.g., Hindi track if Japanese is first)
    """
    # Developers can insert Tatakai API scraper or local database lookup here.
    # For now, this acts as a placeholder and returns None to trigger the English sub/dub fallback.
    return None

async def fetch_gogoanime_stream(anime_query: str, episode: str):
    """
    Fetches direct anime stream URL (English Sub/Dub) using Consumet API (Gogoanime route).
    """
    async with httpx.AsyncClient(timeout=15) as client:
        for base in CONSUMET_INSTANCES:
            try:
                # 1. Search for the anime
                search_url = f"{base}/anime/gogoanime/{anime_query}"
                resp = await client.get(search_url)
                if resp.status_code != 200:
                    continue
                results = resp.json().get("results", [])
                if not results:
                    continue
                anime_id = results[0]["id"]
                
                # 2. Get anime details & episode list
                info_url = f"{base}/anime/gogoanime/info/{anime_id}"
                resp = await client.get(info_url)
                if resp.status_code != 200:
                    continue
                episodes = resp.json().get("episodes", [])
                
                # Find matching episode
                episode_id = None
                for ep in episodes:
                    if str(ep.get("number")) == str(episode):
                        episode_id = ep.get("id")
                        break
                
                if not episode_id:
                    # Fallback to index-based matching if numbering format differs
                    try:
                        idx = int(episode) - 1
                        if 0 <= idx < len(episodes):
                            episode_id = episodes[idx].get("id")
                    except:
                        pass
                
                if not episode_id:
                    continue
                
                # 3. Get stream link
                watch_url = f"{base}/anime/gogoanime/watch/{episode_id}"
                resp = await client.get(watch_url)
                if resp.status_code != 200:
                    continue
                sources = resp.json().get("sources", [])
                if not sources:
                    continue
                
                # Prefer 'default' or first high-quality source
                selected_url = None
                for src in sources:
                    if src.get("quality") == "default":
                        selected_url = src.get("url")
                        break
                if not selected_url:
                    selected_url = sources[0].get("url")
                
                return selected_url
            except Exception as e:
                # Silent logging to console to keep user chat clean
                print(f"Consumet fetch error on {base}: {e}")
    return None

@Client.on_message(filters.command("aplay") & filters.group)
async def anime_play_handler(client: Client, message: Message):
    chat_id = message.chat.id
    
    if not music.userbot_connected:
        header = fraktur("Userbot Offline")
        body = "ᴛʜᴇ ᴜѕᴇʀʙᴏᴛ ɪѕ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ. ᴘʟᴇᴀѕᴇ ᴀѕᴋ ᴛʜᴇ ᴏᴡɴᴇʀ ᴛᴏ ʟᴏɢ ɪɴ ᴜѕɪɴɢ /ʟᴏɢɪɴ."
        return await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")
    
    # Check permissions (admins only, or handle Toggle/Auth bypass similar to music.py)
    user_id = message.from_user.id if message.from_user else None
    if user_id:
        sudoers_list = await db.get_sudoers()
        is_sudoer = (user_id == Config.OWNER_ID or user_id in sudoers_list)
        if not is_sudoer:
            # Check admin rights
            is_admin_user = await music.check_admin(chat_id, user_id, client)
            if not is_admin_user:
                header = fraktur("Access Denied")
                body = "ᴏɴʟʏ ᴀᴅᴍɪɴɪѕᴛʀᴀᴛᴏʀѕ ᴄᴀɴ ѕᴛʀᴇᴀᴍ ᴀɴɪᴍᴇ."
                return await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")

    # Parse command arguments: /aplay [Anime Name] [Episode] [Language_Flag]
    args = message.text.split()
    if len(args) < 2:
        header = fraktur("Usage Instruction")
        body = "ᴘʟᴇᴀѕᴇ ᴘʀᴏᴠɪᴅᴇ ᴀɴ ᴀɴɪᴍᴇ ɴᴀᴍᴇ.\nᴜѕᴀɢᴇ: /ᴀᴘʟᴀʏ [ᴀɴɪᴍᴇ ɴᴀᴍᴇ] [ᴇᴘɪѕᴏᴅᴇ] [ꜰʟᴀɢ]"
        return await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")

    flag = "-en"
    if args[-1] in ["-en", "-hi"]:
        flag = args[-1]
        args = args[:-1]

    episode = "1"
    if len(args) > 1 and args[-1].isdigit():
        episode = args[-1]
        anime_query = " ".join(args[1:-1])
    else:
        anime_query = " ".join(args[1:])

    if not anime_query:
        header = fraktur("Usage Instruction")
        body = "ᴘʟᴇᴀѕᴇ ᴘʀᴏᴠɪᴅᴇ ᴀɴ ᴀɴɪᴍᴇ ɴᴀᴍᴇ.\nᴜѕᴀɢᴇ: /ᴀᴘʟᴀʏ [ᴀɴɪᴍᴇ ɴᴀᴍᴇ] [ᴇᴘɪѕᴏᴅᴇ] [ꜰʟᴀɢ]"
        return await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")

    # Initial status message
    status_msg = await message.reply_text(f"<blockquote>{small_caps('Searching for Anime...')}</blockquote>")

    # Fetch stream URL based on language flag
    stream_url = None
    if flag == "-hi":
        stream_url = await fetch_hindi_anime_stream(anime_query, episode)
        # If Hindi dub not found, log and fallback to Gogoanime (English)
        if not stream_url:
            await status_msg.edit_text(f"<blockquote>{small_caps('Hindi dub not found. Trying English stream...')}</blockquote>")
            stream_url = await fetch_gogoanime_stream(anime_query, episode)
    else:
        stream_url = await fetch_gogoanime_stream(anime_query, episode)

    if not stream_url:
        header = fraktur("Anime Not Found")
        body = f"ᴄᴏᴜʟᴅ ɴᴏᴛ ꜰɪɴᴅ ѕᴛʀᴇᴀᴍɪɴɢ ѕᴏᴜʀᴄᴇ ꜰᴏʀ: {anime_query} (ᴇᴘɪѕᴏᴅᴇ {episode})"
        return await status_msg.edit_text(f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")

    # Ensure Userbot is in the chat
    try:
        await music.userbot.get_chat(chat_id)
    except Exception:
        try:
            invitelink = await client.export_chat_invite_link(chat_id)
            await music.userbot.join_chat(invitelink)
        except Exception as join_err:
            header = fraktur("Userbot Joining Failed")
            body = "ᴜѕᴇʀʙᴏᴛ ᴄᴏᴜʟᴅ ɴᴏᴛ ᴊᴏɪɴ ᴛʜᴇ ᴄʜᴀᴛ. ᴍᴀᴋᴇ ѕᴜʀᴇ ᴛʜᴇ ʙᴏᴛ ʜᴀѕ ɪɴᴠɪᴛᴇ ᴘᴇʀᴍɪѕѕɪᴏɴѕ."
            return await status_msg.edit_text(f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")

    # Attempt to stream using PyTgCalls
    await status_msg.edit_text(f"<blockquote>{small_caps('Joining Voice Chat...')}</blockquote>")
    
    # Configure MediaStream
    ffmpeg_params = None
    if flag == "-hi":
        # Example of mapping parameter for dual-audio files if needed (maps 2nd audio track):
        # ffmpeg_params = "-map 0:v:0 -map 0:a:1"
        pass

    try:
        # Stop any active music stream in the chat first
        try:
            await music.pytgcalls.leave_call(chat_id)
        except:
            pass
            
        stream = MediaStream(
            stream_url,
            audio_parameters=AudioQuality.HIGH,
            video_parameters=VideoQuality.HD_720p,
            ffmpeg_parameters=ffmpeg_params
        )
        
        await music.pytgcalls.play(chat_id, stream)
        
        # Clear music queue to avoid conflicts
        if chat_id in music.queues:
            music.queues[chat_id] = []
            
        header = fraktur("Anime Playback")
        body = f"ɴᴏᴡ ѕᴛʀᴇᴀᴍɪɴɢ: {anime_query}\nᴇᴘɪѕᴏᴅᴇ: {episode}\nʟᴀɴɢᴜᴀɢᴇ: {small_caps('ʜɪɴᴅɪ') if flag == '-hi' else small_caps('ᴇɴɢʟɪѕʜ')}"
        await status_msg.edit_text(f"<blockquote>{header} ❞\n\n{body}</blockquote>")
        
    except Exception as e:
        error_text = await music.handle_error(chat_id, e)
        await status_msg.edit_text(error_text)
