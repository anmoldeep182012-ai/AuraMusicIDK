import os
import random
import asyncio
import datetime
import json
import httpx
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from PIL import Image, ImageDraw, ImageFont, ImageOps
import base64
from config import Config
from database.db import db
from helpers.filters import admin, check_admin
from helpers.styling import small_caps, fraktur

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
        body = "ɪ ʟᴀᴄᴋ ᴛʜᴇ ɴᴇᴄᴇꜱꜱᴀʀʏ ᴀᴅᴍɪɴ ʀɪɢʜᴛꜱ. ᴇɴꜱᴜʀᴇ ɪ ᴀᴍ ᴘʀᴏᴍᴏᴛᴇᴅ ᴡɪᴛʜ ᴛʜᴇ ᴀᴘᴘʀᴏᴘʀɪᴀᴛᴇ ᴘᴇʀᴍɪꜱꜱɪᴏɴꜱ."
    else:
        body = f"ᴀɴ ᴜɴᴇxᴘᴇᴄᴛᴇᴅ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ: {error_str[:100]}"
    return f"<blockquote>\n{header} ❞\n\n{small_caps(body)}\n</blockquote>"

def prepare_sticker_file(input_path, output_path):
    with Image.open(input_path) as img:
        w, h = img.size
        if w > h:
            new_w = 512
            new_h = int(h * (512 / w))
        else:
            new_h = 512
            new_w = int(w * (512 / h))
            
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        img.save(output_path, "WEBP")

async def upload_sticker(user_id, pack_name, pack_title, file_path, emoji, bot_token):
    url_get = f"https://api.telegram.org/bot{bot_token}/getStickerSet"
    url_add = f"https://api.telegram.org/bot{bot_token}/addStickerToSet"
    
    async with httpx.AsyncClient() as client:
        res = await client.get(url_get, params={"name": pack_name})
        exists = res.status_code == 200
        
        with open(file_path, "rb") as f:
            files = {"sticker_file": f}
            
            if exists:
                sticker_obj = {
                    "sticker": "attach://sticker_file",
                    "emoji_list": [emoji]
                }
                data = {
                    "user_id": user_id,
                    "name": pack_name,
                    "sticker": json.dumps(sticker_obj)
                }
                response = await client.post(url_add, data=data, files=files)
            else:
                sticker_obj = {
                    "sticker": "attach://sticker_file",
                    "emoji_list": [emoji]
                }
                data = {
                    "user_id": user_id,
                    "name": pack_name,
                    "title": pack_title,
                    "stickers": json.dumps([sticker_obj]),
                    "sticker_format": "static"
                }
                url_create = f"https://api.telegram.org/bot{bot_token}/createNewStickerSet"
                response = await client.post(url_create, data=data, files=files)
                
        return response.status_code == 200, response.json()

def get_font(size):
    try:
        return ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", size)
    except:
        return ImageFont.load_default()

def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        try:
            bbox = font.getbbox(test_line)
            w = bbox[2] - bbox[0]
        except:
            w = len(test_line) * 8
        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(word)
                current_line = []
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def draw_initials_circle(draw, pos, size, name):
    colors = [
        (225, 112, 85, 255),
        (9, 132, 227, 255),
        (0, 184, 148, 255),
        (108, 92, 231, 255),
        (232, 67, 147, 255)
    ]
    color = colors[sum(ord(c) for c in name) % len(colors)]
    draw.ellipse((pos[0], pos[1], pos[0] + size[0], pos[1] + size[1]), fill=color)
    
    initial = name[0].upper() if name else "?"
    font = get_font(32)
    try:
        bbox = draw.textbbox((0, 0), initial, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
    except:
        w, h = 20, 25
    text_pos = (pos[0] + (size[0] - w) // 2, pos[1] + (size[1] - h) // 2 - 3)
    draw.text(text_pos, initial, fill=(255, 255, 255, 255), font=font)

def generate_quote_image_local(avatar_path, user_name, text, output_path, bg_color_hex="#1b1429"):
    try:
        hex_val = bg_color_hex.lstrip('#')
        if len(hex_val) == 3:
            hex_val = "".join(c*2 for c in hex_val)
        if len(hex_val) == 6:
            bg_color = (int(hex_val[0:2], 16), int(hex_val[2:4], 16), int(hex_val[4:6], 16), 255)
        else:
            bg_color = (24, 37, 51, 255)
    except:
        bg_color = (24, 37, 51, 255)

    name_font = get_font(18)
    text_font = get_font(16)
    
    max_text_width = 320
    lines = wrap_text(text, text_font, max_text_width)
    
    max_line_w = 0
    for line in lines:
        try:
            bbox = text_font.getbbox(line)
            line_w = bbox[2] - bbox[0]
        except:
            line_w = len(line) * 8
        max_line_w = max(max_line_w, line_w)
        
    try:
        bbox = name_font.getbbox(user_name)
        name_w = bbox[2] - bbox[0]
    except:
        name_w = len(user_name) * 10
        
    bubble_content_width = max(max_line_w, name_w)
    bubble_width = bubble_content_width + 32
    bubble_width = max(bubble_width, 150)
    bubble_width = min(bubble_width, 387)
    
    name_height = 20
    spacing = 6
    line_height = 18
    text_height = len(lines) * line_height
    
    bubble_padding_y = 12
    bubble_height = bubble_padding_y * 2 + name_height + spacing + text_height
    bubble_height = max(bubble_height, 80)
    
    width = 512
    height = bubble_height + 40
    
    if height > 512:
        height = 512
        bubble_height = height - 40
        
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    avatar_size = (70, 70)
    avatar_x = 20
    avatar_y = 20 + (bubble_height - avatar_size[1]) // 2
    avatar_pos = (avatar_x, avatar_y)
    
    bubble_x1 = 105
    bubble_y1 = 20
    bubble_x2 = bubble_x1 + bubble_width
    bubble_y2 = 20 + bubble_height
    
    draw.rounded_rectangle([bubble_x1, bubble_y1, bubble_x2, bubble_y2], radius=15, fill=bg_color)
    
    tail_polygon = [
        (bubble_x1, bubble_y2 - 20),
        (bubble_x1 - 10, bubble_y2 - 10),
        (bubble_x1, bubble_y2 - 5)
    ]
    draw.polygon(tail_polygon, fill=bg_color)
    
    if avatar_path and os.path.exists(avatar_path):
        try:
            avatar = Image.open(avatar_path).convert("RGBA")
            avatar = avatar.resize(avatar_size, Image.Resampling.LANCZOS)
            
            mask = Image.new("L", avatar_size, 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, avatar_size[0], avatar_size[1]), fill=255)
            
            circular_avatar = ImageOps.fit(avatar, avatar_size, centering=(0.5, 0.5))
            circular_avatar.putalpha(mask)
            
            img.alpha_composite(circular_avatar, avatar_pos)
        except:
            draw_initials_circle(draw, avatar_pos, avatar_size, user_name)
    else:
        draw_initials_circle(draw, avatar_pos, avatar_size, user_name)
        
    colors = [
        (82, 136, 193, 255),
        (79, 176, 80, 255),
        (225, 112, 85, 255),
        (108, 92, 231, 255)
    ]
    name_color = colors[sum(ord(c) for c in user_name) % len(colors)]
    draw.text((bubble_x1 + 16, bubble_y1 + bubble_padding_y), user_name, fill=name_color, font=name_font)
    
    current_y = bubble_y1 + bubble_padding_y + name_height + spacing
    for line in lines:
        draw.text((bubble_x1 + 16, current_y), line, fill=(255, 255, 255, 255), font=text_font)
        current_y += line_height
        
    img.save(output_path, "WEBP")

async def get_avatar_base64(client, user):
    try:
        photo = None
        if hasattr(user, "photo") and user.photo:
            photo = user.photo
        elif hasattr(user, "chat_photo") and user.chat_photo:
            photo = user.chat_photo
            
        if photo and photo.small_file_id:
            file_path = await client.download_media(photo.small_file_id)
            if file_path and os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    data = f.read()
                mime_type = "image/jpeg"
                if file_path.lower().endswith(".png"):
                    mime_type = "image/png"
                elif file_path.lower().endswith(".webp"):
                    mime_type = "image/webp"
                
                base64_str = base64.b64encode(data).decode("utf-8")
                try:
                    os.remove(file_path)
                except:
                    pass
                return f"data:{mime_type};base64,{base64_str}"
    except:
        pass
    return None

@Client.on_message(filters.command("staff"))
async def staff_list(client: Client, message: Message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return await message.reply_text(small_caps("ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴄᴀɴ ᴏɴʟʏ ʙᴇ ᴜꜱᴇᴅ ɪɴ ɢʀᴏᴜᴘꜱ."))
    chat_id = message.chat.id
    try:
        admins = []
        async for m in client.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
            if not m.user.is_bot:
                admins.append(m.user.mention)
        
        if not admins:
            return await message.reply_text(small_caps("ɴᴏ ᴀᴅᴍɪɴɪꜱᴛʀᴀᴛᴏʀꜱ ꜰᴏᴜɴᴅ."))
        
        body = "\n".join([f"• {a}" for a in admins])
        header = fraktur("Chat Staff")
        await message.reply_text(f"<blockquote>\n{header} ❞\n</blockquote>\n" \
                                 f"<blockquote>\n{body}\n</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>\n{small_caps('ᴇʀʀᴏʀ')} ❞\n\n{str(e)}\n</blockquote>")

@Client.on_message(filters.command("bots"))
async def bots_list(client: Client, message: Message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return await message.reply_text(small_caps("ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴄᴀɴ ᴏɴʟʏ ʙᴇ ᴜꜱᴇᴅ ɪɴ ɢʀᴏᴜᴘꜱ."))
    chat_id = message.chat.id
    m = await message.reply_text(small_caps("ꜰɪɴᴅɪɴɢ ʙᴏᴛꜱ..."))
    try:
        bots = []
        async for member in client.get_chat_members(chat_id):
            if member.user.is_bot:
                bots.append(f"• {member.user.mention} (<code>{member.user.id}</code>)")
        if not bots:
            await m.edit_text(small_caps("ɴᴏ ʙᴏᴛꜱ ꜰᴏᴜɴᴅ."))
        else:
            header = fraktur("Chat Bots")
            body = "\n".join(bots)
            await m.edit_text(f"<blockquote>\n{header} ❞\n</blockquote>\n<blockquote>\n{body}\n</blockquote>")
    except Exception as e:
        await m.edit_text(f"<blockquote>\n{fraktur('Error')} ❞\n\n{str(e)}\n</blockquote>")

@Client.on_message(filters.command("zombies") & filters.group)
async def zombies_clean(client: Client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None
    if user_id:
        is_admin = await check_admin(chat_id, user_id, client)
        if not is_admin:
            return await message.reply_text(small_caps("ᴀᴅᴍɪɴ ʀɪɢʜᴛꜱ ʀᴇQᴜɪʀᴇᴅ"))
            
    bot_me = await client.get_me()
    bot_member = await client.get_chat_member(chat_id, bot_me.id)
    if not bot_member.privileges or not bot_member.privileges.can_restrict_members:
        return await message.reply_text(small_caps("ɪ ɴᴇᴇᴅ 'restrict members' ᴘᴇʀᴍɪꜱꜱɪᴏɴ ᴛᴏ ᴄʟᴇᴀɴ ᴢᴏᴍʙɪᴇꜱ."))

    m = await message.reply_text(small_caps("ꜱᴄᴀɴɴɪɴɢ ꜰᴏʀ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛꜱ..."))
    try:
        zombies_count = 0
        async for member in client.get_chat_members(chat_id):
            if member.user.is_deleted:
                try:
                    await message.chat.ban_member(member.user.id)
                    await message.chat.unban_member(member.user.id)
                    zombies_count += 1
                except:
                    pass
        if zombies_count == 0:
            await m.edit_text(small_caps("ɴᴏ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛꜱ ꜰᴏᴜɴᴅ."))
        else:
            header = fraktur("Clean Up Completed")
            body = f"ʀᴇᴍᴏᴠᴇᴅ {zombies_count} ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛꜱ."
            await m.edit_text(f"<blockquote>\n{header} ❞\n\n{small_caps(body)}\n</blockquote>")
    except Exception as e:
        await m.edit_text(f"<blockquote>\n{fraktur('Error')} ❞\n\n{str(e)}\n</blockquote>")

@Client.on_message(filters.command("stickerid"))
async def sticker_id(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.sticker:
        return await message.reply_text(small_caps("ʀᴇᴘʟʏ ᴛᴏ ᴀ ꜱᴛɪᴄᴋᴇʀ ᴛᴏ ɢᴇᴛ ɪᴛꜱ ꜰɪʟᴇ ɪᴅ."))
    
    file_id = message.reply_to_message.sticker.file_id
    header = fraktur("Sticker Identifier")
    body = f"<code>{file_id}</code>"
    await message.reply_text(f"<blockquote>\n{header} ❞\n\n{body}\n</blockquote>")

@Client.on_message(filters.command(["kang", "packkang"]))
async def kang_sticker(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text(small_caps("ʀᴇᴘʟʏ ᴛᴏ ᴀ ꜱᴛɪᴄᴋᴇʀ ᴏʀ ᴀ ᴘʜᴏᴛᴏ ᴛᴏ ᴋᴀɴɢ."))
        
    replied = message.reply_to_message
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return await message.reply_text(small_caps("ᴄᴀɴɴᴏᴛ ɪᴅᴇɴᴛɪꜰʏ ᴜꜱᴇʀ."))
        
    emoji = "🤔"
    if len(message.command) > 1:
        emoji = message.command[1]
    elif replied.sticker:
        emoji = replied.sticker.emoji or "🤔"
        
    m = await message.reply_text(small_caps("ᴋᴀɴɢɪɴɢ ꜱᴛɪᴄᴋᴇʀ..."))
    
    try:
        if replied.sticker:
            if replied.sticker.is_animated or replied.sticker.is_video:
                return await m.edit_text(small_caps("ᴀɴɪᴍᴀᴛᴇᴅ ᴀɴᴅ ᴠɪᴅᴇᴏ ꜱᴛɪᴄᴋᴇʀꜱ ᴀʀᴇ ɴᴏᴛ ꜱᴜᴘᴘᴏʀᴛᴇᴅ."))
            raw_path = await client.download_media(replied)
            file_path = "downloads/temp_sticker.webp"
            if not os.path.exists("downloads"):
                os.makedirs("downloads")
            prepare_sticker_file(raw_path, file_path)
            try: os.remove(raw_path)
            except: pass
        elif replied.photo:
            raw_path = await client.download_media(replied)
            file_path = "downloads/temp_sticker.webp"
            if not os.path.exists("downloads"):
                os.makedirs("downloads")
            prepare_sticker_file(raw_path, file_path)
            try: os.remove(raw_path)
            except: pass
        else:
            return await m.edit_text(small_caps("ᴘʟᴇᴀꜱᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ꜱᴛɪᴄᴋᴇʀ ᴏʀ ᴀ ᴘʜᴏᴛᴏ."))
            
        bot_username = client.me.username
        pack_name = f"auralyx_{user_id}_by_{bot_username}"
        pack_title = f"Auralyx Sticker Pack Vol. {user_id}"
        
        success, res = await upload_sticker(user_id, pack_name, pack_title, file_path, emoji, Config.BOT_TOKEN)
        
        try: os.remove(file_path)
        except: pass
        
        if success:
            header = fraktur("Sticker Kanged")
            body = f"» {small_caps('ᴘᴀᴄᴋ')}: <a href=\"https://t.me/addstickers/{pack_name}\">{small_caps('ᴛᴀᴘ ᴛᴏ ᴀᴅᴅ')}</a>"
            await m.edit_text(f"<blockquote>\n{header} ❞\n</blockquote>\n<blockquote>\n{body}\n</blockquote>", parse_mode=enums.ParseMode.HTML)
        else:
            error_desc = res.get("description", "Unknown error")
            await m.edit_text(f"<blockquote>\n{fraktur('Failed')} ❞\n\n{small_caps(error_desc)}\n</blockquote>")
            
    except Exception as e:
        await m.edit_text(f"<blockquote>\n{fraktur('Error')} ❞\n\n{str(e)}\n</blockquote>")

@Client.on_message(filters.command("tagall") & admin)
async def tag_all_members(client: Client, message: Message):
    chat_id = message.chat.id
    m = await message.reply_text(small_caps("ᴛᴀɢɢɪɴɢ ᴍᴇᴍʙᴇʀꜱ..."))
    try:
        members = []
        async for member in client.get_chat_members(chat_id):
            if not member.user.is_bot and not member.user.is_deleted:
                members.append(member.user.mention)
        
        if not members:
            return await m.edit_text(small_caps("ɴᴏ ᴍᴇᴍʙᴇʀꜱ ᴛᴏ ᴛᴀɢ."))
            
        await m.delete()
        batch_size = 5
        for i in range(0, len(members), batch_size):
            batch = members[i:i+batch_size]
            tag_text = ", ".join(batch)
            await client.send_message(chat_id, f"» {tag_text}")
            await asyncio.sleep(1.5)
    except Exception as e:
        await client.send_message(chat_id, f"<blockquote>\n{fraktur('Error')} ❞\n\n{str(e)}\n</blockquote>")

@Client.on_message(filters.command("vctag") & admin)
async def vc_tag_members(client: Client, message: Message):
    chat_id = message.chat.id
    m = await message.reply_text(small_caps("ɪɴᴠɪᴛɪɴɢ ᴍᴇᴍʙᴇʀꜱ ᴛᴏ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ..."))
    try:
        members = []
        async for member in client.get_chat_members(chat_id):
            if not member.user.is_bot and not member.user.is_deleted:
                members.append(member.user.mention)
        
        if not members:
            return await m.edit_text(small_caps("ɴᴏ ᴍᴇᴍʙᴇʀꜱ ᴛᴏ ᴛᴀɢ."))
            
        await m.delete()
        batch_size = 5
        for i in range(0, len(members), batch_size):
            batch = members[i:i+batch_size]
            tag_text = ", ".join(batch)
            header = small_caps("ᴊᴏɪɴ ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ")
            await client.send_message(chat_id, f"» {header} : {tag_text}")
            await asyncio.sleep(1.5)
    except Exception as e:
        await client.send_message(chat_id, f"<blockquote>\n{fraktur('Error')} ❞\n\n{str(e)}\n</blockquote>")

@Client.on_message(filters.command("utag") & admin)
async def custom_tag_members(client: Client, message: Message):
    chat_id = message.chat.id
    if len(message.command) < 2:
        return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴜᴛᴀɢ <ᴛᴇxᴛ>"))
    
    custom_text = message.text.split(None, 1)[1]
    m = await message.reply_text(small_caps("ᴛᴀɢɢɪɴɢ ᴍᴇᴍʙᴇʀꜱ..."))
    try:
        members = []
        async for member in client.get_chat_members(chat_id):
            if not member.user.is_bot and not member.user.is_deleted:
                members.append(member.user.mention)
        
        if not members:
            return await m.edit_text(small_caps("ɴᴏ ᴍᴇᴍʙᴇʀꜱ ᴛᴏ ᴛᴀɢ."))
            
        await m.delete()
        batch_size = 5
        for i in range(0, len(members), batch_size):
            batch = members[i:i+batch_size]
            tag_text = ", ".join(batch)
            await client.send_message(chat_id, f"» {small_caps(custom_text)} : {tag_text}")
            await asyncio.sleep(1.5)
    except Exception as e:
        await client.send_message(chat_id, f"<blockquote>\n{fraktur('Error')} ❞\n\n{str(e)}\n</blockquote>")

@Client.on_message(filters.command("info"))
async def info_user(client: Client, message: Message):
    user = get_user_info(message)
    if not user:
        user = message.from_user
    
    try:
        if isinstance(user, str):
            user = await client.get_users(user)
        
        user_id = user.id
        first_name = user.first_name
        last_name = user.last_name or ""
        username = f"@{user.username}" if user.username else "ɴᴏɴᴇ"
        dc_id = user.dc_id or "ᴜɴᴋɴᴏᴡɴ"
        status = str(user.status).replace("UserStatus.", "").lower() if user.status else "ᴜɴᴋɴᴏᴡɴ"
        
        header = fraktur("User Information")
        body = f"» {small_caps('ɪᴅ')}: <code>{user_id}</code>\n" \
               f"» {small_caps('ꜰɪʀꜱᴛ ɴᴀᴍᴇ')}: {first_name}\n" \
               f"» {small_caps('ʟᴀꜱᴛ ɴᴀᴍᴇ')}: {last_name}\n" \
               f"» {small_caps('ᴜꜱᴇʀɴᴀᴍᴇ')}: {username}\n" \
               f"» {small_caps('ᴅᴄ ɪᴅ')}: {dc_id}\n" \
               f"» {small_caps('ꜱᴛᴀᴛᴜꜱ')}: {small_caps(status)}"
               
        await message.reply_text(f"<blockquote>\n{header} ❞\n</blockquote>\n" \
                                 f"<blockquote>\n{body}\n</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>\n{fraktur('Error')} ❞\n\n{str(e)}\n</blockquote>")

@Client.on_message(filters.command("font"))
async def font_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ꜰᴏɴᴛ <ᴛᴇxᴛ>"))
    
    input_text = message.text.split(None, 1)[1]
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("𝚃𝚢𝚙𝚎𝚠𝚛𝚒𝚝𝚎𝚛", callback_data="font_set:typewriter"),
            InlineKeyboardButton("𝕆𝕦𝕥𝕝𝕚𝕟𝕖", callback_data="font_set:outline"),
            InlineKeyboardButton("𝐒𝐞𝐫𝐢𝐟", callback_data="font_set:serif bold")
        ],
        [
            InlineKeyboardButton("𝑆𝑒𝑟𝑖𝑓", callback_data="font_set:serif italic"),
            InlineKeyboardButton("𝑺𝒆𝒓𝒊𝒇", callback_data="font_set:serif bold italic"),
            InlineKeyboardButton("ꜱᴍᴀʟʟ ᴄᴀᴘꜱ", callback_data="font_set:small caps")
        ],
        [
            InlineKeyboardButton("𝓈𝒸𝓇𝒾𝓅𝓉", callback_data="font_set:script"),
            InlineKeyboardButton("𝓼𝓬𝓻𝓲𝓹𝓽", callback_data="font_set:script bold"),
            InlineKeyboardButton("ᵗⁱⁿʸ", callback_data="font_set:tiny")
        ],
        [
            InlineKeyboardButton("🄲🄾🄼🄸🄲", callback_data="font_set:comic"),
            InlineKeyboardButton("𝖲𝖺𝗇𝗌", callback_data="font_set:sans"),
            InlineKeyboardButton("𝗦𝗮𝗻𝘀", callback_data="font_set:sans bold")
        ],
        [
            InlineKeyboardButton("𝘚𝘢𝘯𝘴", callback_data="font_set:sans italic"),
            InlineKeyboardButton("𝙎𝙖𝙣𝙨", callback_data="font_set:sans bold italic"),
            InlineKeyboardButton("ⒸⒾⓇⒸⓁⒺⓈ", callback_data="font_set:circles")
        ],
        [
            InlineKeyboardButton("🅒🅘🅡🅒🅛🅔🅢", callback_data="font_set:dark circles"),
            InlineKeyboardButton("𝔊𝔬𝔱𝔥𝔦𝔠", callback_data="font_set:gothic"),
            InlineKeyboardButton("𝕲𝖔𝖙𝖍𝖎𝖈", callback_data="font_set:gothic bold")
        ],
        [
            InlineKeyboardButton("C̳l̳o̳u̳d̳s̳", callback_data="font_set:clouds"),
            InlineKeyboardButton("H̶a̶p̶p̶y̶", callback_data="font_set:happy"),
            InlineKeyboardButton("S̳a̳d̳", callback_data="font_set:sad")
        ],
        [
            InlineKeyboardButton(small_caps("⌜ ᴄʟᴏꜱᴇ ⌟"), callback_data="font_close")
        ]
    ])
    
    await message.reply_text(input_text, reply_markup=buttons)

@Client.on_callback_query(filters.regex("^font_set:"))
async def font_callback_handler(client: Client, callback_query: CallbackQuery):
    if callback_query.message.reply_to_message:
        if callback_query.from_user.id != callback_query.message.reply_to_message.from_user.id:
            return await callback_query.answer(small_caps("ᴛʜɪꜱ ᴍᴇɴᴜ ɪꜱ ɴᴏᴛ ꜰᴏᴜɴᴅ ꜰᴏʀ ʏᴏᴜ."), show_alert=True)
            
    font_name = callback_query.data.split(":", 1)[1]
    current_text = callback_query.message.text
    if not current_text:
        return await callback_query.answer(small_caps("ɴᴏ ᴛᴇxᴛ ꜰᴏᴜɴᴅ."))
        
    from helpers.styling import apply_font
    new_text = apply_font(current_text, font_name)
    if new_text == current_text:
        return await callback_query.answer(small_caps("ᴛᴇxᴛ ɪꜱ ᴀʟʀᴇᴀᴅʏ ꜱᴛʏʟᴇᴅ."))
        
    try:
        await callback_query.edit_message_text(new_text, reply_markup=callback_query.message.reply_markup)
        await callback_query.answer(small_caps(f"ᴀᴘᴘʟɪᴇᴅ {font_name}"))
    except Exception as e:
        await callback_query.answer(f"Error: {e}")

@Client.on_callback_query(filters.regex("^font_close$"))
async def font_close_callback(client: Client, callback_query: CallbackQuery):
    if callback_query.message.reply_to_message:
        if callback_query.from_user.id != callback_query.message.reply_to_message.from_user.id:
            return await callback_query.answer(small_caps("ᴛʜɪꜱ ᴍᴇɴᴜ ɪꜱ ɴᴏᴛ ꜰᴏᴜɴᴅ ꜰᴏʀ ʏᴏᴜ."), show_alert=True)
    try:
        await callback_query.message.delete()
    except:
        pass

@Client.on_message(filters.command("wish"))
async def wish_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴡɪꜱʜ <ʏᴏᴜʀ ᴡɪꜱʜ>"))
        
    wish = message.text.split(None, 1)[1]
    percentage = random.randint(0, 100)
    await message.reply_text(f"ʜᴇʏ! {message.from_user.mention} ʏᴏᴜʀ ᴡɪꜱʜ: {wish}  ᴘᴏꜱꜱɪʙʟᴇ ᴛᴏ: {percentage}%")

@Client.on_message(filters.command("sigma"))
async def sigma_rating(client: Client, message: Message):
    user = get_user_info(message) or message.from_user
    if isinstance(user, str):
        user = await client.get_users(user)
        
    import datetime
    today = datetime.date.today().day
    local_rand = random.Random(user.id + today)
    rating = local_rand.randint(0, 100)
    
    header = fraktur("Sigma Indicator")
    body = f"» {small_caps('ᴜꜱᴇʀ')}: {user.mention}\n" \
           f"» {small_caps('ꜱɪɢᴍᴀ ʟᴇᴠᴇʟ')}: {rating}%"
           
    await message.reply_text(f"<blockquote>\n{header} ❞\n</blockquote>\n" \
                             f"<blockquote>\n{body}\n</blockquote>")

@Client.on_message(filters.command("cute"))
async def cute_rating(client: Client, message: Message):
    user = get_user_info(message) or message.from_user
    if isinstance(user, str):
        user = await client.get_users(user)
        
    import datetime
    today = datetime.date.today().day
    local_rand = random.Random(user.id + today + 99)
    rating = local_rand.randint(0, 100)
    
    header = fraktur("Cuteness Meter")
    body = f"» {small_caps('ᴜꜱᴇʀ')}: {user.mention}\n" \
           f"» {small_caps('ᴄᴜᴛᴇɴᴇꜱꜱ')}: {rating}%"
           
    await message.reply_text(f"<blockquote>\n{header} ❞\n</blockquote>\n" \
                             f"<blockquote>\n{body}\n</blockquote>")

@Client.on_message(filters.command(["q", "quote"]))
async def quote_message(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text(small_caps("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴛᴏ Qᴜᴏᴛᴇ ɪᴛ."))
        
    replied = message.reply_to_message
    chat_id = message.chat.id
    
    num_messages = 1
    bg_color = "#1b1429"
    
    for arg in message.command[1:]:
        if arg.startswith("#"):
            bg_color = arg
        elif arg.startswith("color="):
            bg_color = arg.split("=", 1)[1]
        else:
            try:
                num_messages = int(arg)
                if num_messages < 1:
                    num_messages = 1
                elif num_messages > 10:
                    num_messages = 10
            except ValueError:
                pass

    m = await message.reply_text(small_caps("ɢᴇɴᴇʀᴀᴛɪɴɢ Qᴜᴏᴛᴇ ꜱᴛɪᴄᴋᴇʀ..."))
    
    messages_to_quote = []
    if num_messages == 1:
        messages_to_quote = [replied]
    else:
        try:
            target_msgs = []
            async for msg in client.get_chat_history(
                chat_id=chat_id,
                offset_id=replied.id + 50,
                limit=100
            ):
                target_msgs.append(msg)
            
            filtered = [msg for msg in target_msgs if msg.id >= replied.id]
            filtered.sort(key=lambda x: x.id)
            messages_to_quote = filtered[:num_messages]
        except Exception:
            messages_to_quote = [replied]
            
    success = False
    temp_sticker_path = f"downloads/quote_{message.id}.webp"
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
        
    try:
        messages_payload = []
        avatar_cache = {}
        
        for msg in messages_to_quote:
            user = msg.from_user or msg.sender_chat
            user_id = user.id if user else 0
            
            first_name = ""
            last_name = ""
            username = ""
            
            if user:
                if msg.from_user:
                    first_name = msg.from_user.first_name or ""
                    last_name = msg.from_user.last_name or ""
                    username = msg.from_user.username or ""
                elif msg.sender_chat:
                    first_name = msg.sender_chat.title or ""
                    last_name = ""
                    username = msg.sender_chat.username or ""
            else:
                first_name = "Deleted Account"
                
            avatar_url = None
            if user_id:
                if user_id in avatar_cache:
                    avatar_url = avatar_cache[user_id]
                else:
                    avatar_url = await get_avatar_base64(client, user)
                    avatar_cache[user_id] = avatar_url
                    
            entities_list = []
            if msg.entities:
                for entity in msg.entities:
                    ent_type = str(entity.type).split(".")[-1].lower()
                    entities_list.append({
                        "type": ent_type,
                        "offset": entity.offset,
                        "length": entity.length
                    })
                    
            text = msg.text or msg.caption or ""
            if not text:
                if msg.sticker: text = "[Sticker]"
                elif msg.photo: text = "[Photo]"
                elif msg.video: text = "[Video]"
                elif msg.document: text = "[Document]"
                elif msg.voice: text = "[Voice Note]"
                elif msg.audio: text = "[Audio]"
                elif msg.animation: text = "[GIF]"
                elif msg.location: text = "[Location]"
                elif msg.poll: text = "[Poll]"
                elif msg.contact: text = "[Contact]"
                else: text = "[Media]"
                
            msg_payload = {
                "entities": entities_list,
                "avatar": True,
                "from": {
                    "id": user_id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "username": username
                },
                "text": text
            }
            if avatar_url:
                msg_payload["from"]["photo"] = {"url": avatar_url}
                
            if msg == messages_to_quote[0] and msg.reply_to_message:
                reply_msg = msg.reply_to_message
                reply_user = reply_msg.from_user or reply_msg.sender_chat
                reply_name = ""
                if reply_user:
                    if reply_msg.from_user:
                        reply_name = reply_msg.from_user.first_name or ""
                        if reply_msg.from_user.last_name:
                            reply_name += f" {reply_msg.from_user.last_name}"
                    elif reply_msg.sender_chat:
                        reply_name = reply_msg.sender_chat.title or ""
                else:
                    reply_name = "Unknown"
                    
                reply_text = reply_msg.text or reply_msg.caption or ""
                if not reply_text:
                    if reply_msg.sticker: reply_text = "[Sticker]"
                    elif reply_msg.photo: reply_text = "[Photo]"
                    elif reply_msg.video: reply_text = "[Video]"
                    elif reply_msg.document: reply_text = "[Document]"
                    elif reply_msg.voice: reply_text = "[Voice Note]"
                    elif reply_msg.audio: reply_text = "[Audio]"
                    elif reply_msg.animation: reply_text = "[GIF]"
                    elif reply_msg.location: reply_text = "[Location]"
                    elif reply_msg.poll: reply_text = "[Poll]"
                    elif reply_msg.contact: reply_text = "[Contact]"
                    else: reply_text = "[Media]"
                    
                msg_payload["replyMessage"] = {
                    "name": reply_name,
                    "text": reply_text,
                    "chatId": reply_msg.chat.id if reply_msg.chat else 0,
                    "id": reply_msg.id
                }
            messages_payload.append(msg_payload)
            
        api_payload = {
            "type": "quote",
            "format": "webp",
            "backgroundColor": bg_color,
            "messages": messages_payload
        }
        
        async with httpx.AsyncClient() as httpx_client:
            res = await httpx_client.post("https://bot.lyo.su/quote/generate.webp", json=api_payload, timeout=15)
            if res.status_code == 200:
                with open(temp_sticker_path, "wb") as f:
                    f.write(res.content)
                success = True
                
    except Exception:
        pass
        
    if not success:
        try:
            first_msg = messages_to_quote[0]
            first_user = first_msg.from_user or first_msg.sender_chat
            first_name = ""
            if first_user:
                if first_msg.from_user:
                    first_name = first_msg.from_user.first_name or "Unknown"
                elif first_msg.sender_chat:
                    first_name = first_msg.sender_chat.title or "Unknown"
            else:
                first_name = "Deleted Account"
                
            avatar_path = None
            if first_user:
                try:
                    photo = first_user.photo or getattr(first_user, "chat_photo", None)
                    if photo and photo.small_file_id:
                        avatar_path = await client.download_media(photo.small_file_id)
                except:
                    pass
                    
            fallback_text = ""
            for i, msg in enumerate(messages_to_quote):
                user = msg.from_user or msg.sender_chat
                name = user.first_name if user and hasattr(user, "first_name") else (user.title if user and hasattr(user, "title") else "Unknown")
                txt = msg.text or msg.caption or ""
                if not txt:
                    if msg.sticker: txt = "[Sticker]"
                    elif msg.photo: txt = "[Photo]"
                    elif msg.video: txt = "[Video]"
                    elif msg.document: txt = "[Document]"
                    else: txt = "[Media]"
                if i == 0:
                    fallback_text += txt
                else:
                    fallback_text += f"\n\n{name}: {txt}"
                    
            generate_quote_image_local(avatar_path, first_name, fallback_text, temp_sticker_path, bg_color)
            
            if avatar_path and os.path.exists(avatar_path):
                try: os.remove(avatar_path)
                except: pass
                
            success = True
        except Exception as e:
            await m.edit_text(f"<blockquote>\n{fraktur('Error')} ❞\n\n{small_caps(str(e)[:100])}\n</blockquote>")
            return

    if success and os.path.exists(temp_sticker_path):
        try:
            await message.reply_sticker(sticker=temp_sticker_path)
            await m.delete()
        except Exception as e:
            await m.edit_text(f"<blockquote>\n{fraktur('Error')} ❞\n\n{small_caps(str(e)[:100])}\n</blockquote>")
        finally:
            try: os.remove(temp_sticker_path)
            except: pass
    else:
        await m.edit_text(small_caps("ꜰᴀɪʟᴇᴅ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ Qᴜᴏᴛᴇ ꜱᴛɪᴄᴋᴇʀ."))
