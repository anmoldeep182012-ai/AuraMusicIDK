import aiohttp
import asyncio
import os
import re
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality
from helpers.styling import small_caps, fraktur
import modules.music as music
from config import Config
from database.db import db
from helpers.filters import admin, check_admin

# --- CONFIGURATION ---
# Consumet API Instance (Gogoanime provider)
CONSUMET_API = "https://consumet-api-production-e852.up.railway.app"

# --- MULTI-LANGUAGE DATA STRATEGY ---

async def fetch_hindi_anime_stream(anime_query, episode):
    """
    MOCK FUNCTION: Placeholder for Hindi Anime Scraper API (e.g., Tatakai API).
    This function should return a direct streaming URL for Hindi dubbed or Dual-Audio content.
    """
    # Logic for Hindi scraper goes here.
    # Targeted output: Direct .mp4 or .mkv link.
    # Example: return {"url": "https://cdn.example.com/naruto-hi-ep5.mkv", "title": f"{anime_query} - EP {episode} [Hindi Dub]"}
    return None

async def fetch_english_anime_stream(anime_query, episode_num):
    """
    Fetches English Sub/Dub streaming URLs from Consumet API (Gogoanime).
    """
    async with aiohttp.ClientSession() as session:
        # 1. Search for Anime
        search_url = f"{CONSUMET_API}/anime/gogoanime/{anime_query}"
        try:
            async with session.get(search_url) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                if not data.get("results"):
                    return None
                anime_id = data["results"][0]["id"]
                anime_title = data["results"][0]["title"]
        except Exception:
            return None

        # 2. Get Episode List
        info_url = f"{CONSUMET_API}/anime/gogoanime/info/{anime_id}"
        try:
            async with session.get(info_url) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                episodes = data.get("episodes", [])
                
                # Match episode number
                target_ep = None
                for ep in episodes:
                    if str(ep.get("number")) == str(episode_num):
                        target_ep = ep
                        break
                
                if not target_ep:
                    return None
                episode_id = target_ep["id"]
        except Exception:
            return None

        # 3. Get Streaming Links
        watch_url = f"{CONSUMET_API}/anime/gogoanime/watch/{episode_id}"
        try:
            async with session.get(watch_url) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                sources = data.get("sources", [])
                if not sources:
                    return None
                
                # Return the highest quality or first source
                # Consumet usually provides a 'default' source first
                return {
                    "url": sources[0]["url"],
                    "title": f"{anime_title} - EP {episode_num}",
                    "is_m3u8": sources[0]["url"].endswith(".m3u8")
                }
        except Exception:
            return None

# --- CORE COMMAND HANDLER ---

@Client.on_message(filters.command(["aplay", "aplay@AuralyxXMusic_Bot"]) & filters.group)
async def aplay_anime(client: Client, message: Message):
    """
    Handles the /aplay command to stream anime in Voice Chat.
    Format: /aplay [Anime Name] [Episode Number] [Flag]
    Flags: -en (Default), -hi (Hindi)
    """
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None

    # 1. Permission Validation
    if user_id:
        sudoers_list = await db.get_sudoers()
        is_sudoer = (user_id == Config.OWNER_ID or user_id in sudoers_list)
        if not is_sudoer:
            # Check Music Toggle & Auth Mode
            music_toggle = await db.get_setting(f"music_{chat_id}", "on")
            if music_toggle == "off":
                is_admin_user = await check_admin(chat_id, user_id, client)
                if not is_admin_user:
                    header = fraktur("Music Disabled")
                    body = "ᴍᴜꜱɪᴄ ꜱᴛʀᴇᴀᴍɪɴɢ ʜᴀꜱ ʙᴇᴇɴ ᴅɪꜱᴀʙʟᴇᴅ ɪɴ ᴛʜɪꜱ ᴄʜᴀᴛ."
                    return await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")

    # 2. Argument Parsing
    if len(message.command) < 2:
        header = fraktur("Usage Instruction")
        body = "ꜰᴏʀᴍᴀᴛ: /ᴀᴘʟᴀʏ [ᴀɴɪᴍᴇ ɴᴀᴍᴇ] [ᴇᴘɪꜱᴏᴅᴇ] [ꜰʟᴀɢ]\n\nꜰʟᴀɢꜱ:\n-ᴇɴ : ᴇɴɢʟɪꜱʜ ꜱᴜʙ/ᴅᴜʙ (ᴅᴇꜰᴀᴜʟᴛ)\n-ʜɪ : ʜɪɴᴅɪ ᴅᴜʙ/ᴅᴜᴀʟ ᴀᴜᴅɪᴏ\n\nᴇxᴀᴍᴘʟᴇ: /ᴀᴘʟᴀʏ ɴᴀʀᴜᴛᴏ 5 -ʜɪ"
        return await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")

    query_parts = message.command[1:]
    lang_flag = "-en"
    episode_num = "1"
    anime_name_parts = []

    for part in query_parts:
        if part.lower() in ["-en", "-hi"]:
            lang_flag = part.lower()
        elif part.isdigit():
            episode_num = part
        else:
            anime_name_parts.append(part)

    anime_name = " ".join(anime_name_parts)
    if not anime_name:
        return await message.reply_text(small_caps("ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀɴ ᴀɴɪᴍᴇ ɴᴀᴍᴇ."))

    # 3. Status Update - Searching
    status_header = fraktur("Anime Streamer")
    m = await message.reply_text(f"<blockquote>{status_header} ❞\n\n{small_caps('ꜱᴇᴀʀᴄʜɪɴɢ ꜰᴏʀ ᴀɴɪᴍᴇ...')}</blockquote>")

    # 4. Fetch Stream URL based on Language
    stream_data = None
    if lang_flag == "-hi":
        stream_data = await fetch_hindi_anime_stream(anime_name, episode_num)
        if not stream_data:
            # Fallback or error
            return await m.edit(f"<blockquote>{status_header} ❞\n\n{small_caps('ʜɪɴᴅɪ ꜱᴛʀᴇᴀᴍ ɴᴏᴛ ꜰᴏᴜɴᴅ. ᴛʀʏɪɴɢ ᴇɴɢʟɪꜱʜ...')}</blockquote>")
    
    if not stream_data:
        stream_data = await fetch_english_anime_stream(anime_name, episode_num)

    if not stream_data:
        return await m.edit(f"<blockquote>{status_header} ❞\n\n{small_caps('ᴀɴɪᴍᴇ ᴏʀ ᴇᴘɪꜱᴏᴅᴇ ɴᴏᴛ ꜰᴏᴜɴᴅ.')}</blockquote>")

    # 5. Joining Voice Chat Logic
    try:
        await music.ensure_admin_sync(client, chat_id)
        
        # Userbot Join Check
        try:
            await music.userbot.get_chat(chat_id)
        except Exception:
            invitelink = await client.export_chat_invite_link(chat_id)
            await music.userbot.join_chat(invitelink)

        await m.edit(f"<blockquote>{status_header} ❞\n\n{small_caps('ᴊᴏɪɴɪɴɢ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ...')}</blockquote>")

        # 6. Stream Preparation
        if chat_id not in music.queues: music.queues[chat_id] = []
        if chat_id in music.auto_leave_tasks:
            music.auto_leave_tasks[chat_id].cancel()
            del music.auto_leave_tasks[chat_id]

        track_info = {
            "url": stream_data["url"],
            "title": stream_data["title"],
            "duration": "Anime",
            "user": message.from_user.mention(style=enums.ParseMode.HTML),
            "is_video": True,
            "thumbnail": None
        }

        is_playing = len(music.queues[chat_id]) > 0
        music.queues[chat_id].append(track_info)

        if is_playing:
            pos = len(music.queues[chat_id]) - 1
            body = f"{small_caps('ᴀᴅᴅᴇᴅ ᴛᴏ Qᴜᴇᴜᴇ')} #{pos}\n\n" \
                   f"{small_caps('ᴛɪᴛʟᴇ')}: {track_info['title']}\n" \
                   f"{small_caps('ʀᴇQᴜᴇꜱᴛᴇᴅ')}: {track_info['user']}"
            await m.edit(f"<blockquote>{fraktur('Queued')} ❞\n\n{body}</blockquote>")
        else:
            # Create Media Stream with HD 720P settings as requested
            stream = MediaStream(
                track_info["url"],
                audio_parameters=AudioQuality.HIGH,
                video_parameters=VideoQuality.HD_720p
            )
            
            await music.pytgcalls.play(chat_id, stream)
            
            header = fraktur("Now Streaming")
            panel_text = f"<blockquote>\n{header} ❞\n</blockquote>\n" \
                          f"<blockquote>\n{small_caps('ᴛɪᴛʟᴇ')}: {track_info['title'][:40]} ❞\n" \
                          f"{small_caps('ʟᴀɴɢᴜᴀɢᴇ')}: {lang_flag.upper()[1:]}\n" \
                          f"{small_caps('ʀᴇQᴜᴇꜱᴛᴇᴅ')}: {track_info['user']}\n</blockquote>\n" \
                          f"<blockquote>\n{small_caps('ᴘᴏᴡᴇʀᴇᴅ')}: <a href=\"https://t.me/Sexuatic\">ꜱᴇxᴜᴀᴛɪᴄ</a> ❞\n</blockquote>"
            
            buttons = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(small_caps("ᴘᴀᴜꜱᴇ"), callback_data="music_pause"),
                    InlineKeyboardButton(small_caps("ꜱᴋɪᴘ"), callback_data="music_skip"),
                    InlineKeyboardButton(small_caps("ꜱᴛᴏᴘ"), callback_data="music_stop")
                ],
                [InlineKeyboardButton(small_caps("ᴄʟᴏꜱᴇ"), callback_data="close_panel")]
            ])
            
            await client.send_message(chat_id, panel_text, reply_markup=buttons, disable_web_page_preview=True)
            await m.delete()

    except Exception as e:
        error_msg = await music.handle_error(chat_id, e)
        await m.edit(error_msg)

# --- FFmpeg Audio Mapping Strategy (Comment Only) ---
"""
STRATEGY FOR DUAL-AUDIO MKV TRACK SWITCHING:
When streaming an MKV file containing multiple audio tracks via PyTgCalls:
1. Use FFmpeg to select the specific audio stream index.
2. In PyTgCalls, this is often done by passing a custom FFmpeg command or pipe.
3. Example FFmpeg flags:
   - '-map 0:v:0' (Select first video track)
   - '-map 0:a:0' (Select first audio track - usually Japanese)
   - '-map 0:a:1' (Select second audio track - usually English/Hindi)
4. Application in code:
   stream = MediaStream(
       "path_to_file.mkv",
       ffmpeg_parameters="-map 0:v:0 -map 0:a:1"
   )
"""
