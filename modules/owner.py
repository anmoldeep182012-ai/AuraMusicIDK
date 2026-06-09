import os
import sys
import asyncio
import aiosqlite
from pyrogram import Client, filters
from pyrogram.types import Message
from helpers.filters import owner_only
from helpers.styling import small_caps, fraktur
from database.db import db
import modules.music as music

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
            return await message.reply_text(small_caps("ɴᴏ ꜱᴜᴅᴏ ᴜꜱᴇʀꜱ ꜰᴏᴜɴᴅ."))
        
        header = fraktur("Sudo Users")
        list_text = "\n".join([f"• {user_id}" for user_id in sudoers])
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{list_text}</blockquote>")
    except Exception as e:
        header = fraktur("Sudo List Error")
        await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("broadcast") & owner_only)
async def broadcast_handler(client: Client, message: Message):
    if not message.reply_to_message and len(message.command) < 2:
        header = fraktur("Usage Error")
        return await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                         f"<blockquote>{small_caps('ᴘʟᴇᴀꜱᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ (ᴛᴇxᴛ, ᴍᴇᴅɪᴀ, ꜱɪᴛᴄᴋᴇʀ) ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴛᴇxᴛ ᴛᴏ ʙʀᴏᴀᴅᴄᴀꜱᴛ.')}</blockquote>")

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
            # Broadcast utilizing copy_message to support all media types or send_message for direct text
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
                                           f"<blockquote>{small_caps('ꜱᴇɴᴛ')}: {sent}\n" \
                                           f"{small_caps('ꜰᴀɪʟᴇᴅ')}: {failed}</blockquote>")
            except:
                pass

        await asyncio.sleep(0.1) # Controlled rate

    header = fraktur("Broadcast Completed")
    await status_msg.edit_text(f"<blockquote>{header} ❞</blockquote>\n" \
                               f"<blockquote>{small_caps('ᴛᴏᴛᴀʟ ꜱᴜᴄᴄᴇꜱꜱ')}: {sent}\n" \
                               f"{small_caps('ᴛᴏᴛᴀʟ ꜰᴀɪʟᴜʀᴇꜱ')}: {failed}</blockquote>")

@Client.on_message(filters.command("restart") & owner_only)
async def restart_handler(client: Client, message: Message):
    await message.reply_text(small_caps("ʀᴇꜱᴛᴀʀᴛɪɴɢ ʙᴏᴛ..."))
    os.execv(sys.executable, ['python'] + sys.argv)

@Client.on_message(filters.command("logs") & owner_only)
async def logs_handler(client: Client, message: Message):
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
    user = music.get_user_info(message)
    if not user: return await message.reply_text(small_caps("ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀ ɪᴅ/ᴜꜱᴇʀɴᴀᴍᴇ."))
    
    try:
        if isinstance(user, str): user = await client.get_users(user)
        await db.set_setting(f"shadowban_{user.id}", "true")
        await message.reply_text(f"<blockquote>{fraktur('Shadowbanned')} ❞\n\n{user.mention}</blockquote>")
    except Exception as e: await message.reply_text(str(e))

@Client.on_message(filters.command("o_unshadow") & owner_only)
async def unshadow_handler(client: Client, message: Message):
    user = music.get_user_info(message)
    if not user: return await message.reply_text(small_caps("ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀ ɪᴅ/ᴜꜱᴇʀɴᴀᴍᴇ."))
    
    try:
        if isinstance(user, str): user = await client.get_users(user)
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
    user = music.get_user_info(message)
    if not user: return await message.reply_text(small_caps("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀɴᴀᴍᴇ/ɪᴅ ᴛᴏ ɢʙᴀɴ."))
    
    reason = message.text.split(None, 2)[2] if len(message.command) > 2 else "No reason provided"
    try:
        if isinstance(user, str): user = await client.get_users(user)
        await db.gban_user(user.id, reason)
        header = fraktur("Globally Banned")
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{small_caps('ᴜꜱᴇʀ')}: {user.mention}\n" \
                                 f"{small_caps('ʀᴇᴀꜱᴏɴ')}: {reason}</blockquote>")
    except Exception as e: await message.reply_text(str(e))

@Client.on_message(filters.command("ungban") & owner_only)
async def ungban_user_command(client: Client, message: Message):
    user = music.get_user_info(message)
    if not user: return await message.reply_text(small_caps("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀɴᴀᴍᴇ/ɪᴅ ᴛᴏ ᴜɴɢʙᴀɴ."))
    
    try:
        if isinstance(user, str): user = await client.get_users(user)
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

@Client.on_message(filters.command("o_give") & owner_only)
async def give_coins_handler(client: Client, message: Message):
    if not message.reply_to_message or len(message.command) < 2:
        return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴏ_ɢɪᴠᴇ <ᴀᴍᴏᴜɴᴛ> (ʀᴇᴘʟʏ ᴛᴏ ᴜꜱᴇʀ)"))
    
    try:
        amount = int(message.command[1])
        user_id = message.reply_to_message.from_user.id
        await db.update_balance(user_id, amount)
        await message.reply_text(f"<blockquote>{fraktur('Coins Added')} ❞\n\n{amount} {small_caps('ᴄᴏɪɴꜱ ɢɪᴠᴇɴ ᴛᴏ')} {message.reply_to_message.from_user.mention}</blockquote>")
    except ValueError:
        await message.reply_text(small_caps("ɪɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ."))

@Client.on_message(filters.command("o_reset") & owner_only)
async def reset_economy_handler(client: Client, message: Message):
    user = music.get_user_info(message)
    if not user: return await message.reply_text(small_caps("ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀ ɪᴅ/ᴜꜱᴇʀɴᴀᴍᴇ."))
    
    try:
        if isinstance(user, str): user = await client.get_users(user)
        # Reset balance to 0 and kills to 0
        async with aiosqlite.connect(db.db_path) as conn:
            await conn.execute("UPDATE users_economy SET balance = 0, kills = 0 WHERE user_id = ?", (user.id,))
            await conn.commit()
        await message.reply_text(f"<blockquote>{fraktur('Profile Wiped')} ❞\n\n{user.mention}</blockquote>")
    except Exception as e: await message.reply_text(str(e))
