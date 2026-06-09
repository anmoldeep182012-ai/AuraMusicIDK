import time
import random
from pyrogram import Client, filters
from pyrogram.types import Message
from database.db import db
from helpers.styling import small_caps, fraktur

@Client.on_message(filters.command(["wallet", "bal"]))
async def wallet_handler(client: Client, message: Message):
    user_id = message.from_user.id
    balance = await db.get_balance(user_id)
    
    header = fraktur("Your Wallet")
    await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                             f"<blockquote>{small_caps('ʙᴀʟᴀɴᴄᴇ')}: {balance} {small_caps('ᴄᴏɪɴꜱ')}</blockquote>")

@Client.on_message(filters.command("daily"))
async def daily_handler(client: Client, message: Message):
    user_id = message.from_user.id
    last_claim = await db.get_daily_claim(user_id)
    current_time = int(time.time())
    
    if current_time - last_claim < 86400:
        remaining = 86400 - (current_time - last_claim)
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        return await message.reply_text(small_caps(f"ʏᴏᴜ ᴀʟʀᴇᴀᴅʏ ᴄʟᴀɪᴍᴇᴅ ʏᴏᴜʀ ᴅᴀɪʟʏ ᴄᴏɪɴꜱ. ᴛʀʏ ᴀɢᴀɪɴ ɪɴ {hours}ʜ {minutes}ᴍ."))
    
    reward = random.randint(500, 2000)
    await db.update_balance(user_id, reward)
    await db.set_daily_claim(user_id, current_time)
    
    header = fraktur("Daily Reward")
    await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                             f"<blockquote>{small_caps('ʏᴏᴜ ʀᴇᴄᴇɪᴠᴇᴅ')}: {reward} {small_caps('ᴄᴏɪɴꜱ')}</blockquote>")

@Client.on_message(filters.command("pay"))
async def pay_handler(client: Client, message: Message):
    if not message.reply_to_message or len(message.command) < 2:
        return await message.reply_text(small_caps("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴡɪᴛʜ ᴛʜᴇ ᴀᴍᴏᴜɴᴛ ᴛᴏ ᴘᴀʏ.\nᴜꜱᴀɢᴇ: /ᴘᴀʏ <ᴀᴍᴏᴜɴᴛ>"))
    
    try:
        amount = int(message.command[1])
        if amount <= 0: return await message.reply_text(small_caps("ᴀᴍᴏᴜɴᴛ ᴍᴜꜱᴛ ʙᴇ ᴘᴏꜱɪᴛɪᴠᴇ."))
        
        sender_id = message.from_user.id
        receiver_id = message.reply_to_message.from_user.id
        
        sender_balance = await db.get_balance(sender_id)
        if sender_balance < amount:
            return await message.reply_text(small_caps("ɪɴꜱᴜꜰꜰɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ."))
        
        await db.update_balance(sender_id, -amount)
        await db.update_balance(receiver_id, amount)
        
        header = fraktur("Payment Successful")
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{small_caps('ꜱᴇɴᴛ')}: {amount} {small_caps('ᴄᴏɪɴꜱ')} ᴛᴏ {message.reply_to_message.from_user.mention}</blockquote>")
    except ValueError:
        await message.reply_text(small_caps("ɪɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ."))

@Client.on_message(filters.command("rob"))
async def rob_handler(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text(small_caps("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴛᴏ ʀᴏʙ ᴛʜᴇᴍ."))
    
    robber_id = message.from_user.id
    victim_id = message.reply_to_message.from_user.id
    
    if robber_id == victim_id:
        return await message.reply_text(small_caps("ʏᴏᴜ ᴄᴀɴɴᴏᴛ ʀᴏʙ ʏᴏᴜʀꜱᴇʟꜰ."))
    
    victim_balance = await db.get_balance(victim_id)
    if victim_balance < 500:
        return await message.reply_text(small_caps("ᴠɪᴄᴛɪᴍ ɪꜱ ᴛᴏᴏ ᴘᴏᴏʀ ᴛᴏ ʙᴇ ʀᴏʙʙᴇᴅ."))
    
    success = random.choice([True, False, False]) # 33% success rate
    if success:
        amount = random.randint(100, victim_balance // 2)
        await db.update_balance(robber_id, amount)
        await db.update_balance(victim_id, -amount)
        header = fraktur("Robbery Successful")
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{small_caps('ʏᴏᴜ ꜱᴛᴏʟᴇ')}: {amount} {small_caps('ᴄᴏɪɴꜱ')} ꜰʀᴏᴍ {message.reply_to_message.from_user.mention}</blockquote>")
    else:
        fine = 500
        await db.update_balance(robber_id, -fine)
        header = fraktur("Robbery Failed")
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{small_caps('ʏᴏᴜ ᴡᴇʀᴇ ᴄᴀᴜɢʜᴛ ᴀɴᴅ ꜰɪɴᴇᴅ')}: {fine} {small_caps('ᴄᴏɪɴꜱ')}</blockquote>")

@Client.on_message(filters.command("toprich"))
async def toprich_handler(client: Client, message: Message):
    top = await db.get_top_rich()
    if not top: return await message.reply_text(small_caps("ɴᴏ ᴅᴀᴛᴀ ꜰᴏᴜɴᴅ."))
    
    body = ""
    for i, (user_id, balance) in enumerate(top, 1):
        try:
            user = await client.get_users(user_id)
            name = user.first_name
        except:
            name = f"User {user_id}"
        body += f"{i}. {small_caps(name)}: {balance}\n"
    
    header = fraktur("Richest Users")
    await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                             f"<blockquote>{body}</blockquote>")

@Client.on_message(filters.command("topkills"))
async def topkills_handler(client: Client, message: Message):
    top = await db.get_top_kills()
    if not top: return await message.reply_text(small_caps("ɴᴏ ᴅᴀᴛᴀ ꜰᴏᴜɴᴅ."))
    
    body = ""
    for i, (user_id, kills) in enumerate(top, 1):
        try:
            user = await client.get_users(user_id)
            name = user.first_name
        except:
            name = f"User {user_id}"
        body += f"{i}. {small_caps(name)}: {kills}\n"
    
    header = fraktur("Top Killers")
    await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                             f"<blockquote>{body}</blockquote>")
