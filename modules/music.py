from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatPrivileges
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, Update, StreamEnded, AudioQuality, VideoQuality
import os
import time
import asyncio
import random
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from helpers.styling import small_caps, fraktur, spaced_text
from config import Config
from database.db import db
from helpers.filters import admin, check_admin
from helpers.utils import animator
from services.yt_service import (
    get_stream_info, is_playlist,
    get_video_id, YoutubeDL, extract_from_cobalt, 
    extract_from_piped, extract_from_invidious, is_stream_url_alive,
    proxy_googlevideo_url
)
from services.vc_service import ensure_admin_sync

# To be initialized in main.py
pytgcalls: PyTgCalls = None
userbot: Client = None
bot: Client = None
userbot_connected = False
executor = ThreadPoolExecutor(max_workers=5)
sys_random = random.SystemRandom()

# Queue and Auto-Leave Management
queues = {} 
auto_leave_tasks = {} 
user_cooldowns = {}

async def get_stream_info_cached(query, is_video=False):
    cached = await db.get_cached_stream(query, is_video)
    if cached:
        return cached
    info = await get_stream_info(query, is_video)
    if info:
        await db.set_cached_stream(query, info)
    return info

def create_media_stream(track: dict) -> MediaStream:
    kwargs = {
        "audio_parameters": AudioQuality.MEDIUM,
        "ffmpeg_parameters": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    }
    if track.get("is_video"):
        kwargs["video_parameters"] = VideoQuality.SD_360p
    else:
        kwargs["video_flags"] = MediaStream.Flags.IGNORE
        
    url = track["url"]
    audio_path = track.get("audio_url")
    
    # Proxy direct googlevideo links through a working Invidious instance
    if url and "googlevideo.com" in url:
        url = proxy_googlevideo_url(url)
    if audio_path and "googlevideo.com" in audio_path:
        audio_path = proxy_googlevideo_url(audio_path)
        
    return MediaStream(
        url,
        audio_path=audio_path,
        **kwargs
    )

async def leave_timer(chat_id, group_name):
    await asyncio.sleep(30)
    if chat_id in queues and not queues[chat_id]:
        try:
            await pytgcalls.leave_call(chat_id)
            queues.pop(chat_id, None)
            auto_leave_tasks.pop(chat_id, None)
            await userbot.send_message(
                chat_id,
                f"» {small_caps('ɴᴏ ᴍᴏʀᴇ Qᴜᴇᴜᴇᴅ ᴛʀᴀᴄᴋꜱ, ʟᴇᴀᴠɪɴɢ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ')}."
            )
        except:
            pass

async def handle_error(chat_id, e):
    error_str = str(e)
    error_lower = error_str.lower()
    
    if "chat_admin_required" in error_lower or "USER_ADMIN_INVALID" in error_str:
        header = fraktur("Admin Rights Required")
        body = "ᴛʜᴇ ʙᴏᴛ ɴᴇᴇᴅѕ ᴛᴏ ʙᴇ ᴘʀᴏᴍᴏᴛᴇᴅ ᴛᴏ ᴀᴅᴍɪɴɪѕᴛʀᴀᴛᴏʀ ᴡɪᴛʜ ᴛʜᴇ 'ɪɴᴠɪᴛᴇ ᴜѕᴇʀѕ' ᴘᴇʀᴍɪѕѕɪᴏɴ ᴛᴏ ᴀᴅᴅ ᴛʜᴇ ᴜѕᴇʀʙᴏᴛ ᴛᴏ ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ."
    elif "voice_chat_not_started" in error_lower or "no_active_group_call" in error_lower:
        header = fraktur("Voice Chat Offline")
        body = "ᴀɴ ᴀᴅᴍɪɴɪѕᴛʀᴀᴛᴏʀ ᴍᴜѕᴛ ѕᴛᴀʀᴛ ᴛʜᴇ ɢʀᴏᴜᴘ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ʙᴇꜰᴏʀᴇ ᴛʜᴇ ʙᴏᴛ ᴄᴀɴ ѕᴛʀᴇᴀᴍ ᴍᴜѕɪᴄ ᴏʀ ᴠɪᴅᴇᴏ."
    elif "auth_key_duplicated" in error_lower:
        header = fraktur("Session Conflict")
        body = "ᴛʜᴇ ᴜѕᴇʀʙᴏᴛ ѕᴇѕѕɪᴏɴ ɪѕ ᴀᴄᴛɪᴠᴇ ᴇʟѕᴇᴡʜᴇʀᴇ. ᴘʟᴇᴀѕᴇ ᴇɴѕᴜʀᴇ ɴᴏ ᴅᴜᴘʟɪᴄᴀᴛᴇ ɪɴѕᴛᴀɴᴄᴇѕ ᴏꜰ ᴛʜᴇ ʙᴏᴛ ᴀʀᴇ ʀᴜɴɴɪɴɢ."
    elif "flood_wait" in error_lower:
        header = fraktur("Flood Limit")
        body = "ᴛᴇʟᴇɢʀᴀᴍ ʀᴀᴛᴇ-ʟɪᴍɪᴛ ᴇɴꜰᴏʀᴄᴇᴅ. ᴘʟᴇᴀѕᴇ ᴡᴀɪᴛ ᴀ ꜰᴇᴡ ᴍɪɴᴜᴛᴇѕ ʙᴇꜰᴏʀᴇ ᴛʀʏɪɴɢ ᴀɢᴀɪɴ."
    elif "invite_hash_expired" in error_lower or "invite_hash_invalid" in error_lower:
        header = fraktur("Invite Link Invalid")
        body = "ᴛʜᴇ ᴄʜᴀᴛ ɪɴᴠɪᴛᴇ ʟɪɴᴋ ɪѕ ᴇxᴘɪʀᴇᴅ ᴏʀ ɪɴᴠᴀʟɪᴅ. ᴘʟᴇᴀѕᴇ ᴍᴀᴋᴇ ѕᴜʀᴇ ᴛʜᴇ ʙᴏᴛ ᴄᴀɴ ɪɴᴠɪᴛᴇ ᴜѕᴇʀѕ."
    elif "channel_private" in error_lower:
        header = fraktur("Private Chat")
        body = "ᴛʜᴇ ᴜѕᴇʀʙᴏᴛ ᴄᴀɴɴᴏᴛ ᴀᴄᴄᴇѕѕ ᴛʜɪѕ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ. ᴘʟᴇᴀѕᴇ ᴀᴅᴅ ᴛʜᴇ ᴜѕᴇʀʙᴏᴛ ᴀᴄᴄᴏᴜɴᴛ ᴍᴀɴᴜᴀʟʟʏ."
    elif "user_already_participant" in error_lower:
        header = fraktur("Userbot Connected")
        body = "ᴛʜᴇ ᴜѕᴇʀʙᴏᴛ ɪѕ ᴀʟʀᴇᴀᴅʏ ᴀ ᴍᴇᴍʙᴇʀ ᴏꜰ ᴛʜɪѕ ᴄʜᴀᴛ."
    elif "video_not_found" in error_lower or "format is not available" in error_lower:
        header = fraktur("Format Error")
        body = "ᴛʜᴇ ʀᴇQᴜᴇѕᴛᴇᴅ ᴍᴇᴅɪᴀ ꜰᴏʀᴍᴀᴛ ɪѕ ɴᴏᴛ ᴀᴠᴀɪʟᴀʙʟᴇ."
    elif "sign in to confirm" in error_lower or ("confirm" in error_lower and "not a bot" in error_lower):
        header = fraktur("Youtube Blocked")
        body = "ʏᴏᴜᴛᴜʙᴇ ɪѕ ʙʟᴏᴄᴋɪɴɢ ᴛʜᴇ ʀᴇQᴜᴇѕᴛ. ᴛʀʏ ᴘʟᴀʏɪɴɢ ѕᴏᴍᴇᴛʜɪɴɢ ᴇʟѕᴇ ᴏʀ ʀᴇꜰʀᴇѕʜ ᴄᴏᴏᴋɪᴇѕ."
    else:
        header = fraktur("Unexpected Error")
        body = f"ᴀɴ ᴜɴᴋɴᴏᴡɴ ɪѕѕᴜᴇ ᴏᴄᴄᴜʀʀᴇᴅ: {error_str[:120]}"
    return f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>"

async def play_logic(client: Client, message: Message, is_video=True):
    if not userbot or not userbot.is_connected:
        header = fraktur("Userbot Offline")
        body = "ᴛʜᴇ ᴜѕᴇʀʙᴏᴛ ɪѕ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ. ᴘʟᴇᴀѕᴇ ᴀѕᴋ ᴛʜᴇ ᴏᴡɴᴇʀ ᴛᴏ ʟᴏɢ ɪɴ ᴜѕɪɴɢ /ʟᴏɢɪɴ."
        return await client.send_message(message.chat.id, f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")

    if len(message.command) < 2:
        header = fraktur("Usage Instruction")
        body = f"ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ʟɪɴᴋ ᴏʀ ᴀ ꜱᴏɴɢ ɴᴀᴍᴇ.\nᴜꜱᴀɢᴇ: /ᴠᴘʟᴀʏ <ɴᴀᴍᴇ/ʟɪɴᴋ>"
        return await client.send_message(message.chat.id, f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")

    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None
    
    # Rate Limiting (5 seconds)
    if user_id:
        now = time.time()
        if user_id in user_cooldowns:
            if now - user_cooldowns[user_id] < 5:
                header = fraktur("Rate Limited")
                body = "ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ ᴀ ꜰᴇᴡ ꜱᴇᴄᴏɴᴅꜱ ʙᴇꜰᴏʀᴇ ʀᴇQᴜᴇꜱᴛɪɴɢ ᴀɴᴏᴛʜᴇʀ ꜱᴏɴɢ."
                return await client.send_message(chat_id, f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")
        user_cooldowns[user_id] = now

    if user_id:
        sudoers_list = await db.get_sudoers()
        is_sudoer = (user_id == Config.OWNER_ID or user_id in sudoers_list)
        if not is_sudoer:
            # Check Music Toggle
            music_toggle = await db.get_setting(f"music_{chat_id}", "on")
            if music_toggle == "off":
                is_admin_user = await check_admin(chat_id, user_id, client)
                if not is_admin_user:
                    header = fraktur("Music Disabled")
                    body = "ᴍᴜꜱɪᴄ ꜱᴛʀᴇᴀᴍɪɴɢ ʜᴀꜱ ʙᴇᴇɴ ᴅɪꜱᴀʙʟᴇᴅ ɪɴ ᴛʜɪꜱ ᴄʜᴀᴛ ʙʏ ᴀᴅᴍɪɴɪꜱᴛʀᴀᴛᴏʀꜱ."
                    return await client.send_message(chat_id, f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")

            # Check Auth Mode
            auth_mode = await db.get_setting(f"auth_{chat_id}", "off")
            if auth_mode == "on":
                is_admin_user = await check_admin(chat_id, user_id, client)
                if not is_admin_user:
                    header = fraktur("Access Denied")
                    body = "ᴀᴜᴛʜ ᴍᴏᴅᴇ ɪꜱ ᴇɴᴀʙʟᴇᴅ. ᴏɴʟʏ ᴀᴅᴍɪɴɪꜱᴛʀᴀᴛᴏʀꜱ ᴀɴᴅ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜꜱᴇʀꜱ ᴄᴀɴ ᴘʟᴀʏ ᴍᴜꜱɪᴄ."
                    return await client.send_message(chat_id, f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")

    query = message.text.split(None, 1)[1]
    
    try:
        await message.delete()
    except:
        pass

    await ensure_admin_sync(client, userbot, chat_id)
    
    is_pl = is_playlist(query)
    loading_text = "ᴘʀᴇᴘᴀʀɪɴɢ ʏᴏᴜʀ ᴘʟᴀʏʟɪꜱᴛ..." if is_pl else "ᴘʀᴇᴘᴀʀɪɴɢ ʏᴏᴜʀ ꜱᴛʀᴇᴀᴍ..."
    m = await client.send_message(chat_id, f"<blockquote>{small_caps(loading_text)}</blockquote>", parse_mode=enums.ParseMode.HTML)
    
    video_folder = "assets/THUMBNAIL VID"
    local_videos = []
    if os.path.exists(video_folder):
        local_videos = [os.path.join(video_folder, f) for f in os.listdir(video_folder) if f.endswith(".mp4")]

    try:
        try:
            user_me = await userbot.get_me()
            member = await userbot.get_chat_member(chat_id, user_me.id)
            if member.status in [enums.ChatMemberStatus.BANNED, enums.ChatMemberStatus.LEFT]:
                raise Exception("userbot_not_in_chat")
        except Exception:
            try:
                invitelink = await client.export_chat_invite_link(chat_id)
                await userbot.join_chat(invitelink)
            except Exception as join_err:
                chat = await client.get_chat(chat_id)
                if chat.username:
                    await userbot.join_chat(chat.username)
                else:
                    raise join_err

        if chat_id not in queues: queues[chat_id] = []
        if chat_id in auto_leave_tasks:
            auto_leave_tasks[chat_id].cancel()
            del auto_leave_tasks[chat_id]

        loop = asyncio.get_event_loop()
        
        if is_pl:
            ydl_opts = {
                'extract_flat': True,
                'quiet': True,
                'cookiefile': "COOKIE/Youtube_Netscape.txt" if "spotify" not in query else "COOKIE/Spotify_Netscape.txt"
            }
            proxy = get_formatted_proxy()
            if proxy:
                ydl_opts['proxy'] = proxy
            with YoutubeDL(ydl_opts) as ydl:
                # Offload blocking extraction to executor
                pl_info = await loop.run_in_executor(executor, lambda: ydl.extract_info(query, False))
                if 'entries' in pl_info:
                    entries = list(pl_info['entries'])
                    pl_tracks = []
                    for entry in entries:
                        url = entry.get('url') or entry.get('webpage_url')
                        if url:
                            track_item = {"url": url, "audio_url": None, "title": entry.get('title', 'Unknown'), "duration": "PL", "user": message.from_user.mention(style=enums.ParseMode.HTML), "is_video": is_video, "thumbnail": None, "yt_url": url}
                            queues[chat_id].append(track_item)
                            pl_tracks.append(track_item)
                    await db.add_multiple_to_queue(chat_id, pl_tracks)
                    header = fraktur("Playlist Queued")
                    body = f"ᴀᴅᴅᴇᴅ {len(entries)} ᴛʀᴀᴄᴋꜱ ᴛᴏ ᴛʜᴇ Qᴜᴇᴜᴇ.\n\nᴛʏᴘᴇ /Qᴜᴇᴜᴇ ᴛᴏ ᴠɪᴇᴡ."
                    await animator.safe_edit(client, chat_id, m.id, f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")
                else: raise Exception("No entries found in playlist.")
        else:
            info = await get_stream_info_cached(query, is_video)
            if not info:
                raise Exception("video_not_found")
            info['user'] = message.from_user.mention(style=enums.ParseMode.HTML)
            is_playing = len(queues[chat_id]) > 0
            queues[chat_id].append(info)
            await db.add_to_queue(chat_id, info)
            if is_playing:
                pos = len(queues[chat_id]) - 1
                header = small_caps('ᴀᴅᴅᴇᴅ ᴛᴏ Qᴜᴇᴜᴇ ᴀᴛ')
                queue_text = f"<blockquote>\n{header} #{pos} ❞\n</blockquote>\n" \
                             f"<blockquote>\n{small_caps('ᴛɪᴛʟᴇ')}: {info['title'][:30]} ❞\n" \
                             f"{small_caps('ᴅᴜʀᴀᴛɪᴏɴ')}: {info['duration']} {small_caps('ᴍɪɴᴜᴛᴇꜱ')}\n" \
                             f"{small_caps('ʀᴇQᴜᴇꜱᴛᴇᴅ')}: {info['user']}\n</blockquote>\n" \
                             f"<blockquote>\n{small_caps('ᴘᴏᴡᴇʀᴇᴅ')}: <a href=\"https://t.me/Sexuatic\">ꜱᴇxᴜᴀᴛɪᴄ</a> ❞\n</blockquote>"
                buttons = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(small_caps("ʟɪɴᴋ"), url="https://t.me/Sexuatic", style=enums.ButtonStyle.PRIMARY),
                        InlineKeyboardButton(small_caps("ꜱᴋɪᴘ"), callback_data="music_skip", style=enums.ButtonStyle.SUCCESS),
                        InlineKeyboardButton(small_caps("ᴄʟᴏꜱᴇ"), callback_data="close_panel", style=enums.ButtonStyle.DANGER)
                    ],
                    [InlineKeyboardButton(small_caps("ᴄʟᴏꜱᴇ ᴘᴀɴᴇʟ"), callback_data="close_panel", style=enums.ButtonStyle.DANGER)]
                ])
                try:
                    sent = False
                    if local_videos:
                        try:
                            await client.send_video(chat_id=chat_id, video=sys_random.choice(local_videos), caption=queue_text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML)
                            sent = True
                        except Exception:
                            pass
                    if not sent:
                        await client.send_message(chat_id, queue_text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
                    await m.delete()
                except Exception as e:
                    try: await m.delete()
                    except: pass
                    raise e
                return

        if len(queues[chat_id]) > 0:
            first = queues[chat_id][0]
            if first.get('duration') == "PL":
                first = await get_stream_info_cached(first['url'], is_video)
                first['user'] = message.from_user.mention(style=enums.ParseMode.HTML)
                queues[chat_id][0] = first
                await db.set_queue(chat_id, queues[chat_id])

            # Optimization: Force separate streams for high-quality AV sync
            stream = create_media_stream(first)

            try:
                await pytgcalls.play(chat_id, stream)
            except Exception as e:
                # Fallback to older pytgcalls signature if needed or handle connection error
                raise Exception(f"Failed to play stream: {str(e)}")

            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"00:00 ━━━━━━━━⬤────── {first['duration']}", callback_data="timer", style=enums.ButtonStyle.PRIMARY)],
                [
                    InlineKeyboardButton(small_caps("ᴘʀᴇᴠ"), callback_data="music_prev", style=enums.ButtonStyle.DEFAULT),
                    InlineKeyboardButton(small_caps("ᴘᴀᴜꜱᴇ"), callback_data="music_pause", style=enums.ButtonStyle.PRIMARY),
                    InlineKeyboardButton(small_caps("ꜱᴋɪᴘ"), callback_data="music_skip", style=enums.ButtonStyle.DEFAULT)
                ],
                [
                    InlineKeyboardButton(small_caps("ᴛᴜɴᴇꜱ"), url="https://t.me/AuralyxTunes", style=enums.ButtonStyle.PRIMARY),
                    InlineKeyboardButton(small_caps("ʜᴏᴍᴇ"), url="https://t.me/AuralyxHome", style=enums.ButtonStyle.PRIMARY)
                ],
                [InlineKeyboardButton(small_caps("ᴄʟᴏꜱᴇ ᴘᴀɴᴇʟ"), callback_data="close_panel", style=enums.ButtonStyle.DANGER)]
            ])
            header = fraktur("Now Playing")
            
            panel_text = f"<blockquote>\n{header} ❞\n</blockquote>\n" \
                          f"<blockquote>\n{small_caps('ᴛɪᴛʟᴇ')}: {first['title'][:30]} ❞\n" \
                          f"{small_caps('ᴅᴜʀᴀᴛɪᴏɴ')}: {first['duration']} {small_caps('ᴍɪɴᴜᴛᴇꜱ')}\n" \
                          f"{small_caps('ʀᴇQᴜᴇꜱᴛᴇᴅ')}: {first['user']}\n</blockquote>\n" \
                          f"<blockquote>\n{small_caps('ᴘᴏᴡᴇʀᴇᴅ')}: <a href=\"https://t.me/Sexuatic\">ꜱᴇxᴜᴀᴛɪᴄ</a> ❞\n</blockquote>"
            try:
                sent = False
                if local_videos:
                    try:
                        await client.send_video(chat_id=chat_id, video=sys_random.choice(local_videos), caption=panel_text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML)
                        sent = True
                    except Exception:
                        pass
                
                if not sent:
                    if first.get('thumbnail'):
                        try:
                            await client.send_photo(chat_id=chat_id, photo=first['thumbnail'], caption=panel_text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML)
                        except Exception:
                            await client.send_message(chat_id, text=panel_text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
                    else:
                        await client.send_message(chat_id, text=panel_text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
                await m.delete()
            except Exception as e:
                try: await m.delete()
                except: pass
                raise e

    except Exception as e:
        error_msg = await handle_error(chat_id, e)
        try:
            await m.edit_text(error_msg, parse_mode=enums.ParseMode.HTML)
        except Exception:
            await client.send_message(chat_id, error_msg, parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("plist") & admin)
async def playlist_command(client: Client, message: Message):
    if len(message.command) < 2:
        header = fraktur("Playlist Menu")
        body = "ᴄᴏᴍᴍᴀɴᴅꜱ:\n/ᴘʟɪꜱᴛ ᴄʀᴇᴀᴛᴇ <ɴᴀᴍᴇ>\n/ᴘʟɪꜱᴛ ᴀᴅᴅ <ɴᴀᴍᴇ> <ʟɪɴᴋ>\n/ᴘʟɪꜱᴛ ᴘʟᴀʏ <ɴᴀᴍᴇ>\n/ᴘʟɪꜱᴛ ʟɪꜱᴛ"
        return await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")
    sub = message.command[1].lower()
    user_id = message.from_user.id
    try:
        if sub == "create":
            if len(message.command) < 3: return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴘʟɪꜱᴛ ᴄʀᴇᴀᴛᴇ <ɴᴀᴍᴇ>"))
            await db.create_playlist(user_id, message.command[2])
            await message.reply_text(f"<blockquote>{fraktur('Success')} ❞\n\n{small_caps('ᴘʟᴀʏʟɪꜱᴛ ᴄʀᴇᴀᴛᴇᴅ')}</blockquote>")
        elif sub == "add":
            if len(message.command) < 4: return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴘʟɪꜱᴛ ᴀᴅᴅ <ɴᴀᴍᴇ> <ʟɪɴᴋ/Qᴜᴇʀʏ>"))
            name, query = message.command[2], message.text.split(None, 3)[3]
            search = VideosSearch(query, limit=1)
            results = search.result().get("result")
            if not results: return await message.reply_text(small_caps("ᴛʀᴀᴄᴋ ɴᴏᴛ ꜰᴏᴜɴᴅ."))
            await db.add_to_playlist(user_id, name, results[0]["title"], results[0]["link"])
            await message.reply_text(f"<blockquote>{fraktur('Added')} ❞\n\n{small_caps(results[0]['title'][:30])}</blockquote>")
        elif sub == "list":
            lists = await db.get_playlists(user_id)
            if not lists: return await message.reply_text(small_caps("ɴᴏ ᴘʟᴀʏʟɪꜱᴛꜱ ꜰᴏᴜɴᴅ."))
            body = "\n".join([f"• {small_caps(l)}" for l in lists])
            await message.reply_text(f"<blockquote>{fraktur('Your Playlists')} ❞\n\n{body}</blockquote>")
        elif sub == "play":
            if len(message.command) < 3: return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴘʟɪꜱᴛ ᴘʟᴀʏ <ɴᴀᴍᴇ>"))
            tracks = await db.get_playlist_tracks(user_id, message.command[2])
            if not tracks: return await message.reply_text(small_caps("ᴘʟᴀʏʟɪꜱᴛ ɪꜱ ᴇᴍᴘᴛʏ."))
            chat_id = message.chat.id
            if chat_id not in queues: queues[chat_id] = []
            new_tracks = [{"url": t['url'], "audio_url": None, "title": t['title'], "duration": "PL", "user": message.from_user.mention, "is_video": True, "thumbnail": None, "yt_url": t['url']} for t in tracks]
            queues[chat_id].extend(new_tracks)
            await db.add_multiple_to_queue(chat_id, new_tracks)
            await message.reply_text(f"<blockquote>{fraktur('Queued')} ❞\n\n{small_caps('ᴘʟᴀʏʟɪꜱᴛ ᴀᴅᴅᴇᴅ')}</blockquote>")
            if len(queues[chat_id]) == len(tracks): await play_logic(client, message, is_video=True)
    except Exception as e: await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("play") & filters.group)
async def play_music(client: Client, message: Message):
    await play_logic(client, message, is_video=False)

@Client.on_message(filters.command("vplay") & filters.group)
async def vplay_music(client: Client, message: Message):
    await play_logic(client, message, is_video=True)

@Client.on_message(filters.command(["cvplay", "cvp"]) & admin)
async def cvplay_command(client: Client, message: Message):
    await play_logic(client, message, is_video=True)

@Client.on_message(filters.command(["player", "pannel"]) & admin)
async def player_panel(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id not in queues or not queues[chat_id]:
        return await message.reply_text(small_caps("ɴᴏᴛʜɪɴɢ ɪꜱ ᴘʟᴀʏɪɴɢ."))
    
    first = queues[chat_id][0]
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"00:00 ━━━━━━━━⬤────── {first['duration']}", callback_data="timer", style=enums.ButtonStyle.PRIMARY)], 
        [
            InlineKeyboardButton(small_caps("ᴘʀᴇᴠ"), callback_data="music_prev", style=enums.ButtonStyle.DEFAULT), 
            InlineKeyboardButton(small_caps("ᴘᴀᴜꜱᴇ"), callback_data="music_pause", style=enums.ButtonStyle.SUCCESS), 
            InlineKeyboardButton(small_caps("ꜱᴋɪᴘ"), callback_data="music_skip", style=enums.ButtonStyle.DEFAULT)
        ], 
        [
            InlineKeyboardButton(small_caps("ᴛᴜɴᴇꜱ"), url="https://t.me/AuralyxTunes", style=enums.ButtonStyle.PRIMARY), 
            InlineKeyboardButton(small_caps("ʜᴏᴍᴇ"), url="https://t.me/AuralyxHome", style=enums.ButtonStyle.PRIMARY)
        ], 
        [InlineKeyboardButton(small_caps("ᴄʟᴏꜱᴇ ᴘᴀɴᴇʟ"), callback_data="close_panel", style=enums.ButtonStyle.DANGER)]
    ])
    header = fraktur("Player Panel")
    panel_text = f"<blockquote>\n{header} ❞\n</blockquote>\n" \
                 f"<blockquote>\n{small_caps('ᴛɪᴛʟᴇ')}: {first['title'][:30]} ❞\n" \
                 f"{small_caps('ᴅᴜʀᴀᴛɪᴏɴ')}: {first['duration']} {small_caps('ᴍɪɴᴜᴛᴇꜱ')}\n" \
                 f"{small_caps('ʀᴇQᴜᴇꜱᴛᴇᴅ')}: {first['user']}\n</blockquote>\n" \
                 f"<blockquote>\n{small_caps('ᴘᴏᴡᴇʀᴇᴅ')}: <a href=\"https://t.me/Sexuatic\">ꜱᴇxᴜᴀᴛɪᴄ</a> ❞\n</blockquote>"
    await message.reply_text(panel_text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)

@Client.on_message(filters.command(["playforce", "pf"]) & admin)
async def play_force(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id in queues: queues[chat_id] = []
    await db.clear_queue(chat_id)
    await play_logic(client, message, is_video=False)

@Client.on_message(filters.command(["vplayforce", "vpf"]) & admin)
async def vplay_force(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id in queues: queues[chat_id] = []
    await db.clear_queue(chat_id)
    await play_logic(client, message, is_video=True)

@Client.on_message(filters.command("admins") & filters.group)
async def admins_list(client: Client, message: Message):
    chat_id = message.chat.id
    try:
        admins = []
        async for m in client.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
            if not m.user.is_bot:
                admins.append(m.user.mention)
        
        if not admins:
            return await message.reply_text(small_caps("ɴᴏ ᴀᴅᴍɪɴɪꜱᴛʀᴀᴛᴏʀꜱ ꜰᴏᴜɴᴅ (ᴇxᴄʟᴜᴅɪɴɢ ʙᴏᴛꜱ)."))
        
        body = "\n".join([f"• {a}" for a in admins])
        header = fraktur("Chat Administrators")
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{body}</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{small_caps('ᴇʀʀᴏʀ')} ❞\n\n{str(e)}</blockquote>")

@Client.on_message(filters.command("settings") & admin)
async def settings_panel(client: Client, message: Message):
    chat_id = message.chat.id
    # Fetch some settings
    music_toggle = await db.get_setting(f"music_{chat_id}", "on")
    auth_mode = await db.get_setting(f"auth_{chat_id}", "off")
    
    header = fraktur("Group Settings")
    body = f"» {small_caps('ᴄʜᴀᴛ')}: {message.chat.title}\n" \
           f"» {small_caps('ᴍᴜꜱɪᴄ ᴛᴏɢɢʟᴇ')}: {music_toggle.upper()}\n" \
           f"» {small_caps('ᴀᴜᴛʜ ᴍᴏᴅᴇ')}: {auth_mode.upper()}"
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(small_caps("ᴍᴜꜱɪᴄ ᴛᴏɢɢʟᴇ"), callback_data=f"set_music_{chat_id}", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton(small_caps("ᴀᴜᴛʜ ᴍᴏᴅᴇ"), callback_data=f"set_auth_{chat_id}", style=enums.ButtonStyle.PRIMARY)
        ],
        [InlineKeyboardButton(small_caps("ᴄʟᴏꜱᴇ"), callback_data="close_panel", style=enums.ButtonStyle.DANGER)]
    ])
    
    await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                             f"<blockquote>{body}</blockquote>", reply_markup=buttons)

@Client.on_callback_query(filters.regex("^set_"))
async def settings_callbacks(client: Client, callback_query: CallbackQuery):
    data = callback_query.data.split("_")
    action, setting, chat_id = data[0], data[1], int(data[2])
    
    # Auth check
    is_admin_user = await check_admin(chat_id, callback_query.from_user.id, client)
    if not is_admin_user:
        return await callback_query.answer(small_caps("ᴀᴅᴍɪɴ ʀɪɢʜᴛꜱ ʀᴇQᴜɪʀᴇᴅ"), show_alert=True)
    
    current = await db.get_setting(f"{setting}_{chat_id}", "on" if setting == "music" else "off")
    new_val = "off" if current == "on" else "on"
    await db.set_setting(f"{setting}_{chat_id}", new_val)
    
    # Update UI
    music_toggle = await db.get_setting(f"music_{chat_id}", "on")
    auth_mode = await db.get_setting(f"auth_{chat_id}", "off")
    
    header = fraktur("Group Settings")
    body = f"» {small_caps('ᴄʜᴀᴛ')}: {callback_query.message.chat.title}\n" \
           f"» {small_caps('ᴍᴜꜱɪᴄ ᴛᴏɢɢʟᴇ')}: {music_toggle.upper()}\n" \
           f"» {small_caps('ᴀᴜᴛʜ ᴍᴏᴅᴇ')}: {auth_mode.upper()}"
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(small_caps("ᴍᴜꜱɪᴄ ᴛᴏɢɢʟᴇ"), callback_data=f"set_music_{chat_id}", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton(small_caps("ᴀᴜᴛʜ ᴍᴏᴅᴇ"), callback_data=f"set_auth_{chat_id}", style=enums.ButtonStyle.PRIMARY)
        ],
        [InlineKeyboardButton(small_caps("ᴄʟᴏꜱᴇ"), callback_data="close_panel", style=enums.ButtonStyle.DANGER)]
    ])
    
    await callback_query.edit_message_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                          f"<blockquote>{body}</blockquote>", reply_markup=buttons)
    await callback_query.answer(small_caps("ꜱᴇᴛᴛɪɴɢ ᴜᴘᴅᴀᴛᴇᴅ"))

@Client.on_message(filters.command(["queue", "q"]) & filters.group)
async def queue_command(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id not in queues or not queues[chat_id]:
        return await message.reply_text(small_caps("ᴛʜᴇ Qᴜᴇᴜᴇ ɪꜱ ᴇᴍᴘᴛʏ."))
    
    body = ""
    for i, track in enumerate(queues[chat_id]):
        if i == 0:
            body += f"» {fraktur('Now Playing')}:\n{small_caps(track['title'][:30])}\n\n"
        else:
            body += f"{i}. {small_caps(track['title'][:30])} (<b>ʀᴇQ</b>: {track['user']})\n"
    
    header = fraktur("Music Queue")
    await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                             f"<blockquote>{body}</blockquote>")

@Client.on_message(filters.command("shuffle") & admin)
async def shuffle_queue(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id not in queues or len(queues[chat_id]) < 2:
        return await message.reply_text(small_caps("ɴᴏᴛ ᴇɴᴏᴜɢʜ ᴛʀᴀᴄᴋꜱ ᴛᴏ ꜱʜᴜꜰꜰʟᴇ."))
    
    now_playing = queues[chat_id].pop(0)
    random.shuffle(queues[chat_id])
    queues[chat_id].insert(0, now_playing)
    
    await message.reply_text(small_caps("Qᴜᴇᴜᴇ ꜱʜᴜꜰꜰʟᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ."))

loops = {}

@Client.on_message(filters.command("loop") & admin)
async def loop_command(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id not in loops:
        loops[chat_id] = False
    
    loops[chat_id] = not loops[chat_id]
    status = "ᴇɴᴀʙʟᴇᴅ" if loops[chat_id] else "ᴅɪꜱᴀʙʟᴇᴅ"
    await message.reply_text(f"<blockquote>{fraktur('Loop Mode')} ❞\n\n{small_caps(status)}</blockquote>")

@Client.on_message(filters.command("volume") & admin)
async def volume_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴠᴏʟᴜᴍᴇ <1-200>"))
    
    try:
        vol = int(message.command[1])
        if not (1 <= vol <= 200):
            return await message.reply_text(small_caps("ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴠᴏʟᴜᴍᴇ ʙᴇᴛᴡᴇᴇɴ 1 ᴀɴᴅ 200."))
        
        await pytgcalls.change_volume_level(message.chat.id, vol)
        await message.reply_text(f"<blockquote>{fraktur('Volume Adjusted')} ❞\n\n{small_caps('ꜱᴇᴛ ᴛᴏ')} {vol}%</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{small_caps('ᴇʀʀᴏʀ')} ❞\n\n{str(e)}</blockquote>")

@Client.on_message(filters.command("seek") & admin)
async def seek_command(client: Client, message: Message):
    if len(message.command) < 2: return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ꜱᴇᴇᴋ <ꜱᴇᴄᴏɴᴅꜱ>"))
    try:
        seconds = int(message.command[1])
        await pytgcalls.seek_in_call(message.chat.id, seconds)
        await message.reply_text(f"<blockquote>{fraktur('Seeked')} ❞\n\n{small_caps('ᴛᴏ')} {seconds} {small_caps('ꜱᴇᴄᴏɴᴅꜱ')}</blockquote>")
    except Exception as e: await message.reply_text(str(e))

@Client.on_message(filters.command("seekback") & admin)
async def seek_back_command(client: Client, message: Message):
    if len(message.command) < 2: return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ꜱᴇᴇᴋʙᴀᴄᴋ <ꜱᴇᴄᴏɴᴅꜱ>"))
    try:
        seconds = int(message.command[1])
        await pytgcalls.seek_in_call(message.chat.id, -seconds)
        await message.reply_text(f"<blockquote>{fraktur('Seeked Back')} ❞\n\n{small_caps('ʙʏ')} {seconds} {small_caps('ꜱᴇᴄᴏɴᴅ')}</blockquote>")
    except Exception as e: await message.reply_text(str(e))

@Client.on_message(filters.command(["speed", "cspeed"]) & admin)
async def speed_command(client: Client, message: Message):
    if len(message.command) < 2: return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ꜱᴘᴇᴇᴅ <0.5-2.0>"))
    try:
        speed = float(message.command[1])
        if not (0.5 <= speed <= 2.0): return await message.reply_text(small_caps("ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ꜱᴘᴇᴇᴅ ʙᴇᴛᴡᴇᴇɴ 0.5 ᴀɴᴅ 2.0."))
        await message.reply_text(f"<blockquote>{fraktur('Playback Speed')} ❞\n\n{small_caps('ꜱᴇᴛ ᴛᴏ')} {speed}x</blockquote>")
    except Exception as e: await message.reply_text(str(e))

@Client.on_message(filters.command("song"))
async def song_download(client: Client, message: Message):
    if len(message.command) < 2: return await message.reply_text(small_caps("ᴘʀᴏᴠɪᴅᴇ ꜱᴏɴɢ ɴᴀᴍᴇ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ."))
    
    query = " ".join(message.command[1:])
    m = await message.reply_text(small_caps("ꜱᴇᴀʀᴄʜɪɴɢ..."))
    
    try:
        search = VideosSearch(query, limit=1)
        res = search.result()
        if not res or not res.get("result"): return await m.edit(small_caps("ɴᴏ ʀᴇꜱᴜʟᴛꜱ ꜰᴏᴜɴᴅ."))
        
        link = res["result"][0]["link"]
        title = res["result"][0]["title"]
        
        await m.edit(small_caps("ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ..."))
        
        # Download logic using yt-dlp
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": "downloads/%(title)s.%(ext)s",
            "quiet": True,
            "cookiefile": "COOKIE/Youtube_Netscape.txt",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }]
        }
        proxy = get_formatted_proxy()
        if proxy:
            ydl_opts['proxy'] = proxy
        
        # Ensure downloads dir exists
        if not os.path.exists("downloads"): os.makedirs("downloads")
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=True)
                raw_path = ydl.prepare_filename(info)
                file_path = os.path.splitext(raw_path)[0] + ".mp3"
        except Exception as first_dl_error:
            video_id = get_video_id(link)
            fallback_success = False
            if video_id:
                cobalt_res = extract_from_cobalt(video_id, is_video=False)
                if cobalt_res and cobalt_res.get("url") and is_stream_url_alive(cobalt_res["url"]):
                    try:
                        file_path = f"downloads/{video_id}.mp3"
                        urllib.request.urlretrieve(cobalt_res["url"], file_path)
                        fallback_success = True
                    except:
                        pass
                if not fallback_success:
                    piped_res = extract_from_piped(video_id, is_video=False)
                    if piped_res and piped_res.get("url") and is_stream_url_alive(piped_res["url"]):
                        try:
                            file_path = f"downloads/{video_id}.mp3"
                            urllib.request.urlretrieve(piped_res["url"], file_path)
                            fallback_success = True
                        except:
                            pass
                if not fallback_success:
                    invidious_res = extract_from_invidious(video_id, is_video=False)
                    if invidious_res and invidious_res.get("url") and is_stream_url_alive(invidious_res["url"]):
                        try:
                            file_path = f"downloads/{video_id}.mp3"
                            urllib.request.urlretrieve(invidious_res["url"], file_path)
                            fallback_success = True
                        except:
                            pass
            if not fallback_success:
                raise first_dl_error
            
        await m.edit(small_caps("ᴜᴘʟᴏᴀᴅɪɴɢ..."))
        await message.reply_audio(file_path, caption=f"<blockquote>{fraktur(title)} ❞</blockquote>")
        await m.delete()
        if os.path.exists(file_path): os.remove(file_path)
        
    except Exception as e: await m.edit(str(e))

@Client.on_message(filters.command(["pause", "p"]) & admin)
async def pause_command(client: Client, message: Message):
    try: await pytgcalls.pause(message.chat.id); await client.send_message(message.chat.id, f"<blockquote>{fraktur('Stream Paused')} ❞</blockquote>")
    except Exception as e: await client.send_message(message.chat.id, await handle_error(message.chat.id, e))

@Client.on_message(filters.command(["resume", "r"]) & admin)
async def resume_command(client: Client, message: Message):
    try: await pytgcalls.resume(message.chat.id); await client.send_message(message.chat.id, f"<blockquote>{fraktur('Stream Resumed')} ❞</blockquote>")
    except Exception as e: await client.send_message(message.chat.id, await handle_error(message.chat.id, e))

@Client.on_callback_query(filters.regex("^music_"))
async def music_callbacks(client: Client, callback_query: CallbackQuery):
    data, chat_id = callback_query.data.split("_")[1], callback_query.message.chat.id
    
    # Permission Check for Player Controls
    is_admin_user = await check_admin(chat_id, callback_query.from_user.id, client)
    if not is_admin_user:
        return await callback_query.answer(small_caps("ᴀᴄᴄᴇꜱꜱ ᴅᴇɴɪᴇᴅ: ᴀᴅᴍɪɴ ʀɪɢʜᴛꜱ ʀᴇQᴜɪʀᴇᴅ"), show_alert=True)

    if data == "skip":
        if chat_id not in queues or not queues[chat_id]: return await callback_query.answer(small_caps("ɴᴏᴛʜɪɴɢ ɪꜱ ᴘʟᴀʏɪɴɢ"))
        try:
            queues[chat_id].pop(0)
            await db.remove_first_track(chat_id)
            if queues[chat_id]:
                next_t = queues[chat_id][0]
                await pytgcalls.play(chat_id, create_media_stream(next_t))
                
                # Send the "Now Playing" panel
                buttons = InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"00:00 ━━━━━━━━⬤────── {next_t['duration']}", callback_data="timer", style=enums.ButtonStyle.PRIMARY)],
                    [
                        InlineKeyboardButton(small_caps("ᴘʀᴇᴠ"), callback_data="music_prev", style=enums.ButtonStyle.DEFAULT),
                        InlineKeyboardButton(small_caps("ᴘᴀᴜꜱᴇ"), callback_data="music_pause", style=enums.ButtonStyle.PRIMARY),
                        InlineKeyboardButton(small_caps("ꜱᴋɪᴘ"), callback_data="music_skip", style=enums.ButtonStyle.DEFAULT)
                    ],
                    [
                        InlineKeyboardButton(small_caps("ᴛᴜɴᴇꜱ"), url="https://t.me/AuralyxTunes", style=enums.ButtonStyle.PRIMARY),
                        InlineKeyboardButton(small_caps("ʜᴏᴍᴇ"), url="https://t.me/AuralyxHome", style=enums.ButtonStyle.PRIMARY)
                    ],
                    [InlineKeyboardButton(small_caps("ᴄʟᴏꜱᴇ ᴘᴀɴᴇʟ"), callback_data="close_panel", style=enums.ButtonStyle.DANGER)]
                ])
                header = fraktur("Now Playing")
                panel_text = f"<blockquote>\n{header} ❞\n</blockquote>\n" \
                              f"<blockquote>\n{small_caps('ᴛɪᴛʟᴇ')}: {next_t['title'][:30]} ❞\n" \
                              f"{small_caps('ᴅᴜʀᴀᴛɪᴏɴ')}: {next_t['duration']} {small_caps('ᴍɪɴᴜᴛᴇꜱ')}\n" \
                              f"{small_caps('ʀᴇQᴜᴇꜱᴛᴇᴅ')}: {next_t['user']}\n</blockquote>\n" \
                              f"<blockquote>\n{small_caps('ᴘᴏᴡᴇʀᴇᴅ')}: <a href=\"https://t.me/Sexuatic\">ꜱᴇxᴜᴀᴛɪᴄ</a> ❞\n</blockquote>"
                
                if next_t.get('thumbnail'):
                    try:
                        await client.send_photo(chat_id=chat_id, photo=next_t['thumbnail'], caption=panel_text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML)
                    except Exception:
                        await client.send_message(chat_id, text=panel_text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
                else:
                    await client.send_message(chat_id, text=panel_text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
            else:
                await pytgcalls.leave_call(chat_id)
                queues.pop(chat_id, None)
                auto_leave_tasks.pop(chat_id, None)
                await client.send_message(chat_id, f"<blockquote>{fraktur('Stream Skipped')} ❞\n\n{small_caps('ɴᴏ ᴍᴏʀᴇ ᴛʀᴀᴄᴋѕ')}</blockquote>")
        except Exception as e: await client.send_message(chat_id, f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")
    elif data == "pause":
        try: await pytgcalls.pause(chat_id); await callback_query.answer(small_caps("ᴘᴀᴜѕᴇᴅ"))
        except: await pytgcalls.resume(chat_id); await callback_query.answer(small_caps("ʀᴇѕᴜᴍᴇᴅ"))
    elif data == "stop":
        if chat_id in queues: queues[chat_id] = []
        await db.clear_queue(chat_id)
        try:
            await pytgcalls.leave_call(chat_id)
            queues.pop(chat_id, None)
            auto_leave_tasks.pop(chat_id, None)
            await client.send_message(chat_id, f"<blockquote>{fraktur('Stream Stopped')} ❞</blockquote>")
        except Exception as e: await client.send_message(chat_id, f"<blockquote>{fraktur('Error')} ❞</blockquote>")
    await callback_query.answer()

@Client.on_message(filters.command(["skip", "s", "next"]) & admin)
async def skip_music(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id not in queues or not queues[chat_id]: return await client.send_message(chat_id, f"<blockquote>{fraktur('Queue Empty')} ❞</blockquote>")
    try:
        queues[chat_id].pop(0)
        await db.remove_first_track(chat_id)
        if queues[chat_id]: 
            next_t = queues[chat_id][0]
            await pytgcalls.play(chat_id, create_media_stream(next_t))
            
            # Send the "Now Playing" panel
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"00:00 ━━━━━━━━⬤────── {next_t['duration']}", callback_data="timer", style=enums.ButtonStyle.PRIMARY)],
                [
                    InlineKeyboardButton(small_caps("ᴘʀᴇᴠ"), callback_data="music_prev", style=enums.ButtonStyle.DEFAULT),
                    InlineKeyboardButton(small_caps("ᴘᴀᴜꜱᴇ"), callback_data="music_pause", style=enums.ButtonStyle.PRIMARY),
                    InlineKeyboardButton(small_caps("ꜱᴋɪᴘ"), callback_data="music_skip", style=enums.ButtonStyle.DEFAULT)
                ],
                [
                    InlineKeyboardButton(small_caps("ᴛᴜɴᴇꜱ"), url="https://t.me/AuralyxTunes", style=enums.ButtonStyle.PRIMARY),
                    InlineKeyboardButton(small_caps("ʜᴏᴍᴇ"), url="https://t.me/AuralyxHome", style=enums.ButtonStyle.PRIMARY)
                ],
                [InlineKeyboardButton(small_caps("ᴄʟᴏꜱᴇ ᴘᴀɴᴇʟ"), callback_data="close_panel", style=enums.ButtonStyle.DANGER)]
            ])
            header = fraktur("Now Playing")
            panel_text = f"<blockquote>\n{header} ❞\n</blockquote>\n" \
                          f"<blockquote>\n{small_caps('ᴛɪᴛʟᴇ')}: {next_t['title'][:30]} ❞\n" \
                          f"{small_caps('ᴅᴜʀᴀᴛɪᴏɴ')}: {next_t['duration']} {small_caps('ᴍɪɴᴜᴛᴇꜱ')}\n" \
                          f"{small_caps('ʀᴇQᴜᴇꜱᴛᴇᴅ')}: {next_t['user']}\n</blockquote>\n" \
                          f"<blockquote>\n{small_caps('ᴘᴏᴡᴇʀᴇᴅ')}: <a href=\"https://t.me/Sexuatic\">ꜱᴇxᴜᴀᴛɪᴄ</a> ❞\n</blockquote>"
            
            if next_t.get('thumbnail'):
                try:
                    await client.send_photo(chat_id=chat_id, photo=next_t['thumbnail'], caption=panel_text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML)
                except Exception:
                    await client.send_message(chat_id, text=panel_text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
            else:
                await client.send_message(chat_id, text=panel_text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
        else:
            await pytgcalls.leave_call(chat_id)
            queues.pop(chat_id, None)
            auto_leave_tasks.pop(chat_id, None)
            await client.send_message(chat_id, f"<blockquote>{fraktur('Stream Skipped')} ❞\n\n{small_caps('ʟᴇᴀᴠɪɴɢ')}</blockquote>")
    except Exception as e: await client.send_message(chat_id, await handle_error(chat_id, e))

@Client.on_message(filters.command(["stop", "end", "cstop"]) & admin)
async def stop_music(client: Client, message: Message):
    if message.chat.id in queues: queues[message.chat.id] = []
    await db.clear_queue(message.chat.id)
    try:
        await pytgcalls.leave_call(message.chat.id)
        queues.pop(message.chat.id, None)
        auto_leave_tasks.pop(message.chat.id, None)
        await client.send_message(message.chat.id, f"<blockquote>{fraktur('Stream Stopped')} ❞</blockquote>")
    except Exception as e: await client.send_message(message.chat.id, await handle_error(message.chat.id, e))

@Client.on_callback_query(filters.regex("close_panel"))
async def close_callback(client: Client, callback_query: CallbackQuery): await callback_query.message.delete()

def init_handlers(pytg: PyTgCalls):
    @pytg.on_update()
    async def stream_handler(client: PyTgCalls, update: Update):
        if isinstance(update, StreamEnded):
            chat_id = update.chat_id
            if chat_id not in queues:
                return

            async def play_next_track():
                if not queues[chat_id]:
                    # Queue is empty, schedule auto-leave
                    auto_leave_tasks[chat_id] = asyncio.create_task(leave_timer(chat_id, "this group"))
                    return
                
                next_t = queues[chat_id][0]
                try:
                    await client.play(chat_id, create_media_stream(next_t))
                    
                    # Send the "Now Playing" panel
                    if bot:
                        buttons = InlineKeyboardMarkup([
                            [InlineKeyboardButton(f"00:00 ━━━━━━━━⬤────── {next_t['duration']}", callback_data="timer", style=enums.ButtonStyle.PRIMARY)],
                            [
                                InlineKeyboardButton(small_caps("ᴘʀᴇᴠ"), callback_data="music_prev", style=enums.ButtonStyle.DEFAULT),
                                InlineKeyboardButton(small_caps("ᴘᴀᴜꜱᴇ"), callback_data="music_pause", style=enums.ButtonStyle.PRIMARY),
                                InlineKeyboardButton(small_caps("ꜱᴋɪᴘ"), callback_data="music_skip", style=enums.ButtonStyle.DEFAULT)
                            ],
                            [
                                InlineKeyboardButton(small_caps("ᴛᴜɴᴇꜱ"), url="https://t.me/AuralyxTunes", style=enums.ButtonStyle.PRIMARY),
                                InlineKeyboardButton(small_caps("ʜᴏᴍᴇ"), url="https://t.me/AuralyxHome", style=enums.ButtonStyle.PRIMARY)
                            ],
                            [InlineKeyboardButton(small_caps("ᴄʟᴏꜱᴇ ᴘᴀɴᴇʟ"), callback_data="close_panel", style=enums.ButtonStyle.DANGER)]
                        ])
                        header = fraktur("Now Playing")
                        panel_text = f"<blockquote>\n{header} ❞\n</blockquote>\n" \
                                      f"<blockquote>\n{small_caps('ᴛɪᴛʟᴇ')}: {next_t['title'][:30]} ❞\n" \
                                      f"{small_caps('ᴅᴜʀᴀᴛɪᴏɴ')}: {next_t['duration']} {small_caps('ᴍɪɴᴜᴛᴇꜱ')}\n" \
                                      f"{small_caps('ʀᴇQᴜᴇꜱᴛᴇᴅ')}: {next_t['user']}\n</blockquote>\n" \
                                      f"<blockquote>\n{small_caps('ᴘᴏᴡᴇʀᴇᴅ')}: <a href=\"https://t.me/Sexuatic\">ꜱᴇxᴜᴀᴛɪᴄ</a> ❞\n</blockquote>"
                        
                        if next_t.get('thumbnail'):
                            try:
                                await bot.send_photo(chat_id=chat_id, photo=next_t['thumbnail'], caption=panel_text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML)
                            except Exception:
                                await bot.send_message(chat_id, text=panel_text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
                        else:
                            await bot.send_message(chat_id, text=panel_text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)

                except Exception as play_err:
                    print(f"Auto-play failed for track '{next_t.get('title', 'Unknown')}': {play_err}")
                    
                    # Notify group chat using the bot client
                    try:
                        if bot:
                            header = fraktur("Stream Error")
                            body = f"ᴛʜᴇ ѕᴛʀᴇᴀᴍ ʟɪɴᴋ ꜰᴏʀ <b>{next_t.get('title', 'Unknown')}</b> ɪѕ ʙʀᴏᴋᴇɴ. ѕᴋɪᴘᴘɪɴɢ..."
                            await bot.send_message(chat_id, f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")
                    except Exception as notify_err:
                        print(f"Failed to notify stream error: {notify_err}")
                    
                    # Pop the broken track and recursively try the next one
                    if queues[chat_id]:
                        queues[chat_id].pop(0)
                        await db.remove_first_track(chat_id)
                    await play_next_track()

            # Loop logic
            if chat_id in loops and loops[chat_id]:
                # If loop is enabled, don't pop, just play the same track again
                if queues[chat_id]:
                    next_t = queues[chat_id][0]
                    try:
                        await client.play(chat_id, create_media_stream(next_t))
                        return
                    except Exception:
                        # If playing the loop track fails, turn off loop and fall through to play next
                        loops[chat_id] = False

            # Pop the completed track
            if queues[chat_id]:
                queues[chat_id].pop(0)
                await db.remove_first_track(chat_id)

            await play_next_track()
