import os
import random
import asyncio
import time
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.db import db
from helpers.filters import sudoers
from helpers.styling import small_caps, fraktur, spaced_text
import modules.music as music

DEFAULT_START_TEXT = """
┌ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ ─────────────────────────•
│ ʜᴇʏ, {name}
│ ɪ ᴀᴍ ⌜ ᴀᴜʀᴀʟʏx x ᴍᴜꜱɪᴄ ⌟
└──────────────────────────────────────•

<blockquote>ᴀ ᴜ ʀ ᴀ ʟ ʏ x  ❞</blockquote>

<blockquote>ᴜᴘᴛɪᴍᴇ: {uptime}  ❞
ꜱᴇʀᴠᴇʀ ꜱᴛᴏʀᴀɢᴇ: {storage}%
ᴄᴘᴜ ʟᴏᴀᴅ: {cpu}%</blockquote>

<blockquote>ᴇɴᴊᴏʏ ᴘʀᴇᴍɪᴜᴍ ʟɪꜱᴛᴇɴɪɴɢ ᴇxᴘᴇʀɪᴇɴᴄᴇ  ❞</blockquote>

───────────────────────────────────────
ᴘᴏᴡᴇʀᴇᴅ » <a href="https://t.me/Sexuatic">ꜱᴇxᴜᴀᴛɪᴄ</a>
───────────────────────────────────────
"""

async def get_start_panel_data(client, user_id, first_name):
    uptime = "0ʜ:0ᴍ:3"
    storage = "63.1"
    cpu = "16.4"
    mention = f"<a href=\"tg://user?id={user_id}\">{first_name}</a>"
    custom_text = await db.get_setting("start_text")
    if not custom_text: custom_text = DEFAULT_START_TEXT
    
    try:
        caption = custom_text.format(name=mention, uptime=uptime, storage=storage, cpu=cpu)
    except Exception:
        caption = DEFAULT_START_TEXT.format(name=mention, uptime=uptime, storage=storage, cpu=cpu)
        
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(small_caps("⌜ ᴛᴀᴘ ᴛᴏ ꜱᴇᴇ ᴍᴀɢɪᴄ ⌟"), url=f"https://t.me/{client.me.username}?startgroup=true", style=enums.ButtonStyle.PRIMARY)],
        [
            InlineKeyboardButton(small_caps("⌜ ᴘʀɪᴠᴀᴄʏ ᴘᴏʟɪᴄʏ ⌟"), url="https://t.me/Sexuatic", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton(small_caps("⌜ ᴀᴜʀᴀʟʏx ᴛᴜɴᴇꜱ ⌟"), url="https://t.me/AuralyxTunes", style=enums.ButtonStyle.PRIMARY)
        ],
        [
            InlineKeyboardButton(small_caps("⌜ ɴᴇᴛᴡᴏʀᴋ ⌟"), url="https://t.me/AuralyxNetwork", style=enums.ButtonStyle.DEFAULT),
            InlineKeyboardButton(small_caps("⌜ ᴍʏ ʜᴏᴍᴇ ⌟"), url="https://t.me/AuralyxHome", style=enums.ButtonStyle.DEFAULT)
        ],
        [InlineKeyboardButton(small_caps("⌜ ʜᴇʟᴘ ᴀɴᴅ ᴄᴏᴍᴍᴀɴᴅꜱ ⌟"), callback_data="help_menu_1_start", style=enums.ButtonStyle.PRIMARY)],
        [InlineKeyboardButton(small_caps("⌜ ᴍʏ ᴍᴀꜱᴛᴇʀ ⌟"), url="https://t.me/Sexuatic", style=enums.ButtonStyle.DANGER)]
    ])
    return caption, buttons

@Client.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    sticker_msg = None
    for pack_name in ["Auralyx", "auralyx"]:
        try:
            stickers = await client.get_stickers(pack_name)
            if stickers:
                random_sticker = random.choice(stickers)
                sticker_msg = await client.send_sticker(message.chat.id, random_sticker.file_id)
                break
        except Exception:
            try:
                if music.userbot:
                    stickers = await music.userbot.get_stickers(pack_name)
                    if stickers:
                        random_sticker = random.choice(stickers)
                        sticker_msg = await client.send_sticker(message.chat.id, random_sticker.file_id)
                        break
            except Exception as e:
                pass

    local_photo_path = "assets/Start_Panel.png"
    caption, buttons = await get_start_panel_data(client, message.from_user.id, message.from_user.first_name)

    if os.path.exists(local_photo_path):
        await client.send_photo(
            chat_id=message.chat.id,
            photo=local_photo_path,
            has_spoiler=True,
            caption=caption,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=buttons
        )
    else:
        await client.send_message(
            chat_id=message.chat.id,
            text=caption,
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=buttons
        )
    
    if sticker_msg:
        try:
            await asyncio.sleep(1.2)
            await sticker_msg.delete()
        except:
            pass

@Client.on_callback_query(filters.regex("^start_panel$"))
async def start_panel_callback(client: Client, callback_query: CallbackQuery):
    caption, buttons = await get_start_panel_data(client, callback_query.from_user.id, callback_query.from_user.first_name)
    if callback_query.message.photo or callback_query.message.video or callback_query.message.document:
        try:
            await callback_query.edit_message_caption(caption=caption, reply_markup=buttons, parse_mode=enums.ParseMode.HTML)
        except: pass
    else:
        try:
            await callback_query.edit_message_text(text=caption, reply_markup=buttons, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
        except: pass
    await callback_query.answer()

@Client.on_message(filters.command("setstart") & sudoers)
async def set_start_handler(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text(small_caps("ᴘʟᴇᴀꜱᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴛᴏ ꜱᴇᴛ ɪᴛ ᴀꜱ ꜱᴛᴀʀᴛ ᴘᴀɴᴇʟ ᴛᴇxᴛ."))

    new_text = message.reply_to_message.text
    await db.set_setting("start_text", new_text)
    await message.reply_text(small_caps("ꜱᴛᴀʀᴛ ᴘᴀɴᴇʟ ᴛᴇxᴛ ᴜᴘᴅᴀᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ."))

@Client.on_message(filters.command("ping"))
async def ping_handler(client: Client, message: Message):
    start = time.time()
    m = await message.reply_text(small_caps("ᴘɪɴɢɪɴɢ..."))
    end = time.time()
    latency = (end - start) * 1000
    await m.edit_text(f"<blockquote>{fraktur('Pong')} ❞\n\n{small_caps('ʟᴀᴛᴇɴᴄʏ')}: {latency:.2f}ᴍꜱ</blockquote>")

@Client.on_message(filters.command(["id", "getid"]))
async def id_handler(client: Client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else "Unknown"

    text = f"» {small_caps('ᴄʜᴀᴛ ɪᴅ')}: <code>{chat_id}</code>\n"
    text += f"» {small_caps('ᴜꜱᴇʀ ɪᴅ')}: <code>{user_id}</code>"

    if message.reply_to_message:
        replied_user_id = message.reply_to_message.from_user.id
        text += f"\n» {small_caps('ʀᴇᴘʟɪᴇᴅ ᴜꜱᴇʀ ɪᴅ')}: <code>{replied_user_id}</code>"

    await message.reply_text(f"<blockquote>{fraktur('Identifiers')} ❞</blockquote>\n" \
                             f"<blockquote>{text}</blockquote>")

@Client.on_message(filters.command("maintenance") & sudoers)
async def maintenance_command_handler(client: Client, message: Message):
    if len(message.command) < 2: return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ <ᴏɴ|ᴏꜰꜰ>"))
    mode = message.command[1].lower()
    if mode == "on":
        await db.set_setting("maintenance", "true")
        await message.reply_text(small_caps("ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ ᴍᴏᴅᴇ ᴇɴᴀʙʟᴇᴅ."))
    else:
        await db.set_setting("maintenance", "false")
        await message.reply_text(small_caps("ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ ᴍᴏᴅᴇ ᴅɪꜱᴀʙʟᴇᴅ."))

HELP_MENU_TEXT = f"""
{fraktur('A U R A L Y X')}
━━━━━━━━━━━━━━━━━━━━━━
{small_caps('ʜ ᴇ ʟ ᴘ   ᴘ ᴀ ɴ ᴇ ʟ')}
━━━━━━━━━━━━━━━━━━━━━━
ᴄʜᴏᴏꜱᴇ ᴛʜᴇ ᴄᴀᴛᴇɢᴏʀʏ ꜰᴏʀ ᴡʜɪᴄʜ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ɢᴇᴛ ʜᴇʟᴘ.
ᴀꜱᴋ ʏᴏᴜʀ ᴅᴏᴜʙᴛꜱ ᴀᴛ <a href="https://t.me/AuralyxNetwork">ꜱᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ</a>

<code>ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅꜱ ᴄᴀɴ ʙᴇ ᴜꜱᴇᴅ ᴡɪᴛʜ : /</code>"""

def get_help_page(page=1, origin="start"):
    back_cb = "start_panel" if origin == "start" else "close_panel"
    
    if page == 1:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(small_caps("⌜ ᴀᴅᴍɪɴ ⌟"), callback_data=f"help_admin_{origin}", style=enums.ButtonStyle.DEFAULT),
                InlineKeyboardButton(small_caps("⌜ ᴀᴜᴛʜ ⌟"), callback_data=f"help_auth_{origin}", style=enums.ButtonStyle.DEFAULT),
                InlineKeyboardButton(small_caps("⌜ ʙʀᴏᴀᴅᴄᴀꜱᴛ ⌟"), callback_data=f"help_gcast_{origin}", style=enums.ButtonStyle.DEFAULT)
            ],
            [
                InlineKeyboardButton(small_caps("⌜ ʙʟ-ᴄʜᴀᴛ ⌟"), callback_data=f"help_blchat_{origin}", style=enums.ButtonStyle.DEFAULT),
                InlineKeyboardButton(small_caps("⌜ ʙʟ-ᴜꜱᴇʀ ⌟"), callback_data=f"help_blusers_{origin}", style=enums.ButtonStyle.DEFAULT),
                InlineKeyboardButton(small_caps("⌜ ᴄ-ᴠᴘʟᴀʏ ⌟"), callback_data=f"help_cplay_{origin}", style=enums.ButtonStyle.DEFAULT)
            ],
            [
                InlineKeyboardButton(small_caps("⌜ ɢ-ʙᴀɴ ⌟"), callback_data=f"help_gban_{origin}", style=enums.ButtonStyle.DEFAULT),
                InlineKeyboardButton(small_caps("⌜ ʟᴏᴏᴘ ⌟"), callback_data=f"help_loop_{origin}", style=enums.ButtonStyle.DEFAULT),
                InlineKeyboardButton(small_caps("⌜ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ ⌟"), callback_data=f"help_log_{origin}", style=enums.ButtonStyle.DEFAULT)
            ],
            [
                InlineKeyboardButton(small_caps("⌜ ᴘɪɴɢ ⌟"), callback_data=f"help_ping_{origin}", style=enums.ButtonStyle.DEFAULT),
                InlineKeyboardButton(small_caps("⌜ ᴠ-ᴘʟᴀʏ ⌟"), callback_data=f"help_play_{origin}", style=enums.ButtonStyle.DEFAULT),
                InlineKeyboardButton(small_caps("⌜ ꜱʜᴜꜰꜰʟᴇ ⌟"), callback_data=f"help_shuffle_{origin}", style=enums.ButtonStyle.DEFAULT)
            ],
            [
                InlineKeyboardButton(small_caps("⌜ ꜱᴇᴇᴋ ⌟"), callback_data=f"help_seek_{origin}", style=enums.ButtonStyle.DEFAULT),
                InlineKeyboardButton(small_caps("⌜ ꜱᴏɴɢ ⌟"), callback_data=f"help_song_{origin}", style=enums.ButtonStyle.DEFAULT),
                InlineKeyboardButton(small_caps("⌜ ꜱᴘᴇᴇᴅ ⌟"), callback_data=f"help_speed_{origin}", style=enums.ButtonStyle.DEFAULT)
            ],
            [
                InlineKeyboardButton("< ", callback_data=f"help_page_2_{origin}", style=enums.ButtonStyle.DEFAULT),
                InlineKeyboardButton(small_caps("ʙᴀᴄᴋ") if origin == "start" else small_caps("ᴄʟᴏꜱᴇ"), callback_data=back_cb, style=enums.ButtonStyle.DEFAULT),
                InlineKeyboardButton(" >", callback_data=f"help_page_2_{origin}", style=enums.ButtonStyle.DEFAULT)
            ]
        ])
    else:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(small_caps("⌜ ɢʀᴏᴜᴘ ⌟"), callback_data=f"help_groups_{origin}", style=enums.ButtonStyle.DEFAULT),
                InlineKeyboardButton(small_caps("⌜ ꜱᴛɪᴄᴋᴇʀ ⌟"), callback_data=f"help_stickers_{origin}", style=enums.ButtonStyle.DEFAULT),
                InlineKeyboardButton(small_caps("⌜ ᴛᴀɢ-ᴀʟʟ ⌟"), callback_data=f"help_tagall_{origin}", style=enums.ButtonStyle.DEFAULT)
            ],
            [
                InlineKeyboardButton(small_caps("⌜ ɪɴꜰᴏ ⌟"), callback_data=f"help_info_{origin}", style=enums.ButtonStyle.DEFAULT),
                InlineKeyboardButton(small_caps("⌜ ᴀᴄᴛɪᴏɴ ⌟"), callback_data=f"help_action_{origin}", style=enums.ButtonStyle.DEFAULT),
                InlineKeyboardButton(small_caps("⌜ ꜰᴏɴᴛ ⌟"), callback_data=f"help_font_{origin}", style=enums.ButtonStyle.DEFAULT)
            ],
            [
                InlineKeyboardButton(small_caps("⌜ ꜰᴜɴ ⌟"), callback_data=f"help_fun_{origin}", style=enums.ButtonStyle.DEFAULT),
                InlineKeyboardButton(small_caps("⌜ Qᴜᴏᴛʟʏ ⌟"), callback_data=f"help_quotly_{origin}", style=enums.ButtonStyle.DEFAULT)
            ],
            [
                InlineKeyboardButton("< ", callback_data=f"help_page_1_{origin}", style=enums.ButtonStyle.DEFAULT),
                InlineKeyboardButton(small_caps("ʙᴀᴄᴋ") if origin == "start" else small_caps("ᴄʟᴏꜱᴇ"), callback_data=back_cb, style=enums.ButtonStyle.DEFAULT),
                InlineKeyboardButton(" >", callback_data=f"help_page_1_{origin}", style=enums.ButtonStyle.DEFAULT)
            ]
        ])

def get_back_button(origin="start"):
    return InlineKeyboardMarkup([[InlineKeyboardButton(small_caps("ʙᴀᴄᴋ"), callback_data=f"help_menu_1_{origin}", style=enums.ButtonStyle.DEFAULT)]])

def get_help_msg(title: str, content: str) -> str:
    return f"{fraktur('A U R A L Y X')}\n━━━━━━━━━━━━━━━━━━━━━━\n{small_caps(title)}\n━━━━━━━━━━━━━━━━━━━━━━\n{content}"

@Client.on_message(filters.command("help"))
async def help_handler(client: Client, message: Message):
    await message.reply_text(HELP_MENU_TEXT, reply_markup=get_help_page(1, "cmd"), parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)

@Client.on_callback_query(filters.regex("^help_"))
async def help_callbacks(client: Client, callback_query: CallbackQuery):
    if callback_query.message.reply_to_message:
        if callback_query.from_user.id != callback_query.message.reply_to_message.from_user.id:
            return await callback_query.answer(small_caps("ᴛʜɪꜱ ᴍᴇɴᴜ ɪꜱ ɴᴏᴛ ꜰᴏʀ ʏᴏᴜ."), show_alert=True)

    parts = callback_query.data.split("_")
    action = parts[1]
    origin = parts[-1] if len(parts) > 2 and parts[-1] in ["start", "cmd"] else "start"
    
    sudo_categories = ["gcast", "blchat", "blusers", "gban", "log"]
    if action in sudo_categories:
        sudoers_list = await db.get_sudoers()
        from config import Config
        if callback_query.from_user.id != Config.OWNER_ID and callback_query.from_user.id not in sudoers_list:
            return await callback_query.answer(small_caps("ᴛʜɪꜱ ɪꜱ ᴀ ꜱᴜᴅᴏ-ᴏɴʟʏ ᴄᴀᴛᴇɢᴏʀʏ."), show_alert=True)

    await callback_query.answer()
    
    if action == "menu" or action == "page":
        page = parts[2] if len(parts) > 2 and parts[2] in ["1", "2"] else "1"
        markup = get_help_page(int(page), origin)
        
        if callback_query.message.photo or callback_query.message.video or callback_query.message.document:
            try: await callback_query.edit_message_caption(caption=HELP_MENU_TEXT, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        else:
            try: await callback_query.edit_message_text(HELP_MENU_TEXT, reply_markup=markup, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
            except: pass
            
    elif action == "ping":
        content = """• <code>/ping</code> » ꜱʜᴏᴡꜱ ᴛʜᴇ ᴘɪɴɢ ᴀɴᴅ ꜱʏꜱᴛᴇᴍ ꜱᴛᴀᴛꜱ.\n• <code>/stats</code> » ꜱʜᴏᴡꜱ ᴛʜᴇ ᴏᴠᴇʀᴀʟʟ ꜱᴛᴀᴛꜱ."""
        markup = get_back_button(origin)
        if callback_query.message.photo or callback_query.message.video or callback_query.message.document:
            try: await callback_query.edit_message_caption(caption=get_help_msg("ᴘ ɪ ɴ ɢ   &   ꜱ ᴛ ᴀ ᴛ ꜱ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        else:
            try: await callback_query.edit_message_text(get_help_msg("ᴘ ɪ ɴ ɢ   &   ꜱ ᴛ ᴀ ᴛ ꜱ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        
    elif action == "admin":
        content = """• <code>/pause</code> » ᴘᴀᴜꜱᴇ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴘʟᴀʏɪɴɢ ꜱᴛʀᴇᴀᴍ.\n• <code>/resume</code> » ʀᴇꜱᴜᴍᴇ ᴛʜᴇ ᴘᴀᴜꜱᴇᴅ ꜱᴛʀᴇᴀᴍ.\n• <code>/skip</code> » ꜱᴋɪᴘ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴘʟᴀʏɪɴɢ ꜱᴛʀᴇᴀᴍ.\n• <code>/stop</code> » ᴄʟᴇᴀʀꜱ ᴛʜᴇ Qᴜᴇᴜᴇ ᴀɴᴅ ᴇɴᴅ ᴛʜᴇ ꜱᴛʀᴇᴀᴍ.\n• <code>/player</code> » ɢᴇᴛ ᴀ ɪɴᴛᴇʀᴀᴄᴛɪᴠᴇ ᴘʟᴀʏᴇʀ ᴘᴀɴᴇʟ.\n• <code>/queue</code> » ꜱʜᴏᴡꜱ ᴛʜᴇ Qᴜᴇᴜᴇᴅ ᴛʀᴀᴄᴋꜱ ʟɪꜱᴛ."""
        markup = get_back_button(origin)
        if callback_query.message.photo or callback_query.message.video or callback_query.message.document:
            try: await callback_query.edit_message_caption(caption=get_help_msg("ᴀ ᴅ ᴍ ɪ ɴ   ᴄ ᴏ ᴍ ᴍ ᴀ ɴ ᴅ ꜱ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        else:
            try: await callback_query.edit_message_text(get_help_msg("ᴀ ᴅ ᴍ ɪ ɴ   ᴄ ᴏ ᴍ ᴍ ᴀ ɴ ᴅ ꜱ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        
    elif action == "auth":
        content = """• <code>/auth</code> » ᴀᴅᴅ ᴀ ᴜꜱᴇʀ ᴛᴏ ᴀᴜᴛʜ ʟɪꜱᴛ ᴏꜰ ᴛʜᴇ ʙᴏᴛ.\n• <code>/unauth</code> » ʀᴇᴍᴏᴠᴇ ᴀ ᴜꜱᴇʀ ꜰʀᴏᴍ ᴛʜᴇ ᴀᴜᴛʜ ʟɪꜱᴛ.\n• <code>/authusers</code> » ꜱʜᴏᴡꜱ ᴛʜᴇ ʟɪꜱᴛ ᴏꜰ ᴀᴜᴛʜ ᴜꜱᴇʀꜱ."""
        markup = get_back_button(origin)
        if callback_query.message.photo or callback_query.message.video or callback_query.message.document:
            try: await callback_query.edit_message_caption(caption=get_help_msg("ᴀ ᴜ ᴛ ʜ   ᴜ ꜱ ᴇ ʀ ꜱ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        else:
            try: await callback_query.edit_message_text(get_help_msg("ᴀ ᴜ ᴛ ʜ   ᴜ ꜱ ᴇ ʀ ꜱ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        
    elif action == "gcast":
        content = "• <code>/broadcast</code> » ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴛᴏ ꜱᴇʀᴠᴇᴅ ᴄʜᴀᴛꜱ."
        markup = get_back_button(origin)
        if callback_query.message.photo or callback_query.message.video or callback_query.message.document:
            try: await callback_query.edit_message_caption(caption=get_help_msg("ʙ ʀ ᴏ ᴀ ᴅ ᴄ ᴀ ꜱ ᴛ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        else:
            try: await callback_query.edit_message_text(get_help_msg("ʙ ʀ ᴏ ᴀ ᴅ ᴄ ᴀ ꜱ ᴛ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass

    elif action == "blchat":
        content = """• <code>/blacklistchat</code> » ʙʟᴀᴄᴋʟɪꜱᴛ ᴀ ᴄʜᴀᴛ ꜰʀᴏᴍ ᴛʜᴇ ʙᴏᴛ.\n• <code>/whitelistchat</code> » ᴡʜɪᴛᴇʟɪꜱᴛ ᴛʜᴇ ʙʟᴀᴄᴋʟɪꜱᴛᴇᴅ ᴄʜᴀᴛ.\n• <code>/blacklistedchat</code> » ꜱʜᴏᴡꜱ ᴛʜᴇ ʟɪꜱᴛ ᴏꜰ ʙʟ-ᴄʜᴀᴛꜱ."""
        markup = get_back_button(origin)
        if callback_query.message.photo or callback_query.message.video or callback_query.message.document:
            try: await callback_query.edit_message_caption(caption=get_help_msg("ᴄ ʜ ᴀ ᴛ   ʙ ʟ ᴀ ᴄ ᴋ ʟ ɪ ꜱ ᴛ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        else:
            try: await callback_query.edit_message_text(get_help_msg("ᴄ ʜ ᴀ ᴛ   ʙ ʟ ᴀ ᴄ ᴋ ʟ ɪ ꜱ ᴛ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass

    elif action == "cplay":
        content = """• <code>/cvplay</code> » ꜱᴛʀᴇᴀᴍ ᴠɪᴅᴇᴏ ᴏɴ ᴄʜᴀɴɴᴇʟ'ꜱ ᴠᴄ.\n• <code>/vplayforce</code> » ꜰᴏʀᴄᴇ ꜱᴛʀᴇᴀᴍ ᴏɴ ᴠᴄ."""
        markup = get_back_button(origin)
        if callback_query.message.photo or callback_query.message.video or callback_query.message.document:
            try: await callback_query.edit_message_caption(caption=get_help_msg("ᴄ ʜ ᴀ ɴ ɴ ᴇ ʟ   ᴘ ʟ ᴀ ʏ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        else:
            try: await callback_query.edit_message_text(get_help_msg("ᴄ ʜ ᴀ ɴ ɴ ᴇ ʟ   ᴘ ʟ ᴀ ʏ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass

    elif action == "gban":
        content = """• <code>/gban</code> » ɢʟᴏʙᴀʟʟʏ ʙᴀɴꜱ ᴀ ᴜꜱᴇʀ.\n• <code>/ungban</code> » ɢʟᴏʙᴀʟʟʏ ᴜɴʙᴀɴꜱ ᴀ ᴜꜱᴇʀ.\n• <code>/gbannedusers</code> » ꜱʜᴏᴡꜱ ᴛʜᴇ ʟɪꜱᴛ ᴏꜰ ɢʙᴀɴ ᴜꜱᴇʀꜱ."""
        markup = get_back_button(origin)
        if callback_query.message.photo or callback_query.message.video or callback_query.message.document:
            try: await callback_query.edit_message_caption(caption=get_help_msg("ɢ ʟ ᴏ ʙ ᴀ ʟ   ʙ ᴀ ɴ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        else:
            try: await callback_query.edit_message_text(get_help_msg("ɢ ʟ ᴏ ʙ ᴀ ʟ   ʙ ᴀ ɴ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass

    elif action == "loop":
        content = "• <code>/loop</code> » ᴇɴᴀʙʟᴇ/ᴅɪꜱᴀʙʟᴇ ʟᴏᴏᴘ ᴍᴏᴅᴇ."
        markup = get_back_button(origin)
        if callback_query.message.photo or callback_query.message.video or callback_query.message.document:
            try: await callback_query.edit_message_caption(caption=get_help_msg("ʟ ᴏ ᴏ ᴘ   ꜱ ᴛ ʀ ᴇ ᴀ ᴍ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        else:
            try: await callback_query.edit_message_text(get_help_msg("ʟ ᴏ ᴏ ᴘ   ꜱ ᴛ ʀ ᴇ ᴀ ᴍ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass

    elif action == "log":
        content = """• <code>/logs</code> » ɢᴇᴛ ʟᴏɢꜱ ᴏꜰ ᴛʜᴇ ʙᴏᴛ.\n• <code>/maintenance</code> » ᴇɴᴀʙʟᴇ/ᴅɪꜱᴀʙʟᴇ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ ᴍᴏᴅᴇ."""
        markup = get_back_button(origin)
        if callback_query.message.photo or callback_query.message.video or callback_query.message.document:
            try: await callback_query.edit_message_caption(caption=get_help_msg("ᴍ ᴀ ɪ ɴ ᴛ ᴇ ɴ ᴀ ɴ ᴄ ᴇ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        else:
            try: await callback_query.edit_message_text(get_help_msg("ᴍ ᴀ ɪ ɴ ᴛ ᴇ ɴ ᴀ ɴ ᴄ ᴇ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass

    elif action == "play":
        content = """• <code>/vplay</code> » ꜱᴛʀᴇᴀᴍ ᴠɪᴅᴇᴏ ᴏɴ ᴠɪᴅᴇᴏᴄʜᴀᴛ.\n• <code>/vplayforce</code> » ꜰᴏʀᴄᴇ ꜱᴛʀᴇᴀᴍ ᴠɪᴅᴇᴏ ᴏɴ ᴠᴄ."""
        markup = get_back_button(origin)
        if callback_query.message.photo or callback_query.message.video or callback_query.message.document:
            try: await callback_query.edit_message_caption(caption=get_help_msg("ᴘ ʟ ᴀ ʏ   ᴄ ᴏ ᴍ ᴍ ᴀ ɴ ᴅ ꜱ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        else:
            try: await callback_query.edit_message_text(get_help_msg("ᴘ ʟ ᴀ ʏ   ᴄ ᴏ ᴍ ᴍ ᴀ ɴ ᴅ ꜱ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass

    elif action == "shuffle":
        content = "• <code>/shuffle</code> » ꜱʜᴜꜰꜰʟᴇ'ꜱ ᴛʜᴇ Qᴜᴇᴜᴇ."
        markup = get_back_button(origin)
        if callback_query.message.photo or callback_query.message.video or callback_query.message.document:
            try: await callback_query.edit_message_caption(caption=get_help_msg("ꜱ ʜ ᴜ ꜰ ꜰ ʟ ᴇ   Q ᴜ ᴇ ᴜ ᴇ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        else:
            try: await callback_query.edit_message_text(get_help_msg("ꜱ ʜ ᴜ ꜰ ꜰ ʟ ᴇ   Q ᴜ ᴇ ᴜ ᴇ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass

    elif action == "seek":
        content = """• <code>/seek</code> » ꜱᴇᴇᴋ ᴛʜᴇ ꜱᴛʀᴇᴀᴍ ᴛᴏ ɢɪᴠᴇɴ ᴅᴜʀᴀᴛɪᴏɴ.\n• <code>/seekback</code> » ʙᴀᴄᴋᴡᴀʀᴅ ꜱᴇᴇᴋ ᴛʜᴇ ꜱᴛʀᴇᴀᴍ."""
        markup = get_back_button(origin)
        if callback_query.message.photo or callback_query.message.video or callback_query.message.document:
            try: await callback_query.edit_message_caption(caption=get_help_msg("ꜱ ᴇ ᴇ ᴋ   ꜱ ᴛ ʀ ᴇ ᴀ ᴍ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        else:
            try: await callback_query.edit_message_text(get_help_msg("ꜱ ᴇ ᴇ ᴋ   ꜱ ᴛ ʀ ᴇ ᴀ ᴍ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass

    elif action == "song":
        content = "• <code>/song</code> » ᴅᴏᴡɴʟᴏᴀᴅ ᴀɴʏ ᴛʀᴀᴄᴋ ꜰʀᴏᴍ ʏᴏᴜᴛᴜʙᴇ."
        markup = get_back_button(origin)
        if callback_query.message.photo or callback_query.message.video or callback_query.message.document:
            try: await callback_query.edit_message_caption(caption=get_help_msg("ꜱ ᴏ ɴ ɢ   ᴅ ᴏ ᴡ ɴ ʟ ᴏ ᴀ ᴅ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        else:
            try: await callback_query.edit_message_text(get_help_msg("ꜱ ᴏ ɴ ɢ   ᴅ ᴏ ᴡ ɴ ʟ ᴏ ᴀ ᴅ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass

    elif action == "speed":
        content = "• <code>/speed</code> » ᴀᴅᴊᴜꜱᴛ ᴀᴜᴅɪᴏ ᴘʟᴀʏʙᴀᴄᴋ ꜱᴘᴇᴇᴅ."
        markup = get_back_button(origin)
        if callback_query.message.photo or callback_query.message.video or callback_query.message.document:
            try: await callback_query.edit_message_caption(caption=get_help_msg("ꜱ ᴘ ᴇ ᴇ ᴅ   ᴄ ᴏ ɴ ᴛ ʀ ᴏ ʟ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        else:
            try: await callback_query.edit_message_text(get_help_msg("ꜱ ᴘ ᴇ ᴇ ᴅ   ᴄ ᴏ ɴ ᴛ ʀ ᴏ ʟ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass

    elif action == "groups":
        content = """• <code>/pin</code> » ᴘɪɴꜱ ᴀ ᴍᴇꜱꜱᴀɢᴇ.\n• <code>/unpin</code> » ᴜɴᴘɪɴꜱ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛʟʏ ᴘɪɴɴᴇᴅ.\n• <code>/staff</code> » ᴅɪꜱᴘʟᴀʏꜱ ᴛʜᴇ ʟɪꜱᴛ ᴏꜰ ꜱᴛᴀꜰꜰ.\n• <code>/bots</code> » ᴅɪꜱᴘʟᴀʏꜱ ᴛʜᴇ ʟɪꜱᴛ ᴏꜰ ʙᴏᴛꜱ.\n• <code>/zombies</code> » ʀᴇᴍᴏᴠᴇꜱ ᴅᴇʟᴇᴛᴇᴅ ᴍᴇᴍʙᴇʀꜱ."""
        markup = get_back_button(origin)
        if callback_query.message.photo or callback_query.message.video or callback_query.message.document:
            try: await callback_query.edit_message_caption(caption=get_help_msg("ɢ ʀ ᴏ ᴜ ᴘ   ᴍ ᴀ ɴ ᴀ ɢ ᴇ ᴍ ᴇ ɴ ᴛ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        else:
            try: await callback_query.edit_message_text(get_help_msg("ɢ ʀ ᴏ ᴜ ᴘ   ᴍ ᴀ ɴ ᴀ ɢ ᴇ ᴍ ᴇ ɴ ᴛ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass

    elif action == "stickers":
        content = """• <code>/packkang</code> » ᴄʀᴇᴀᴛᴇꜱ ᴀ ᴘᴀᴄᴋ ᴏꜰ ꜱᴛɪᴄᴋᴇʀꜱ.\n• <code>/stickerid</code> » ɢᴇᴛꜱ ᴛʜᴇ ꜱᴛɪᴄᴋᴇʀ ɪᴅ."""
        markup = get_back_button(origin)
        if callback_query.message.photo or callback_query.message.video or callback_query.message.document:
            try: await callback_query.edit_message_caption(caption=get_help_msg("ꜱ ᴛ ɪ ᴄ ᴋ ᴇ ʀ ꜱ   ᴄ ᴏ ᴍ ᴍ ᴀ ɴ ᴅ ꜱ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        else:
            try: await callback_query.edit_message_text(get_help_msg("ꜱ ᴛ ɪ ᴄ ᴋ ᴇ ʀ ꜱ   ᴄ ᴏ ᴍ ᴍ ᴀ ɴ ᴅ ꜱ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass

    elif action == "info":
        content = """• <code>/id</code> » ɢᴇᴛ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴄʜᴀᴛ/ᴜꜱᴇʀ ɪᴅ.\n• <code>/info</code> » ɢᴇᴛ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ ᴀʙᴏᴜᴛ ᴀ ᴜꜱᴇʀ."""
        markup = get_back_button(origin)
        if callback_query.message.photo or callback_query.message.video or callback_query.message.document:
            try: await callback_query.edit_message_caption(caption=get_help_msg("ɪ ɴ ꜰ ᴏ   ᴄ ᴏ ᴍ ᴍ ᴀ ɴ ᴅ ꜱ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        else:
            try: await callback_query.edit_message_text(get_help_msg("ɪ ɴ ꜰ ᴏ   ᴄ ᴏ ᴍ ᴍ ᴀ ɴ ᴅ ꜱ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass

    elif action == "tagall":
        content = """• <code>/tagall</code> » ʀᴀɴᴅᴏᴍ ᴍᴇꜱꜱᴀɢᴇ ᴛᴀɢ.\n• <code>/vctag</code> » ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ɪɴᴠɪᴛᴇ ᴛᴀɢ.\n• <code>/utag</code> » ᴀɴʏ ᴡʀɪᴛᴛᴇɴ ᴛᴇxᴛ ᴛᴀɢ."""
        markup = get_back_button(origin)
        if callback_query.message.photo or callback_query.message.video or callback_query.message.document:
            try: await callback_query.edit_message_caption(caption=get_help_msg("ᴛ ᴀ ɢ   ᴄ ᴏ ᴍ ᴍ ᴀ ɴ ᴅ ꜱ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        else:
            try: await callback_query.edit_message_text(get_help_msg("ᴛ ᴀ ɢ   ᴄ ᴏ ᴍ ᴍ ᴀ ɴ ᴅ ꜱ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass

    elif action == "action":
        content = """• <code>/ban</code> » ʙᴀɴꜱ ᴀ ᴜꜱᴇʀ.\n• <code>/kick</code> » ᴋɪᴄᴋꜱ ᴀ ᴜꜱᴇʀ ᴏᴜᴛ.\n• <code>/mute</code> » ꜱɪʟᴇɴᴄᴇꜱ ᴀ ᴜꜱᴇʀ.\n• <code>/unban</code> » ᴜɴʙᴀɴꜱ ᴀ ᴜꜱᴇʀ."""
        markup = get_back_button(origin)
        if callback_query.message.photo or callback_query.message.video or callback_query.message.document:
            try: await callback_query.edit_message_caption(caption=get_help_msg("ᴀ ᴄ ᴛ ɪ ᴏ ɴ   ᴄ ᴏ ᴍ ᴍ ᴀ ɴ ᴅ ꜱ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        else:
            try: await callback_query.edit_message_text(get_help_msg("ᴀ ᴄ ᴛ ɪ ᴏ ɴ   ᴄ ᴏ ᴍ ᴍ ᴀ ɴ ᴅ ꜱ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass

    elif action == "font":
        content = "• <code>/font</code> [ᴛᴇxᴛ] » ᴄʜᴀɴɢᴇ ꜰᴏɴᴛꜱ ᴏꜰ ᴀɴʏ ᴛᴇxᴛ."
        markup = get_back_button(origin)
        if callback_query.message.photo or callback_query.message.video or callback_query.message.document:
            try: await callback_query.edit_message_caption(caption=get_help_msg("ꜰ ᴏ ɴ ᴛ   ᴍ ᴏ ᴅ ᴜ ʟ ᴇ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        else:
            try: await callback_query.edit_message_text(get_help_msg("ꜰ ᴏ ɴ ᴛ   ᴍ ᴏ ᴅ ᴜ ʟ ᴇ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass

    elif action == "fun":
        content = """• <code>/wish</code> » ᴀᴅᴅ ʏᴏᴜʀ ᴡɪꜱʜ.\n• <code>/sigma</code> » ᴄʜᴇᴄᴋ ʏᴏᴜʀ ꜱɪɢᴍᴀɴᴇꜱꜱ.\n• <code>/cute</code> » ᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴄᴜᴛᴇɴᴇꜱꜱ."""
        markup = get_back_button(origin)
        if callback_query.message.photo or callback_query.message.video or callback_query.message.document:
            try: await callback_query.edit_message_caption(caption=get_help_msg("ꜰ ᴜ ɴ   ᴍ ᴏ ᴅ ᴜ ʟ ᴇ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        else:
            try: await callback_query.edit_message_text(get_help_msg("ꜰ ᴜ ɴ   ᴍ ᴏ ᴅ ᴜ ʟ ᴇ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass

    elif action == "quotly":
        content = """• <code>/q</code> » ᴄʀᴇᴀᴛᴇ ᴀ Qᴜᴏᴛᴇ ꜰʀᴏᴍ ᴛʜᴇ ᴍᴇꜱꜱᴀɢᴇ.\n• <code>/q r</code> » ᴄʀᴇᴀᴛᴇ ᴀ Qᴜᴏᴛᴇ ᴡɪᴛʜ ʀᴇᴘʟʏ."""
        markup = get_back_button(origin)
        if callback_query.message.photo or callback_query.message.video or callback_query.message.document:
            try: await callback_query.edit_message_caption(caption=get_help_msg("Q ᴜ ᴏ ᴛ ʟ ʏ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        else:
            try: await callback_query.edit_message_text(get_help_msg("Q ᴜ ᴏ ᴛ ʟ ʏ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
    
    elif action == "blusers":
        content = """• <code>/blacklist</code> » ʙʟᴀᴄᴋʟɪꜱᴛ ᴀ ᴜꜱᴇʀ ꜰʀᴏᴍ ᴛʜᴇ ʙᴏᴛ.\n• <code>/whitelist</code> » ᴡʜɪᴛᴇʟɪꜱᴛ ᴛʜᴇ ʙʟᴀᴄᴋʟɪꜱᴛᴇᴅ ᴜꜱᴇʀ.\n• <code>/blacklistedusers</code> » ꜱʜᴏᴡꜱ ᴛʜᴇ ʟɪꜱᴛ ᴏꜰ ʙʟ-ᴜꜱᴇʀꜱ."""
        markup = get_back_button(origin)
        if callback_query.message.photo or callback_query.message.video or callback_query.message.document:
            try: await callback_query.edit_message_caption(caption=get_help_msg("ᴜ ꜱ ᴇ ʀ   ʙ ʟ ᴀ ᴄ ᴋ ʟ ɪ ꜱ ᴛ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass
        else:
            try: await callback_query.edit_message_text(get_help_msg("ᴜ ꜱ ᴇ ʀ   ʙ ʟ ᴀ ᴄ ᴋ ʟ ɪ ꜱ ᴛ", content), reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except: pass