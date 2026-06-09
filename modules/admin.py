from pyrogram import Client, filters, enums
from pyrogram.types import Message, ChatPrivileges
from helpers.filters import admin
from helpers.styling import small_caps, fraktur
from database.db import db
import asyncio

def get_user_info(message: Message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        user = message.command[1]
    else:
        user = None
    return user

async def handle_admin_error(e):
    error_str = str(e)
    header = fraktur("Action Failed")
    if "USER_ADMIN_INVALID" in error_str or "ChatAdminRequired" in error_str:
        body = "ɪ ʟᴀᴄᴋ ᴛʜᴇ ɴᴇᴄᴇꜱꜱᴀʀʏ ᴀᴍɪɴ ʀɪɢʜᴛꜱ. ᴇɴꜱᴜʀᴇ ɪ ᴀᴍ ᴘʀᴏᴍᴏᴛᴇᴅ ᴡɪᴛʜ ᴛʜᴇ ᴀᴘᴘʀᴏᴘʀɪᴀᴛᴇ ᴘᴇʀᴍɪꜱꜱɪᴏɴꜱ."
    else:
        body = f"ᴀɴ ᴜɴᴇxᴘᴇᴄᴛᴇᴅ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ: {error_str[:100]}"
    return f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>"

@Client.on_message(filters.command("ban") & admin)
async def ban_user(client: Client, message: Message):
    user = get_user_info(message)
    if not user:
        header = fraktur("Input Required")
        body = "ᴘʟᴇᴀꜱᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀɴᴀᴍᴇ/ɪᴅ ᴛᴏ ʙᴀɴ."
        return await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")
    
    try:
        if isinstance(user, str):
            user = await client.get_users(user)
        
        await message.chat.ban_member(user.id)
        header = fraktur("User Banned")
        body = f"» {small_caps('ᴜꜱᴇʀ')}: {user.mention}\n" \
               f"» {small_caps('ᴀᴅᴍɪɴ')}: {message.from_user.mention}"
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{body}</blockquote>")
    except Exception as e:
        await message.reply_text(await handle_admin_error(e))

@Client.on_message(filters.command("unban") & admin)
async def unban_user(client: Client, message: Message):
    user = get_user_info(message)
    if not user:
        header = fraktur("Input Required")
        body = "ᴘʟᴇᴀꜱᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀɴᴀᴍᴇ/ɪᴅ ᴛᴏ ᴜɴʙᴀɴ."
        return await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")
    
    try:
        if isinstance(user, str):
            user = await client.get_users(user)
        
        await message.chat.unban_member(user.id)
        header = fraktur("User Unbanned")
        body = f"» {small_caps('ᴜꜱᴇʀ')}: {user.mention}\n" \
               f"» {small_caps('ᴀᴅᴍɪɴ')}: {message.from_user.mention}"
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{body}</blockquote>")
    except Exception as e:
        await message.reply_text(await handle_admin_error(e))

@Client.on_message(filters.command("kick") & admin)
async def kick_user(client: Client, message: Message):
    user = get_user_info(message)
    if not user:
        header = fraktur("Input Required")
        body = "ᴘʟᴇᴀꜱᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀɴᴀᴍᴇ/ɪᴅ ᴛᴏ ᴋɪᴄᴋ."
        return await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")
    
    try:
        if isinstance(user, str):
            user = await client.get_users(user)
        
        await message.chat.ban_member(user.id)
        await message.chat.unban_member(user.id)
        header = fraktur("User Kicked")
        body = f"» {small_caps('ᴜꜱᴇʀ')}: {user.mention}\n" \
               f"» {small_caps('ᴀᴅᴍɪɴ')}: {message.from_user.mention}"
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{body}</blockquote>")
    except Exception as e:
        await message.reply_text(await handle_admin_error(e))

@Client.on_message(filters.command("mute") & admin)
async def mute_user(client: Client, message: Message):
    user = get_user_info(message)
    if not user:
        header = fraktur("Input Required")
        body = "ᴘʟᴇᴀꜱᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀɴᴀᴍᴇ/ɪᴅ ᴛᴏ ᴍᴜᴛᴇ."
        return await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")
    
    try:
        if isinstance(user, str):
            user = await client.get_users(user)
        
        await message.chat.restrict_member(user.id, enums.ChatPermissions(can_send_messages=False))
        header = fraktur("User Muted")
        body = f"» {small_caps('ᴜꜱᴇʀ')}: {user.mention}\n" \
               f"» {small_caps('ᴀᴅᴍɪɴ')}: {message.from_user.mention}"
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{body}</blockquote>")
    except Exception as e:
        await message.reply_text(await handle_admin_error(e))

@Client.on_message(filters.command("unmute") & admin)
async def unmute_user(client: Client, message: Message):
    user = get_user_info(message)
    if not user:
        header = fraktur("Input Required")
        body = "ᴘʟᴇᴀꜱᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀɴᴀᴍᴇ/ɪᴅ ᴛᴏ ᴜɴᴍᴜᴛᴇ."
        return await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")
    
    try:
        if isinstance(user, str):
            user = await client.get_users(user)
        
        await message.chat.restrict_member(user.id, enums.ChatPermissions(can_send_messages=True))
        header = fraktur("User Unmuted")
        body = f"» {small_caps('ᴜꜱᴇʀ')}: {user.mention}\n" \
               f"» {small_caps('ᴀᴅᴍɪɴ')}: {message.from_user.mention}"
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{body}</blockquote>")
    except Exception as e:
        await message.reply_text(await handle_admin_error(e))

@Client.on_message(filters.command("warn") & admin)
async def warn_user(client: Client, message: Message):
    user = get_user_info(message)
    if not user:
        header = fraktur("Input Required")
        body = "ᴘʟᴇᴀꜱᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀɴᴀᴍᴇ/ɪᴅ ᴛᴏ ᴡᴀʀɴ."
        return await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")
    
    try:
        if isinstance(user, str):
            user = await client.get_users(user)
        
        count = await db.add_warn(user.id, message.chat.id)
        limit = 3 
        
        if count >= limit:
            await message.chat.ban_member(user.id)
            await message.chat.unban_member(user.id)
            await db.reset_warns(user.id, message.chat.id)
            header = fraktur("Warn Limit Reached")
            body = f"» {small_caps('ᴜꜱᴇʀ')}: {user.mention}\n" \
                   f"» {small_caps('ᴀᴄᴛɪᴏɴ')}: {small_caps('ᴋɪᴄᴋᴇᴅ ꜰʀᴏᴍ ᴄʜᴀᴛ')}"
            await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                     f"<blockquote>{body}</blockquote>")
        else:
            header = fraktur("User Warned")
            body = f"» {small_caps('ᴜꜱᴇʀ')}: {user.mention}\n" \
                   f"» {small_caps('ᴡᴀʀɴɪɴɢꜱ')}: {count}/{limit}\n" \
                   f"» {small_caps('ᴀᴅᴍɪɴ')}: {message.from_user.mention}"
            await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                     f"<blockquote>{body}</blockquote>")
    except Exception as e:
        await message.reply_text(await handle_admin_error(e))

@Client.on_message(filters.command("warnings") & admin)
async def view_warnings(client: Client, message: Message):
    user = get_user_info(message)
    if not user:
        user = message.from_user
    
    try:
        if isinstance(user, str):
            user = await client.get_users(user)
        
        count = await db.get_warns(user.id, message.chat.id)
        header = fraktur("User Warnings")
        body = f"» {small_caps('ᴜꜱᴇʀ')}: {user.mention}\n" \
               f"» {small_caps('ᴄᴏᴜɴᴛ')}: {count}/3"
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{body}</blockquote>")
    except Exception as e:
        await message.reply_text(await handle_admin_error(e))

@Client.on_message(filters.command("resetwarns") & admin)
async def reset_warnings(client: Client, message: Message):
    user = get_user_info(message)
    if not user:
        header = fraktur("Input Required")
        body = "ᴘʟᴇᴀꜱᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀɴᴀᴍᴇ/ɪᴅ ᴛᴏ ʀᴇꜱᴇᴛ."
        return await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")
    
    try:
        if isinstance(user, str):
            user = await client.get_users(user)
        
        await db.reset_warns(user.id, message.chat.id)
        header = fraktur("Warnings Reset")
        body = f"» {small_caps('ᴜꜱᴇʀ')}: {user.mention}\n" \
               f"» {small_caps('ᴀᴅᴍɪɴ')}: {message.from_user.mention}"
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{body}</blockquote>")
    except Exception as e:
        await message.reply_text(await handle_admin_error(e))

@Client.on_message(filters.command("purge") & admin)
async def purge_messages(client: Client, message: Message):
    if not message.reply_to_message:
        header = fraktur("Purge Error")
        body = "ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴛᴏ ꜱᴛᴀʀᴛ ᴘᴜʀɢɪɴɢ ꜰʀᴏᴍ ᴛʜᴇʀᴇ."
        return await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")
    
    try:
        message_ids = []
        for msg_id in range(message.reply_to_message.id, message.id):
            message_ids.append(msg_id)
        
        for i in range(0, len(message_ids), 100):
            await client.delete_messages(message.chat.id, message_ids[i:i+100])
        
        await message.delete()
        header = fraktur("Purge Completed")
        m = await client.send_message(message.chat.id, f"<blockquote>{header} ❞</blockquote>")
        await asyncio.sleep(3)
        await m.delete()
    except Exception as e:
        await message.reply_text(await handle_admin_error(e))

@Client.on_message(filters.command("pin") & admin)
async def pin_message(client: Client, message: Message):
    if not message.reply_to_message:
        header = fraktur("Pin Error")
        body = "ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴛᴏ ᴘɪɴ ɪᴛ."
        return await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")
    
    try:
        await message.reply_to_message.pin()
        await message.delete()
    except Exception as e:
        await message.reply_text(await handle_admin_error(e))

@Client.on_message(filters.command("unpin") & admin)
async def unpin_message(client: Client, message: Message):
    try:
        await message.chat.unpin_all_messages()
        header = fraktur("Unpinned")
        await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps('ᴀʟʟ ᴍᴇꜱꜱᴀɢᴇꜱ ᴜɴᴘɪɴɴᴇᴅ')}</blockquote>")
    except Exception as e:
        await message.reply_text(await handle_admin_error(e))

@Client.on_message(filters.command("promote") & admin)
async def promote_user(client: Client, message: Message):
    user = get_user_info(message)
    if not user:
        header = fraktur("Input Required")
        body = "ᴘʟᴇᴀꜱᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀɴᴀᴍᴇ/ɪᴅ ᴛᴏ ᴘʀᴏᴍᴏᴛᴇ."
        return await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")
    
    try:
        if isinstance(user, str):
            user = await client.get_users(user)
        
        await message.chat.promote_member(
            user.id,
            privileges=ChatPrivileges(
                can_manage_chat=True,
                can_delete_messages=True,
                can_manage_video_chats=True,
                can_restrict_members=True,
                can_promote_members=False,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=True
            )
        )
        header = fraktur("User Promoted")
        body = f"» {small_caps('ᴜꜱᴇʀ')}: {user.mention}\n" \
               f"» {small_caps('ᴀᴅᴍɪɴ')}: {message.from_user.mention}"
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{body}</blockquote>")
    except Exception as e:
        await message.reply_text(await handle_admin_error(e))

@Client.on_message(filters.command("demote") & admin)
async def demote_user(client: Client, message: Message):
    user = get_user_info(message)
    if not user:
        header = fraktur("Input Required")
        body = "ᴘʟᴇᴀꜱᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀɴᴀᴍᴇ/ɪᴅ ᴛᴏ ᴅᴇᴍᴏᴛᴇ."
        return await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")
    
    try:
        if isinstance(user, str):
            user = await client.get_users(user)
        
        await message.chat.promote_member(
            user.id,
            privileges=ChatPrivileges(
                can_manage_chat=False,
                can_delete_messages=False,
                can_manage_video_chats=False,
                can_restrict_members=False,
                can_promote_members=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False
            )
        )
        header = fraktur("User Demoted")
        body = f"» {small_caps('ᴜꜱᴇʀ')}: {user.mention}\n" \
               f"» {small_caps('ᴀᴅᴍɪɴ')}: {message.from_user.mention}"
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{body}</blockquote>")
    except Exception as e:
        await message.reply_text(await handle_admin_error(e))

@Client.on_message(filters.command("auth") & admin)
async def auth_user_command(client: Client, message: Message):
    user = get_user_info(message)
    if not user: 
        header = fraktur("Input Required")
        body = "ᴘʟᴇᴀꜱᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀɴᴀᴍᴇ/ɪᴅ ᴛᴏ ᴀᴜᴛʜ."
        return await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")
    
    try:
        if isinstance(user, str): user = await client.get_users(user)
        await db.add_auth_user(user.id, message.chat.id)
        header = fraktur("Authorized")
        body = f"» {small_caps('ᴜꜱᴇʀ')}: {user.mention}"
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{body}</blockquote>")
    except Exception as e: await message.reply_text(await handle_admin_error(e))

@Client.on_message(filters.command("unauth") & admin)
async def unauth_user_command(client: Client, message: Message):
    user = get_user_info(message)
    if not user:
        header = fraktur("Input Required")
        body = "ᴘʟᴇᴀꜱᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀɴᴀᴍᴇ/ɪᴅ ᴛᴏ ᴜɴᴀᴜᴛʜ."
        return await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")
    
    try:
        if isinstance(user, str): user = await client.get_users(user)
        await db.remove_auth_user(user.id, message.chat.id)
        header = fraktur("Deauthorized")
        body = f"» {small_caps('ᴜꜱᴇʀ')}: {user.mention}"
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{body}</blockquote>")
    except Exception as e: await message.reply_text(await handle_admin_error(e))

@Client.on_message(filters.command("authusers"))
async def auth_users_list(client: Client, message: Message):
    users = await db.get_auth_users(message.chat.id)
    if not users: return await message.reply_text(small_caps("ɴᴏ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜꜱᴇʀꜱ ɪɴ ᴛʜɪꜱ ᴄʜᴀᴛ."))
    
    body = ""
    for i, user_id in enumerate(users, 1):
        try:
            user = await client.get_users(user_id)
            body += f"{i}. {user.mention}\n"
        except:
            body += f"{i}. <code>{user_id}</code>\n"
            
    header = fraktur("Authorized Users")
    await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                             f"<blockquote>{body}</blockquote>")

@Client.on_message(filters.command("blacklist") & admin)
async def blacklist_user_command(client: Client, message: Message):
    user = get_user_info(message)
    if not user:
        header = fraktur("Input Required")
        body = "ᴘʟᴇᴀꜱᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀɴᴀᴍᴇ/ɪᴅ ᴛᴏ ʙʟᴀᴄᴋʟɪꜱᴛ."
        return await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")
    
    try:
        if isinstance(user, str): user = await client.get_users(user)
        await db.blacklist_user(user.id)
        header = fraktur("User Blacklisted")
        body = f"» {small_caps('ᴜꜱᴇʀ')}: {user.mention}"
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{body}</blockquote>")
    except Exception as e: await message.reply_text(await handle_admin_error(e))

@Client.on_message(filters.command("whitelist") & admin)
async def whitelist_user_command(client: Client, message: Message):
    user = get_user_info(message)
    if not user:
        header = fraktur("Input Required")
        body = "ᴘʟᴇᴀꜱᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀɴᴀᴍᴇ/ɪᴅ ᴛᴏ ᴡʜɪᴛᴇʟɪꜱᴛ."
        return await message.reply_text(f"<blockquote>{header} ❞\n\n{small_caps(body)}</blockquote>")
    
    try:
        if isinstance(user, str): user = await client.get_users(user)
        await db.whitelist_user(user.id)
        header = fraktur("User Whitelisted")
        body = f"» {small_caps('ᴜꜱᴇʀ')}: {user.mention}"
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{body}</blockquote>")
    except Exception as e: await message.reply_text(await handle_admin_error(e))

@Client.on_message(filters.command("blacklistedusers"))
async def blacklisted_users_list(client: Client, message: Message):
    users = await db.get_blacklisted_users()
    if not users: return await message.reply_text(small_caps("ɴᴏ ʙʟᴀᴄᴋʟɪꜱᴛᴇᴅ ᴜꜱᴇʀꜱ."))
    
    body = ""
    for i, user_id in enumerate(users, 1):
        try:
            user = await client.get_users(user_id)
            body += f"{i}. {user.mention}\n"
        except:
            body += f"{i}. <code>{user_id}</code>\n"
            
    header = fraktur("Blacklisted Users")
    await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                             f"<blockquote>{body}</blockquote>")
