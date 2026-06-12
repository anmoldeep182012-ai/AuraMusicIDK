import os
import sys
import asyncio
import aiosqlite
import shutil
import tempfile
import json
import time
from pyrogram import Client, filters, enums, raw
from pyrogram.types import Message
from helpers.filters import owner_only
from helpers.styling import small_caps, fraktur
from database.db import db
import modules.music as music

@Client.on_message(filters.command("update_ytdlp") & owner_only)
async def update_ytdlp_handler(client: Client, message: Message):
    m = await message.reply_text(small_caps("ᴜᴘᴅᴀᴛɪɴɢ ʏᴛ-ᴅʟᴘ ᴀɴᴅ ᴘʏᴛᴜʙᴇꜰɪx..."))
    try:
        import subprocess
        process = await asyncio.create_subprocess_shell(
            "pip install -U yt-dlp pytubefix",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        header = fraktur("Update Success") if process.returncode == 0 else fraktur("Update Failed")
        out = stdout.decode().strip()[-200:] or stderr.decode().strip()[-200:]
        
        await m.edit_text(
            f"<blockquote>{header} ❞\n\n"
            f"<code>{out}</code></blockquote>"
        )
    except Exception as e:
        await m.edit_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("addsudo") & owner_only)
async def add_sudo_handler(client: Client, message: Message):
    try:
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
        elif len(message.command) > 1:
            try:
                user_id = int(message.command[1])
            except ValueError:
                user = await client.get_users(message.command[1])
                user_id = user.id
        else:
            return await message.reply_text(small_caps("ᴘʟᴇᴀꜱᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀ ɪᴅ/ᴜꜱᴇʀɴᴀᴍᴇ."))

        await db.add_sudo(user_id)
        header = fraktur("Sudo Added")
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{small_caps('ᴜꜱᴇʀ ɪᴅ')}: {user_id}</blockquote>")
    except Exception as e:
        header = fraktur("Sudo Error")
        await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("delsudo") & owner_only)
async def del_sudo_handler(client: Client, message: Message):
    try:
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
        elif len(message.command) > 1:
            try:
                user_id = int(message.command[1])
            except ValueError:
                user = await client.get_users(message.command[1])
                user_id = user.id
        else:
            return await message.reply_text(small_caps("ᴘʟᴇᴀꜱᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀ ɪᴅ/ᴜꜱᴇʀɴᴀᴍᴇ."))

        await db.remove_sudo(user_id)
        header = fraktur("Sudo Removed")
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{small_caps('ᴜꜱᴇʀ ɪᴅ')}: {user_id}</blockquote>")
    except Exception as e:
        header = fraktur("Sudo Error")
        await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("sudolist") & owner_only)
async def sudo_list_handler(client: Client, message: Message):
    try:
        sudoers = await db.get_sudoers()
        if not sudoers:
            return await message.reply_text(small_caps("ɴᴏ ꜱᴜᴅᴏ ᴜꜱᴇʀ備 ꜰᴏᴜɴᴅ."))
        
        status_msg = await message.reply_text(small_caps("ꜰᴇᴛᴄʜɪɴɢ ꜱᴜᴅᴏᴇʀꜱ ᴅᴇᴛᴀɪʟꜱ..."))
        
        body = ""
        for i, user_id in enumerate(sudoers, 1):
            user = None
            # Try to fetch using bot client
            try:
                user = await client.get_users(user_id)
            except Exception:
                pass
                
            # Try userbot if bot failed or phone is missing
            if music.userbot and (not user or not getattr(user, "phone_number", None)):
                try:
                    ub_user = await music.userbot.get_users(user_id)
                    if ub_user:
                        user = ub_user
                except Exception:
                    pass
            
            if user:
                name = f"{user.first_name} {user.last_name or ''}".strip()
                username = f"@{user.username}" if user.username else "N/A"
                phone = f"+{user.phone_number}" if getattr(user, "phone_number", None) else "Hidden"
                body += f"{i}. <b>{name}</b> ({username})\n" \
                        f"   » {small_caps('ɪᴅ')}: <code>{user.id}</code>\n" \
                        f"   » {small_caps('ᴘʜᴏɴᴇ')}: <code>{phone}</code>\n\n"
            else:
                body += f"{i}. <code>{user_id}</code> ({small_caps('ᴜɴᴀʙʟᴇ ᴛᴏ ʀᴇꜱᴏʟᴠᴇ')})\n\n"
        
        header = fraktur("Sudo Users")
        await status_msg.delete()
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{body.strip()}</blockquote>")
    except Exception as e:
        header = fraktur("Sudo List Error")
        await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(str(e))}</blockquote>")


@Client.on_message(filters.command("broadcast") & owner_only)
async def broadcast_handler(client: Client, message: Message):
    if not message.reply_to_message and len(message.command) < 2:
        header = fraktur("Usage Error")
        return await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                         f"<blockquote>{small_caps('ᴘʟᴇᴀꜱᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ (ᴛᴇxᴛ, ᴍᴇᴅɪᴀ, ꜱᴛɪᴄᴋᴇʀ) ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴛᴇxᴛ ᴛᴏ ʙʀᴏᴀᴅᴄᴀꜱᴛ.')}</blockquote>")

    status_msg = await message.reply_text(small_caps("ɪɴɪᴛɪᴀᴛɪɴɢ ɢʟᴏʙᴀʟ ʙʀᴏᴀᴅᴄᴀꜱᴛ..."))

    # Fetch DB Targets
    chats = await db.get_served_chats()
    users = await db.get_served_users()
    all_targets = set(chats + users)

    # Dynamically Fetch Userbot Dialogs for max reach
    if music.userbot:
        try:
            async for dialog in music.userbot.get_dialogs():
                all_targets.add(dialog.chat.id)
        except Exception as e:
            print(f"Dialog Fetch Error: {e}")

    all_targets = list(all_targets)
    sent = 0
    failed = 0

    for chat_id in all_targets:
        try:
            # Broadcast utilizing copy to support all media types or send_message for direct text
            if message.reply_to_message:
                await message.reply_to_message.copy(chat_id)
            else:
                broadcast_text = message.text.split(None, 1)[1]
                await client.send_message(chat_id, broadcast_text)
            sent += 1
        except Exception:
            # Fallback to Userbot
            try:
                if music.userbot:
                    if message.reply_to_message:
                        await music.userbot.copy_message(chat_id, message.chat.id, message.reply_to_message.id)
                    else:
                        broadcast_text = message.text.split(None, 1)[1]
                        await music.userbot.send_message(chat_id, broadcast_text)
                    sent += 1
                else:
                    failed += 1
            except:
                failed += 1

        # Periodic update
        if (sent + failed) % 15 == 0:
            try:
                await status_msg.edit_text(f"<blockquote>{fraktur('Broadcast in Progress')} ❞</blockquote>\n" \
                                           f"<blockquote>{small_caps('**ꜱᴇɴᴛ**')}: {sent}\n" \
                                           f"{small_caps('**ꜰᴀɪʟᴇᴅ**')}: {failed}</blockquote>")
            except:
                pass

        await asyncio.sleep(0.1) # Controlled rate

    header = fraktur("Broadcast Completed")
    await status_msg.edit_text(f"<blockquote>{header} ❞</blockquote>\n" \
                               f"<blockquote>{small_caps('ᴛᴏᴛᴀʟ ꜱᴜᴄᴄᴇꜱꜱ')}: {sent}\n" \
                               f"{small_caps('ᴛᴏᴛᴀʟ ꜰᴀɪʟᴜʀᴇꜱ')}: {failed}</blockquote>")

@Client.on_message(filters.command("dbsync") & owner_only)
async def dbsync_handler(client: Client, message: Message):
    if not music.userbot or not music.userbot.is_connected:
        header = fraktur("Sync Error")
        return await message.reply_text(
            f"<blockquote>{header} ❞\n\n"
            f"{small_caps('ᴜѕᴇʀʙᴏᴛ ɪѕ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ. ᴘʟᴇᴀѕᴇ ʟᴏɢɪɴ ꜰɪʀѕᴛ.')}</blockquote>"
        )
        
    status_msg = await message.reply_text(small_caps("ѕʏɴᴄɪɴɢ ᴅᴀᴛᴀʙᴀѕᴇ ᴡɪᴛʜ ᴜѕᴇʀʙᴏᴛ ᴅɪᴀʟᴏɢѕ..."))
    
    try:
        from helpers.utils import sync_served_chats_from_userbot
        await sync_served_chats_from_userbot(music.userbot)
        
        chats_count = len(await db.get_served_chats())
        users_count = len(await db.get_served_users())
        
        header = fraktur("Sync Completed")
        await status_msg.edit_text(
            f"<blockquote>{header} ❞\n\n"
            f"{small_caps('ᴅᴀᴛᴀʙᴀѕᴇ ʜᴀѕ ʙᴇᴇɴ ѕʏɴᴄᴇᴅ.')}\n\n"
            f"» {small_caps('ᴛᴏᴛᴀʟ ᴄʜᴀᴛѕ')}: {chats_count}\n"
            f"» {small_caps('ᴛᴏᴛᴀʟ ᴜѕᴇʀѕ')}: {users_count}</blockquote>"
        )
    except Exception as e:
        header = fraktur("Sync Failed")
        await status_msg.edit_text(
            f"<blockquote>{header} ❞\n\n"
            f"<code>{str(e)}</code></blockquote>"
        )

@Client.on_message(filters.command("restart") & owner_only)
async def restart_handler(client: Client, message: Message):
    await message.reply_text(small_caps("ʀᴇꜱᴛᴀʀᴛɪɴɢ ʙᴏᴛ..."))
    os.execv(sys.executable, ['python'] + sys.argv)

@Client.on_message(filters.command("logs") & owner_only)
async def logs_handler(client: Client, message: Message):
    # Search for log file in workspace or task folders
    if os.path.exists("logs/bot.log"):
        await message.reply_document("logs/bot.log", caption=small_caps("ꜱʏꜱᴛᴇᴍ ʟᴏɢꜱ"))
    else:
        await message.reply_text(small_caps("ʟᴏɢ ꜰɪʟᴇ ɴᴏᴛ ꜰᴏᴜɴᴅ."))

@Client.on_message(filters.command("o_stats") & owner_only)
async def stats_handler(client: Client, message: Message):
    chats = len(await db.get_served_chats())
    users = len(await db.get_served_users())
    sudoers = len(await db.get_sudoers())
    
    header = fraktur("System Statistics")
    body = f"» {small_caps('ᴛᴏᴛᴀʟ ᴄʜᴀᴛꜱ')}: {chats}\n" \
           f"» {small_caps('ᴛᴏᴛᴀʟ ᴜꜱᴇʀꜱ')}: {users}\n" \
           f"» {small_caps('ꜱᴜᴅᴏ ᴜꜱᴇʀꜱ')}: {sudoers}"
    
    await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                             f"<blockquote>{body}</blockquote>")

@Client.on_message(filters.command("o_forceleave") & owner_only)
async def force_leave_handler(client: Client, message: Message):
    count = 0
    for chat_id in list(music.queues.keys()):
        try:
            await music.pytgcalls.leave_call(chat_id)
            music.queues[chat_id] = []
            count += 1
        except:
            pass
    await message.reply_text(f"<blockquote>{fraktur('Force Leave')} ❞\n\n{small_caps('ʟᴇꜰᴛ')} {count} {small_caps('ᴠᴏɪᴄᴇ ᴄʜᴀᴛꜱ')}</blockquote>")

@Client.on_message(filters.command("o_shadowban") & owner_only)
async def shadowban_handler(client: Client, message: Message):
    # Try getting user from message
    user = None
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            user = await client.get_users(message.command[1])
        except Exception:
            pass
            
    if not user: return await message.reply_text(small_caps("ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀ ɪᴅ/ᴜꜱᴇʀɴᴀᴍᴇ."))
    
    try:
        await db.set_setting(f"shadowban_{user.id}", "true")
        await message.reply_text(f"<blockquote>{fraktur('Shadowbanned')} ❞\n\n{user.mention}</blockquote>")
    except Exception as e: await message.reply_text(str(e))

@Client.on_message(filters.command("o_unshadow") & owner_only)
async def unshadow_handler(client: Client, message: Message):
    user = None
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            user = await client.get_users(message.command[1])
        except Exception:
            pass
            
    if not user: return await message.reply_text(small_caps("ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀ ɪᴅ/ᴜꜱᴇʀɴᴀᴍᴇ."))
    
    try:
        await db.set_setting(f"shadowban_{user.id}", "false")
        await message.reply_text(f"<blockquote>{fraktur('Unshadowed')} ❞\n\n{user.mention}</blockquote>")
    except Exception as e: await message.reply_text(str(e))

@Client.on_message(filters.command("o_maintenance") & owner_only)
async def maintenance_handler(client: Client, message: Message):
    if len(message.command) < 2: return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴏ_ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ <ᴏɴ|ᴏꜰꜰ>"))
    mode = message.command[1].lower()
    if mode == "on":
        await db.set_setting("maintenance", "true")
        await message.reply_text(small_caps("ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ ᴍᴏᴅᴇ ᴇɴᴀʙʟᴇᴅ."))
    else:
        await db.set_setting("maintenance", "false")
        await message.reply_text(small_caps("ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ ᴍᴏᴅᴇ ᴅɪꜱᴀʙʟᴇᴅ."))

@Client.on_message(filters.command("blacklistchat") & owner_only)
async def blacklist_chat_command(client: Client, message: Message):
    try:
        chat_id = int(message.command[1]) if len(message.command) > 1 else message.chat.id
        await db.blacklist_chat(chat_id)
        header = fraktur("Chat Blacklisted")
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{small_caps('ᴄʜᴀᴛ ɪᴅ')}: <code>{chat_id}</code></blockquote>")
    except Exception as e: await message.reply_text(str(e))

@Client.on_message(filters.command("whitelistchat") & owner_only)
async def whitelist_chat_command(client: Client, message: Message):
    try:
        chat_id = int(message.command[1]) if len(message.command) > 1 else message.chat.id
        await db.whitelist_chat(chat_id)
        header = fraktur("Chat Whitelisted")
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{small_caps('ᴄʜᴀᴛ ɪᴅ')}: <code>{chat_id}</code></blockquote>")
    except Exception as e: await message.reply_text(str(e))

@Client.on_message(filters.command("blacklistedchat") & owner_only)
async def blacklisted_chats_list(client: Client, message: Message):
    chats = await db.get_blacklisted_chats()
    if not chats: return await message.reply_text(small_caps("ɴᴏ ʙʟᴀᴄᴋʟɪꜱᴛᴇᴅ ᴄʜᴀᴛꜱ."))
    
    list_text = "\n".join([f"• <code>{c}</code>" for c in chats])
    header = fraktur("Blacklisted Chats")
    await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                             f"<blockquote>{list_text}</blockquote>")

@Client.on_message(filters.command("gban") & owner_only)
async def gban_user_command(client: Client, message: Message):
    user = None
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            user = await client.get_users(message.command[1])
        except Exception:
            pass
            
    if not user: return await message.reply_text(small_caps("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀɴᴀᴍᴇ/ɪᴅ ᴛᴏ ɢʙᴀɴ."))
    
    reason = message.text.split(None, 2)[2] if len(message.command) > 2 else "No reason provided"
    try:
        await db.gban_user(user.id, reason)
        header = fraktur("Globally Banned")
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{small_caps('ᴜꜱᴇʀ')}: {user.mention}\n" \
                                 f"{small_caps('ʀᴇᴀꜱᴏɴ')}: {reason}</blockquote>")
    except Exception as e: await message.reply_text(str(e))

@Client.on_message(filters.command("ungban") & owner_only)
async def ungban_user_command(client: Client, message: Message):
    user = None
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            user = await client.get_users(message.command[1])
        except Exception:
            pass
            
    if not user: return await message.reply_text(small_caps("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀɴᴀᴍᴇ/ɪᴅ ᴛᴏ ᴜɴɢʙᴀɴ."))
    
    try:
        await db.ungban_user(user.id)
        header = fraktur("Globally Unbanned")
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{small_caps('ᴜꜱᴇʀ')}: {user.mention}</blockquote>")
    except Exception as e: await message.reply_text(str(e))

@Client.on_message(filters.command("gbannedusers") & owner_only)
async def gbanned_users_list(client: Client, message: Message):
    users = await db.get_gbanned_users()
    if not users: return await message.reply_text(small_caps("ɴᴏ ɢʟᴏʙᴀʟʟʏ ʙᴀɴɴᴇᴅ ᴜꜱᴇʀꜱ."))
    
    body = ""
    for i, data in enumerate(users, 1):
        body += f"{i}. <code>{data['user_id']}</code> (ʀᴇᴀꜱᴏɴ: {data['reason']})\n"
            
    header = fraktur("Global Ban List")
    await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                             f"<blockquote>{body}</blockquote>")

@Client.on_message(filters.command("stats"))
async def public_stats_handler(client: Client, message: Message):
    chats = len(await db.get_served_chats())
    users = len(await db.get_served_users())
    
    header = fraktur("Overall Statistics")
    body = f"» {small_caps('ᴛᴏᴛᴀʟ ᴄʜᴀᴛꜱ')}: {chats}\n" \
           f"» {small_caps('ᴛᴏᴛᴀʟ ᴜꜱᴇʀꜱ')}: {users}"
    
    await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                             f"<blockquote>{body}</blockquote>")

async def resolve_user(client: Client, message: Message, arg_index: int = 1):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    if len(message.command) > arg_index:
        target = message.command[arg_index]
        try:
            if target.isdigit():
                return await client.get_users(int(target))
            else:
                return await client.get_users(target)
        except Exception:
            pass
    return None

async def resolve_target_and_amount(client: Client, message: Message):
    if len(message.command) < 2:
        return None, None
    try:
        amount = int(message.command[1])
    except ValueError:
        return None, None
    user = None
    if message.reply_to_message and message.reply_to_message.from_user:
        user = message.reply_to_message.from_user
    elif len(message.command) > 2:
        target = message.command[2]
        try:
            if target.isdigit():
                user = await client.get_users(int(target))
            else:
                user = await client.get_users(target)
        except Exception:
            pass
    return user, amount

@Client.on_message(filters.command("o_give") & owner_only)
async def give_coins_handler(client: Client, message: Message):
    user, amount = await resolve_target_and_amount(client, message)
    if not user or amount is None:
        # fallback: check if they replied and only provided amount
        if message.reply_to_message and message.reply_to_message.from_user and len(message.command) >= 2:
            try:
                amount = int(message.command[1])
                user = message.reply_to_message.from_user
            except ValueError:
                pass
        if not user or amount is None:
            return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴏ_ɢɪᴠᴇ <ᴀᴍᴏᴜɴᴛ> (ʀᴇᴘʟʏ ᴛᴏ ᴜꜱᴇʀ) ᴏʀ /ᴏ_ɢɪᴠᴇ <ᴀᴍᴏᴜɴᴛ> <ᴜꜱᴇʀ_ɪᴅ/ᴜꜱᴇʀɴᴀᴍᴇ>"))
    try:
        await db.update_balance(user.id, amount)
        await message.reply_text(f"<blockquote>{fraktur('Coins Added')} ❞\n\n{amount} {small_caps('ᴄᴏɪɴꜱ ɢɪᴠᴇɴ ᴛᴏ')} {user.mention}</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("o_reset") & owner_only)
async def reset_economy_handler(client: Client, message: Message):
    user = await resolve_user(client, message)
    if not user:
        return await message.reply_text(small_caps("ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀ ɪᴅ/ᴜꜱᴇʀɴᴀᴍᴇ ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴛʜᴇɪʀ ᴍᴇꜱꜱᴀɢᴇ."))
    try:
        await db._execute("UPDATE users_economy SET balance = 0, kills = 0, xp = 0, protection_until = 0 WHERE user_id = ?", user.id)
        await message.reply_text(f"<blockquote>{fraktur('Profile Wiped')} ❞\n\n{user.mention}</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("o_take") & owner_only)
async def take_coins_handler(client: Client, message: Message):
    user, amount = await resolve_target_and_amount(client, message)
    if not user or amount is None:
        if message.reply_to_message and message.reply_to_message.from_user and len(message.command) >= 2:
            try:
                amount = int(message.command[1])
                user = message.reply_to_message.from_user
            except ValueError:
                pass
        if not user or amount is None:
            return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴏ_ᴛᴀᴋᴇ <ᴀᴍᴏᴜɴᴛ> (ʀᴇᴘʟʏ ᴛᴏ ᴜꜱᴇʀ) ᴏʀ /ᴏ_ᴛᴀᴋᴇ <ᴀᴍᴏᴜɴᴛ> <ᴜꜱᴇʀ_ɪᴅ/ᴜꜱᴇʀɴᴀᴍᴇ>"))
    try:
        await db.update_balance(user.id, -amount)
        await message.reply_text(f"<blockquote>{fraktur('Coins Deducted')} ❞\n\n{amount} {small_caps('ᴄᴏɪɴꜱ ᴛᴀᴋᴇɴ ꜰʀᴏᴍ')} {user.mention}</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("o_setbal") & owner_only)
async def set_balance_handler(client: Client, message: Message):
    user, amount = await resolve_target_and_amount(client, message)
    if not user or amount is None:
        if message.reply_to_message and message.reply_to_message.from_user and len(message.command) >= 2:
            try:
                amount = int(message.command[1])
                user = message.reply_to_message.from_user
            except ValueError:
                pass
        if not user or amount is None:
            return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴏ_ꜱᴇᴛʙᴀʟ <ᴀᴍᴏᴜɴᴛ> (ʀᴇᴘʟʏ ᴛᴏ ᴜꜱᴇʀ) ᴏʀ /ᴏ_ꜱᴇᴛʙᴀʟ <ᴀᴍᴏᴜɴᴛ> <ᴜꜱᴇʀ_ɪᴅ/ᴜꜱᴇʀɴᴀᴍᴇ>"))
    try:
        await db.set_balance(user.id, amount)
        await message.reply_text(f"<blockquote>{fraktur('Balance Updated')} ❞\n\n{small_caps('ʙᴀʟᴀɴᴄᴇ ꜱᴇᴛ ᴛᴏ')} {amount} {small_caps('ᴄᴏɪɴꜱ ꜰᴏʀ')} {user.mention}</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("o_setxp") & owner_only)
async def set_xp_handler(client: Client, message: Message):
    user, amount = await resolve_target_and_amount(client, message)
    if not user or amount is None:
        if message.reply_to_message and message.reply_to_message.from_user and len(message.command) >= 2:
            try:
                amount = int(message.command[1])
                user = message.reply_to_message.from_user
            except ValueError:
                pass
        if not user or amount is None:
            return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴏ_ꜱᴇᴛxᴘ <ᴀᴍᴏᴜɴᴛ> (ʀᴇᴘʟʏ ᴛᴏ ᴜꜱᴇʀ) ᴏʀ /ᴏ_ꜱᴇᴛxᴘ <ᴀᴍᴏᴜɴᴛ> <ᴜꜱᴇʀ_ɪᴅ/ᴜꜱᴇʀɴᴀᴍᴇ>"))
    try:
        await db.set_xp(user.id, amount)
        await message.reply_text(f"<blockquote>{fraktur('XP Updated')} ❞\n\n{small_caps('xᴘ ꜱᴇᴛ ᴛᴏ')} {amount} ꜰᴏʀ {user.mention}</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("o_setkills") & owner_only)
async def set_kills_handler(client: Client, message: Message):
    user, amount = await resolve_target_and_amount(client, message)
    if not user or amount is None:
        if message.reply_to_message and message.reply_to_message.from_user and len(message.command) >= 2:
            try:
                amount = int(message.command[1])
                user = message.reply_to_message.from_user
            except ValueError:
                pass
        if not user or amount is None:
            return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴏ_ꜱᴇᴛᴋɪʟʟꜱ <ᴀᴍᴏᴜɴᴛ> (ʀᴇᴘʟʏ ᴛᴏ ᴜꜱᴇʀ) ᴏʀ /ᴏ_ꜱᴇᴛᴋɪʟʟꜱ <ᴀᴍᴏᴜɴᴛ> <ᴜꜱᴇʀ_ɪᴅ/ᴜꜱᴇʀɴᴀᴍᴇ>"))
    try:
        await db.set_kills(user.id, amount)
        await message.reply_text(f"<blockquote>{fraktur('Kills Updated')} ❞\n\n{small_caps('ᴋɪʟʟꜱ ꜱᴇᴛ ᴛᴏ')} {amount} ꜰᴏʀ {user.mention}</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("o_addpremium") & owner_only)
async def add_premium_handler(client: Client, message: Message):
    user = await resolve_user(client, message)
    if not user:
        return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴏ_ᴀᴅᴅᴘʀᴇᴍɪᴜᴍ (ʀᴇᴘʟʏ ᴛᴏ ᴜꜱᴇʀ) ᴏʀ /ᴏ_ᴀᴅᴅᴘʀᴇᴍɪᴜᴍ <ᴜꜱᴇʀ_ɪᴅ/ᴜꜱᴇʀɴᴀᴍᴇ>"))
    try:
        await db.set_premium(user.id, True)
        await message.reply_text(f"<blockquote>{fraktur('Premium Granted')} ❞\n\n{user.mention} {small_caps('ɪꜱ ɴᴏᴡ ᴀ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀ')}</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("o_delpremium") & owner_only)
async def del_premium_handler(client: Client, message: Message):
    user = await resolve_user(client, message)
    if not user:
        return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴏ_ᴅᴇʟᴘʀᴇᴍɪᴜᴍ (ʀᴇᴘʟʏ ᴛᴏ ᴜꜱᴇʀ) ᴏʀ /ᴏ_ᴅᴇʟᴘʀᴇᴍɪᴜᴍ <ᴜꜱᴇʀ_ɪᴅ/ᴜꜱᴇʀɴᴀᴍᴇ>"))
    try:
        await db.set_premium(user.id, False)
        await message.reply_text(f"<blockquote>{fraktur('Premium Revoked')} ❞\n\n{user.mention} {small_caps('ᴘʀᴇᴍɪᴜᴍ ꜱᴛᴀᴛᴜꜱ ʀᴇᴍᴏᴠᴇᴅ')}</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("o_activecalls") & owner_only)
async def active_calls_handler(client: Client, message: Message):
    try:
        active = []
        for chat_id, queue in list(music.queues.items()):
            if queue:
                try:
                    chat = await client.get_chat(chat_id)
                    title = chat.title
                except Exception:
                    title = "Unknown Chat"
                active.append(f"• <code>{chat_id}</code> - {title} ({len(queue)} {small_caps('ᴛʀᴀᴄᴋꜱ')})")
        if not active:
            return await message.reply_text(small_caps("ɴᴏ ᴀᴄᴛɪᴠᴇ ꜱᴛʀᴇᴀᴍꜱ ᴀᴛ ᴛʜᴇ ᴍᴏᴍᴇɴᴛ."))
        header = fraktur("Active Call Streams")
        body = "\n".join(active)
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{body}</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("o_cleanqueue") & owner_only)
async def clean_queue_handler(client: Client, message: Message):
    chat_id = message.chat.id
    if len(message.command) > 1:
        try:
            chat_id = int(message.command[1])
        except ValueError:
            return await message.reply_text(small_caps("ɪɴᴠᴀʟɪᴅ ᴄʜᴀᴛ ɪᴅ."))
    try:
        if chat_id in music.queues:
            music.queues[chat_id] = []
        try:
            await music.pytgcalls.leave_call(chat_id)
        except Exception:
            pass
        if chat_id in music.auto_leave_tasks:
            try:
                music.auto_leave_tasks[chat_id].cancel()
                del music.auto_leave_tasks[chat_id]
            except Exception:
                pass
        await message.reply_text(f"<blockquote>{fraktur('Queue Cleared')} ❞\n\n{small_caps('Qᴜᴇᴜᴇ ᴄʟᴇᴀʀᴇᴅ ᴀɴᴅ ʟᴇꜰᴛ ᴄᴀʟʟ ꜰᴏʀ')} <code>{chat_id}</code></blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("o_chats") & owner_only)
async def chats_list_handler(client: Client, message: Message):
    status_msg = await message.reply_text(small_caps("ꜰᴇᴛᴄʜɪɴɢ ᴄʜᴀᴛꜱ..."))
    try:
        groups = []
        if music.userbot:
            async for dialog in music.userbot.get_dialogs():
                chat = dialog.chat
                if chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL]:
                    count = chat.members_count
                    if count is None:
                        try:
                            count = await music.userbot.get_chat_members_count(chat.id)
                        except Exception:
                            try:
                                count = await client.get_chat_members_count(chat.id)
                            except Exception:
                                count = 0
                    groups.append(f"• {chat.title} (<code>{chat.id}</code>) - {count} {small_caps('ᴍᴇᴍʙᴇʀꜱ')}")
        else:
            async for dialog in client.get_dialogs():
                chat = dialog.chat
                if chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL]:
                    count = chat.members_count
                    if count is None:
                        try:
                            count = await client.get_chat_members_count(chat.id)
                        except Exception:
                            count = 0
                    groups.append(f"• {chat.title} (<code>{chat.id}</code>) - {count} {small_caps('ᴍᴇᴍʙᴇʀꜱ')}")
        if not groups:
            return await status_msg.edit_text(small_caps("ᴛʜᴇ ʙᴏᴛ ɪꜱ ɴᴏᴛ ɪɴ ᴀɴʏ ɢʀᴏᴜᴘꜱ/ᴄʜᴀɴɴᴇʟꜱ."))
        header = fraktur("Bot Served Chats")
        body = "\n".join(groups[:50])
        if len(groups) > 50:
            body += f"\n\n... ᴀɴᴅ {len(groups) - 50} ᴍᴏʀᴇ ᴄʜᴀᴛꜱ."
        await status_msg.edit_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                   f"<blockquote>{body}</blockquote>")
    except Exception as e:
        await status_msg.edit_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("o_leave") & owner_only)
async def leave_chat_handler(client: Client, message: Message):
    chat_id = message.chat.id
    if len(message.command) > 1:
        try:
            chat_id = int(message.command[1])
        except ValueError:
            return await message.reply_text(small_caps("ɪɴᴠᴀʟɪᴅ ᴄʜᴀᴛ ɪᴅ."))
    try:
        if chat_id in music.queues:
            music.queues[chat_id] = []
        try:
            await music.pytgcalls.leave_call(chat_id)
        except Exception:
            pass
        await client.leave_chat(chat_id)
        if music.userbot:
            try:
                await music.userbot.leave_chat(chat_id)
            except Exception:
                pass
        await message.reply_text(f"<blockquote>{fraktur('Left Chat')} ❞\n\n{small_caps('ʙᴏᴛ ᴀɴᴅ ᴜꜱᴇʀʙᴏᴛ ʟᴇꜰᴛ')} <code>{chat_id}</code></blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("o_join") & owner_only)
async def join_chat_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴏ_ᴊᴏɪɴ <ɪɴᴠɪᴛᴇ_ʟɪɴᴋ/ᴜꜱᴇʀɴᴀᴍᴇ>"))
    link = message.command[1]
    try:
        userbot_success = False
        if music.userbot:
            try:
                await music.userbot.join_chat(link)
                userbot_success = True
            except Exception as e:
                userbot_success = f"Failed: {str(e)}"
        bot_success = False
        try:
            await client.join_chat(link)
            bot_success = True
        except Exception as e:
            bot_success = f"Failed: {str(e)}"
        status_text = f"• {small_caps('ʙᴏᴛ')}: {'SUCCESS' if bot_success is True else bot_success}\n" \
                      f"• {small_caps('ᴜꜱᴇʀʙᴏᴛ')}: {'SUCCESS' if userbot_success is True else userbot_success}"
        await message.reply_text(f"<blockquote>{fraktur('Join Request')} ❞</blockquote>\n" \
                                 f"<blockquote>{status_text}</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("o_setname") & owner_only)
async def set_bot_name_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴏ_ꜱᴇᴛɴᴀᴍᴇ <ɴᴇᴡ_ɴᴀᴍᴇ>"))
    name = message.text.split(None, 1)[1]
    try:
        await client.invoke(
            raw.functions.bots.SetBotInfo(
                lang_code="",
                name=name
            )
        )
        try:
            await client.update_profile(first_name=name)
        except Exception:
            pass
        await message.reply_text(f"<blockquote>{fraktur('Name Updated')} ❞\n\n{small_caps('ꜱᴇᴛ ᴛᴏ')}: {name}</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("o_setbio") & owner_only)
async def set_bot_bio_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴏ_ꜱᴇᴛʙɪᴏ <ɴᴇᴡ_ʙɪᴏ>"))
    bio = message.text.split(None, 1)[1]
    try:
        await client.invoke(
            raw.functions.bots.SetBotInfo(
                lang_code="",
                about=bio
            )
        )
        await message.reply_text(f"<blockquote>{fraktur('Bio Updated')} ❞\n\n{small_caps('ꜱᴇᴛ ᴛᴏ')}: {bio}</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("o_setdescription") & owner_only)
async def set_bot_desc_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴏ_ꜱᴇᴛᴅᴇꜱᴄʀɪᴘᴛɪᴏɴ <ɴᴇᴡ_ᴅᴇꜱᴄʀɪᴘᴛɪᴏɴ>"))
    desc = message.text.split(None, 1)[1]
    try:
        await client.invoke(
            raw.functions.bots.SetBotInfo(
                lang_code="",
                description=desc
            )
        )
        await message.reply_text(f"<blockquote>{fraktur('Description Updated')} ❞\n\n{small_caps('ꜱᴇᴛ ᴛᴏ')}: {desc}</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("o_env") & owner_only)
async def view_env_handler(client: Client, message: Message):
    try:
        env_vars = []
        sensitive_keys = ["token", "hash", "session", "password", "secret", "database", "key"]
        for k, v in os.environ.items():
            is_sensitive = any(sk in k.lower() for sk in sensitive_keys)
            val = "[REDACTED]" if is_sensitive else v
            env_vars.append(f"• <b>{k}</b>: <code>{val}</code>")
        header = fraktur("Environment Variables")
        body = "\n".join(env_vars)
        full_text = f"<blockquote>{header} ❞</blockquote>\n<blockquote>{body}</blockquote>"
        if len(full_text) > 4096:
            file_path = "env_vars.txt"
            plain_vars = []
            for k, v in os.environ.items():
                is_sensitive = any(sk in k.lower() for sk in sensitive_keys)
                val = "[REDACTED]" if is_sensitive else v
                plain_vars.append(f"{k}: {val}")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(plain_vars))
            await message.reply_document(file_path, caption=small_caps("ᴇɴᴠɪʀᴏɴᴍᴇɴᴛ ᴠᴀʀɪᴀʙʟᴇꜱ"))
            try:
                os.remove(file_path)
            except Exception:
                pass
        else:
            await message.reply_text(full_text)
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("o_users") & owner_only)
async def unique_users_handler(client: Client, message: Message):
    try:
        served_count = len(await db.get_served_users())
        econ_rows = await db._fetch("SELECT COUNT(user_id) FROM users_economy")
        econ_count = econ_rows[0][0] if econ_rows else 0
        header = fraktur("Registered Users")
        body = f"• {small_caps('ꜱᴇʀᴠᴇᴅ ᴜꜱᴇʀꜱ')}: {served_count}\n" \
               f"• {small_caps('ᴇᴄᴏɴᴏᴍʏ ᴀᴄᴄᴏᴜɴᴛꜱ')}: {econ_count}"
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{body}</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("o_userslist") & owner_only)
async def users_list_handler(client: Client, message: Message):
    status_msg = await message.reply_text(small_caps("ꜰᴇᴛᴄʜɪɴɢ ᴜꜱᴇʀꜱ ʟɪꜱᴛ..."))
    try:
        user_ids = await db.get_served_users()
        if not user_ids:
            return await status_msg.edit_text(small_caps("ɴᴏ ꜱᴇʀᴠᴇᴅ ᴜꜱᴇʀꜱ ꜰᴏᴜɴᴅ."))
        
        resolved_users = []
        chunk_size = 100
        for i in range(0, len(user_ids), chunk_size):
            chunk = user_ids[i:i + chunk_size]
            try:
                users = await client.get_users(chunk)
                if not isinstance(users, list):
                    users = [users]
                resolved_users.extend(users)
            except Exception:
                for uid in chunk:
                    try:
                        u = await client.get_users(uid)
                        resolved_users.append(u)
                    except Exception:
                        pass
        
        user_lines = []
        resolved_ids = {u.id for u in resolved_users}
        
        for u in resolved_users:
            mention = u.mention(style=enums.ParseMode.HTML)
            username = f"@{u.username}" if u.username else "ɴᴏ ᴜꜱᴇʀɴᴀᴍᴇ"
            user_lines.append(f"• {mention} ({username}) - <code>{u.id}</code>")
            
        for uid in user_ids:
            if uid not in resolved_ids:
                user_lines.append(f"• ᴜɴᴋɴᴏᴡɴ ᴜꜱᴇʀ (ɴᴏ ᴜꜱᴇʀɴᴀᴍᴇ) - <code>{uid}</code>")
                
        header = fraktur("Bot Served Users")
        body = "\n".join(user_lines[:100])
        if len(user_lines) > 100:
            body += f"\n\n... ᴀɴᴅ {len(user_lines) - 100} ᴍᴏʀᴇ ᴜꜱᴇʀꜱ."
            
        full_text = f"<blockquote>{header} ❞</blockquote>\n<blockquote>{body}</blockquote>"
        if len(full_text) > 4096:
            file_path = "users_list.txt"
            plain_lines = []
            for u in resolved_users:
                username = f"@{u.username}" if u.username else "no_username"
                name = f"{u.first_name} {u.last_name or ''}".strip()
                plain_lines.append(f"{name} ({username}) - {u.id}")
            for uid in user_ids:
                if uid not in resolved_ids:
                    plain_lines.append(f"Unknown User - {uid}")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(plain_lines))
            await message.reply_document(file_path, caption=small_caps("ꜱᴇʀᴠᴇᴅ ᴜꜱᴇʀꜱ ʟɪꜱᴛ"))
            try:
                os.remove(file_path)
            except Exception:
                pass
            await status_msg.delete()
        else:
            await status_msg.edit_text(full_text)
    except Exception as e:
        await status_msg.edit_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("o_dbbackup") & owner_only)
async def database_backup_handler(client: Client, message: Message):
    status_msg = await message.reply_text(small_caps("ɪɴɪᴛɪᴀᴛɪɴɢ ᴅᴀᴛᴀʙᴀꜱᴇ ʙᴀᴄᴋᴜᴘ..."))
    try:
        if db.is_postgres:
            backup_data = {}
            tables = [
                "settings", "sudoers", "warns", "global_bans", 
                "served_chats", "served_users", "user_playlists", 
                "playlist_tracks", "users_economy", "daily_claims", 
                "auth_users", "blacklisted_chats", "blacklisted_users"
            ]
            for table in tables:
                try:
                    rows = await db._fetch(f"SELECT * FROM {table}")
                    backup_data[table] = [list(r) for r in rows]
                except Exception as te:
                    backup_data[table] = f"Error: {te}"
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
                json.dump(backup_data, f, indent=4)
                temp_path = f.name
            caption = f"<blockquote>{fraktur('PostgreSQL Backup')} ❞\n\n{small_caps('ᴀʟʟ ᴀᴄᴛɪᴠᴇ ᴛᴀʙʟᴇꜱ ᴅᴜᴍᴘᴇᴅ ᴛᴏ ᴊꜱᴏɴ')}</blockquote>"
            await message.reply_document(temp_path, caption=caption)
            await status_msg.delete()
            try: os.unlink(temp_path)
            except: pass
        else:
            db_file = db.db_path
            if os.path.exists(db_file):
                with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_f:
                    temp_path = temp_f.name
                shutil.copy2(db_file, temp_path)
                caption = f"<blockquote>{fraktur('SQLite Database Backup')} ❞\n\n{small_caps('<b>ꜰᴜʟʟ ᴛɢ_ʙᴏᴛ.ᴅʙ ꜰɪʟᴇ ᴜᴘʟᴏᴀᴅ</b>')}</blockquote>"
                await message.reply_document(temp_path, caption=caption)
                await status_msg.delete()
                try: os.unlink(temp_path)
                except: pass
            else:
                await status_msg.edit_text(small_caps("ꜱQʟɪᴛᴇ ᴅᴀᴛᴀʙᴀꜱᴇ ꜰɪʟᴇ ɴᴏᴛ ꜰᴏᴜɴᴅ ᴏɴ ᴅɪꜱᴋ."))
    except Exception as e:
        await status_msg.edit_text(f"<blockquote>{fraktur('Backup Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("o_cleanup") & owner_only)
async def disk_cleanup_handler(client: Client, message: Message):
    try:
        downloads_dir = "downloads"
        count = 0
        if os.path.exists(downloads_dir):
            for filename in os.listdir(downloads_dir):
                file_path = os.path.join(downloads_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                        count += 1
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        count += 1
                except Exception:
                    pass
        await message.reply_text(f"<blockquote>{fraktur('Disk Cleanup')} ❞\n\n{small_caps('ᴄʟᴇᴀʀᴇᴅ')} {count} {small_caps('ꜰɪʟᴇꜱ ꜰʀᴏᴍ ᴅᴏᴡɴʟᴏᴀᴅꜱ ᴅɪʀᴇᴄᴛᴏʀʏ')}</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("o_help") & owner_only)
async def owner_help_handler(client: Client, message: Message):
    header = fraktur("Owner Control Panel")
    body = (
        f"» {small_caps('ᴇᴄᴏɴᴏᴍʏ ᴄᴏɴᴛʀᴏʟꜱ')}\n"
        f"• <code>/o_give &lt;ᴀᴍᴏᴜɴᴛ&gt;</code> - ɢɪᴠᴇ ᴄᴏɪɴꜱ (ʀᴇᴘʟʏ/ᴜꜱᴇʀ)\n"
        f"• <code>/o_take &lt;ᴀᴍᴏᴜɴᴛ&gt;</code> - ᴛᴀᴋᴇ ᴄᴏɪɴꜱ (ʀᴇᴘʟʏ/ᴜꜱᴇʀ)\n"
        f"• <code>/o_setbal &lt;ᴀᴍᴏᴜɴᴛ&gt;</code> - ꜱᴇᴛ ʙᴀʟᴀɴᴄᴇ (ʀᴇᴘʟʏ/ᴜꜱᴇʀ)\n"
        f"• <code>/o_setxp &lt;ᴀᴍᴏᴜɴᴛ&gt;</code> - ꜱᴇᴛ xᴘ (ʀᴇᴘʟʏ/ᴜꜱᴇʀ)\n"
        f"• <code>/o_setkills &lt;ᴀᴍᴏᴜɴᴛ&gt;</code> - ꜱᴇᴛ ᴋɪʟʟꜱ (ʀᴇᴘʟʏ/ᴜꜱᴇʀ)\n"
        f"• <code>/o_reset</code> - ᴡɪᴘᴇ ᴜꜱᴇʀ ᴇᴄᴏɴᴏᴍʏ ᴘʀᴏꜰɪʟᴇ\n\n"
        
        f"» {small_caps('ᴘʀᴇᴍɪᴜᴍ & ꜱᴜᴅᴏ')}\n"
        f"• <code>/o_addpremium</code> - ᴀᴅᴅ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀ (ʀᴇᴘʟʏ/ᴜꜱᴇʀ)\n"
        f"• <code>/o_delpremium</code> - ʀᴇᴍᴏᴠᴇ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀ (ʀᴇᴘʟʏ/ᴜꜱᴇʀ)\n"
        f"• <code>/addsudo</code> - ᴘʀᴏᴍᴏᴛᴇ ᴛᴏ ꜱᴜᴅᴏ (ʀᴇᴘʟʏ/ᴜꜱᴇʀ)\n"
        f"• <code>/delsudo</code> - ᴅᴇᴍᴏᴛᴇ ꜰʀᴏᴍ ꜱᴜᴅᴏ (ʀᴇᴘʟʏ/ᴜꜱᴇʀ)\n"
        f"• <code>/sudolist</code> - ꜱʜᴏᴡ ʟɪꜱᴛ ᴏꜰ ꜱᴜᴅᴏᴇʀꜱ\n\n"
        
        f"» {small_caps('ᴄʜᴀᴛꜱ & ᴄᴀʟʟꜱ')}\n"
        f"• <code>/o_activecalls</code> - ʟɪꜱᴛ ᴀᴄᴛɪᴠᴇ ᴠᴄ ꜱᴛʀᴇᴀᴍꜱ\n"
        f"• <code>/o_cleanqueue &lt;ᴄʜᴀᴛ_ɪᴅ&gt;</code> - ᴄʟᴇᴀʀ ᴄʜᴀᴛ Qᴜᴇᴜᴇ & ꜱᴛᴏᴘ ᴠᴄ\n"
        f"• <code>/o_chats</code> - ʟɪꜱᴛ ᴀʟʟ ʙᴏᴛ-ꜱᴇʀᴠᴇᴅ ᴄʜᴀᴛꜱ\n"
        f"• <code>/o_leave &lt;ᴄʜᴀᴛ_ɪᴅ&gt;</code> - ꜰᴏʀᴄᴇ ʟᴇᴀᴠᴇ ᴄʜᴀᴛ\n"
        f"• <code>/o_join &lt;ʟɪɴᴋ&gt;</code> - ꜰᴏʀᴄᴇ ᴊᴏɪɴ ᴀ ᴄʜᴀᴛ\n\n"
        
        f"» {small_caps('ʙᴏᴛ ᴘʀᴏꜰɪʟᴇ & ᴇɴᴠ')}\n"
        f"• <code>/o_setname &lt;ɴᴀᴍᴇ&gt;</code> - ᴜᴘᴅᴀᴛᴇ ʙᴏᴛ ᴅɪꜱᴘʟᴀʏ ɴᴀᴍᴇ\n"
        f"• <code>/o_setbio &lt;ʙɪᴏ&gt;</code> - ᴜᴘᴅᴀᴛᴇ ʙᴏᴛ ᴀʙᴏᴜᴛ/ʙɪᴏ\n"
        f"• <code>/o_setdescription &lt;ᴅᴇꜱᴄ&gt;</code> - ᴜᴘᴅᴀᴛᴇ ʙᴏᴛ ᴅᴇꜱᴄʀɪᴘᴛɪᴏɴ\n"
        f"• <code>/o_env</code> - ꜱʜᴏᴡ ɴᴏɴ-ꜱᴇɴꜱɪᴛɪᴠᴇ ᴇɴᴠ ᴠᴀʀꜱ\n"
        f"• <code>/o_users</code> - ꜱʜᴏᴡ ᴛᴏᴛᴀʟ ʀᴇɢɪꜱᴛᴇʀᴇᴅ ᴜꜱᴇʀꜱ\n"
        f"• <code>/o_userslist</code> - ʟɪꜱᴛ ᴀʟʟ ꜱᴇʀᴠᴇᴅ ᴜꜱᴇʀꜱ\n\n"
        
        f"» {small_caps('ꜱʏꜱᴛᴇᴍ ᴍᴏᴅᴇʀᴀᴛɪᴏɴ')}\n"
        f"• <code>/o_shadowban</code> / <code>/o_unshadow</code> - shadowban\n"
        f"• <code>/o_maintenance &lt;ᴏɴ/ᴏꜰꜰ&gt;</code> - maintenance mode\n"
        f"• <code>/blacklistchat</code> / <code>/whitelistchat</code> - chat bl\n"
        f"• <code>/gban</code> / <code>/ungban</code> - global ban\n\n"
        
        f"» {small_caps('ᴜᴛɪʟɪᴛɪᴇꜱ')}\n"
        f"• <code>/o_dbbackup</code> - dump database (json/sqlite)\n"
        f"• <code>/o_cleanup</code> - clear downloads folder\n"
        f"• <code>/broadcast</code> - global message broadcast\n"
        f"• <code>/restart</code> - reboot bot process\n"
        f"• <code>/logs</code> - upload system logs"
    )
    await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                             f"<blockquote>{body}</blockquote>")

