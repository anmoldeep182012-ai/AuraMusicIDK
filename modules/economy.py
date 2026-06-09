import time
import random
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from database.db import db
from helpers.styling import small_caps, fraktur

@Client.on_message(filters.command(["wallet", "bal"]))
async def wallet_handler(client: Client, message: Message):
    user = None
    if message.reply_to_message and message.reply_to_message.from_user:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        arg = message.command[1]
        try:
            if arg.isdigit():
                user = await client.get_users(int(arg))
            else:
                user = await client.get_users(arg)
        except Exception:
            return await message.reply_text(small_caps("ᴜꜱᴇʀ ɴᴏᴛ ꜰᴏᴜɴᴅ."))
            
    if not user:
        user = message.from_user
        
    user_id = user.id
    balance = await db.get_balance(user_id)
    
    if user_id == message.from_user.id:
        header = fraktur("Your Wallet")
    else:
        header = fraktur(f"{user.first_name}'s Wallet")
        
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
        if amount <= 0: return await message.reply_text(small_caps("ᴀᴍᴏᴜᴛ ᴍᴜꜱᴛ ʙᴇ ᴘᴏꜱɪᴛɪᴠᴇ."))
        
        sender_id = message.from_user.id
        
        if not message.reply_to_message.from_user:
            return await message.reply_text(small_caps("ᴄᴀɴɴᴏᴛ ᴛʀᴀɴꜱꜰᴇʀ ᴄᴏɪɴꜱ ᴛᴏ ᴛʜɪꜱ ᴇɴᴛɪᴛʏ."))
            
        if message.reply_to_message.from_user.is_bot:
            return await message.reply_text(small_caps("ʏᴏᴜ ᴄᴀɴɴᴏᴛ ᴛʀᴀɴꜱꜰᴇʀ ᴄᴏɪɴꜱ ᴛᴏ ᴀ ʙᴏᴛ."))
            
        receiver_id = message.reply_to_message.from_user.id
        
        if sender_id == receiver_id:
            return await message.reply_text(small_caps("ʏᴏᴜ ᴄᴀɴɴᴏᴛ ᴛʀᴀɴꜱꜰᴇʀ ᴄᴏɪɴꜱ ᴛᴏ ʏᴏᴜʀꜱᴇʟꜰ."))
        
        sender_balance = await db.get_balance(sender_id)
        if sender_balance < amount:
            return await message.reply_text(small_caps("ɪɴ<b>ꜱ</b>ᴜꜰꜰɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ."))
        
        await db.update_balance(sender_id, -amount)
        await db.update_balance(receiver_id, amount)
        
        header = fraktur("Payment Successful")
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                             f"<blockquote>{small_caps('<b>ꜱᴇɴᴛ</b>')}: {amount} {small_caps('<b>ᴄᴏɪɴꜱ</b>')} ᴛᴏ {message.reply_to_message.from_user.mention}</blockquote>")
    except ValueError:
        await message.reply_text(small_caps("ɪɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ."))

@Client.on_message(filters.command("rob"))
async def rob_handler(client: Client, message: Message):
    victim = None
    requested_amount = None
    
    if message.reply_to_message and message.reply_to_message.from_user:
        victim = message.reply_to_message.from_user
        if len(message.command) > 1:
            try:
                requested_amount = int(message.command[1])
            except ValueError:
                return await message.reply_text(small_caps("ɪɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ."))
    elif len(message.command) > 1:
        arg = message.command[1]
        try:
            if arg.isdigit():
                victim = await client.get_users(int(arg))
            else:
                victim = await client.get_users(arg)
        except Exception:
            return await message.reply_text(small_caps("ᴜꜱᴇʀ ɴᴏᴛ ꜰᴏᴜɴᴅ."))

    if not victim:
        return await message.reply_text(small_caps("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴏʀ ꜱᴘᴇᴄɪꜰʏ ᴜꜱᴇʀ ɪᴅ/ᴜꜱᴇʀɴᴀᴍᴇ ᴛᴏ ʀᴏʙ ᴛʜᴇᴍ."))
        
    if victim.is_bot:
        return await message.reply_text(small_caps("ʏᴏᴜ ᴄᴀɴɴᴏᴛ ʀᴏʙ ᴀ ʙᴏᴛ."))
    
    robber_id = message.from_user.id
    victim_id = victim.id
    
    if robber_id == victim_id:
        return await message.reply_text(small_caps("ʏᴏᴜ ᴄᴀɴɴᴏᴛ ʀᴏʙ ʏᴏᴜʀ<b>ꜱ</b>ᴇʟꜰ."))
        
    protection_until = await db.get_protection(victim_id)
    if protection_until > int(time.time()):
        return await message.reply_text(small_caps("ᴛʜɪꜱ ᴜꜱᴇʀ ʜᴀꜱ ᴀᴄᴛɪᴠᴇ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ."))
    
    victim_balance = await db.get_balance(victim_id)
    if victim_balance < 500:
        return await message.reply_text(small_caps("ᴠɪᴄᴛɪᴍ ɪꜱ ᴛᴏᴏ ᴘᴏᴏʀ ᴛᴏ ʙᴇ ʀᴏʙʙᴇᴅ."))
        
    if requested_amount is not None:
        if requested_amount <= 0:
            return await message.reply_text(small_caps("ᴀᴍᴏᴜɴᴛ ᴍᴜꜱᴛ ʙᴇ ᴘᴏꜱɪᴛɪᴠᴇ."))
        if requested_amount < 100:
            return await message.reply_text(small_caps("ᴍɪɴɪᴍᴜᴍ ʀᴏʙʙᴇʀʏ ᴀᴍᴏᴜɴᴛ ɪꜱ 100 ᴄᴏɪɴꜱ."))
        max_allowed = victim_balance // 2
        if requested_amount > max_allowed:
            return await message.reply_text(small_caps(f"ʏᴏᴜ ᴄᴀɴ ᴏɴʟʏ ʀᴏʙ ᴜᴘ ᴛᴏ {max_allowed} ᴄᴏɪɴꜱ (50%)."))
    
    success = True  # 100% success rate
    if success:
        if requested_amount is not None:
            amount = requested_amount
        else:
            amount = random.randint(100, victim_balance // 2)
            
        await db.update_balance(robber_id, amount)
        await db.update_balance(victim_id, -amount)
        header = fraktur("Robbery Successful")
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{small_caps('ʏᴏᴜ ꜱᴛᴏʟᴇ')}: {amount} {small_caps('ᴄᴏɪɴꜱ')} ꜰʀᴏᴍ {victim.mention}</blockquote>")
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

@Client.on_message(filters.command("kill"))
async def kill_handler(client: Client, message: Message):
    victim = None
    if message.reply_to_message and message.reply_to_message.from_user:
        victim = message.reply_to_message.from_user
    elif len(message.command) > 1:
        arg = message.command[1]
        try:
            if arg.isdigit():
                victim = await client.get_users(int(arg))
            else:
                victim = await client.get_users(arg)
        except Exception:
            return await message.reply_text(small_caps("ᴜꜱᴇʀ ɴᴏᴛ ꜰᴏᴜɴᴅ."))

    if not victim:
        return await message.reply_text(small_caps("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴏʀ ꜱᴘᴇᴄɪꜰʏ ᴜꜱᴇʀ ɪᴅ/ᴜꜱᴇʀɴᴀᴍᴇ ᴛᴏ ᴋɪʟʟ ᴛʜᴇᴍ."))
        
    if victim.is_bot:
        return await message.reply_text(small_caps("ʏᴏᴜ ᴄᴀɴɴᴏᴛ ᴋɪʟʟ ᴀ ʙᴏᴛ."))
        
    killer_id = message.from_user.id
    victim_id = victim.id
    
    if killer_id == victim_id:
        return await message.reply_text(small_caps("ʏᴏᴜ ᴄᴀɴɴᴏᴛ ᴋɪʟʟ ʏᴏᴜʀꜱᴇʟꜰ."))
        
    # Check protection
    protection_until = await db.get_protection(victim_id)
    if protection_until > int(time.time()):
        return await message.reply_text(small_caps("ᴛʜɪꜱ ᴜꜱᴇʀ ɪꜱ ᴘʀᴏᴛᴇᴄᴛᴇᴅ!"))
        
    coins_earned = random.randint(50, 200)
    xp_earned = random.randint(5, 15)
    
    # Try to deduct from victim balance up to the coins earned
    victim_balance = await db.get_balance(victim_id)
    deduct = min(victim_balance, coins_earned)
    await db.update_balance(victim_id, -deduct)
    
    await db.update_balance(killer_id, coins_earned)
    await db.update_xp(killer_id, xp_earned)
    await db.add_kill(killer_id)
    
    # Format the message exactly as requested
    killer_mention = message.from_user.mention
    victim_mention = victim.mention
    
    response = (
        f"👤 ㅤ ㅤㅤ {killer_mention} Kɪʟʟᴇᴅ {victim_mention}\n"
        f"💰 Eᴀʀɴᴇᴅ: ${coins_earned}, +{xp_earned} Xᴘ"
    )
    await message.reply_text(response)

@Client.on_message(filters.command("protect"))
async def protect_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴘʀᴏᴛᴇᴄᴛ <ᴅᴜʀᴀᴛɪᴏɴ> (ᴇ.ɢ. 1ᴅ)"))
        
    arg = message.command[1].lower()
    days = 0
    if arg.endswith("d"):
        try:
            days = int(arg[:-1])
        except ValueError:
            return await message.reply_text(small_caps("ɪɴᴠᴀʟɪᴅ ᴅᴜʀᴀᴛɪᴏɴ ꜰᴏʀᴍᴀᴛ. ᴜꜱᴇ ᴇ.ɢ. 1ᴅ."))
    else:
        try:
            days = int(arg)
        except ValueError:
            return await message.reply_text(small_caps("ɪɴᴠᴀʟɪᴅ ᴅᴜʀᴀᴛɪᴏɴ ꜰᴏʀᴍᴀᴛ. ᴜꜱᴇ ᴇ.ɢ. 1ᴅ."))

    if days <= 0:
        return await message.reply_text(small_caps("ᴅᴜʀᴀᴛɪᴏɴ ᴍᴜꜱᴛ ʙᴇ ᴘᴏꜱɪᴛɪᴠᴇ."))

    user_id = message.from_user.id
    is_premium = await db.is_premium(user_id)

    if days > 1 and not is_premium:
        msg = "❗ Nᴏʀᴍᴀʟ Uꜱᴇʀꜱ Cᴀɴ Oɴʟʏ Uꜱᴇ: 1ᴅ\n💓 Uᴘɢʀᴀ德 Tᴏ Pʀᴇᴍɪᴜᴍ: /pay_premium"
        return await message.reply_text(msg)

    if days > 2:
        # Premium limit is 2d max
        return await message.reply_text(small_caps("ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀꜱ ᴄᴀɴ ᴏɴʟʏ ᴜꜱᴇ ᴜᴘ ᴛᴏ 2ᴅ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ."))

    current_time = int(time.time())
    expiry = current_time + (days * 86400)
    await db.set_protection(user_id, expiry)
    
    await message.reply_text(small_caps(f"ᴘʀᴏᴛᴇᴄᴛɪᴏɴ ᴀᴄᴛɪᴠᴀᴛᴇᴅ ꜰᴏʀ {days}ᴅ!"))

@Client.on_message(filters.command("pay_premium"))
async def pay_premium_handler(client: Client, message: Message):
    user_id = message.from_user.id
    is_premium = await db.is_premium(user_id)
    if is_premium:
        return await message.reply_text(small_caps("ʏᴏᴜ ᴀʀᴇ ᴀʟʀᴇᴀᴅʏ ᴀ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀ!"))
        
    balance = await db.get_balance(user_id)
    cost = 5000
    if balance < cost:
        return await message.reply_text(small_caps(f"ɪɴꜱᴜꜰꜰɪᴄɪᴇɴᴛ ᴄᴏɪɴꜱ. ᴘʀᴇᴍɪᴜᴍ ᴄᴏꜱᴛꜱ {cost} ᴄᴏɪɴꜱ."))
        
    await db.update_balance(user_id, -cost)
    await db.set_premium(user_id, True)
    
    await message.reply_text("💓 Uᴘɢʀᴀᴅᴇ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ! ʏᴏᴜ ᴀʀᴇ ɴᴏᴡ ᴀ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀ.")

@Client.on_message(filters.command(["create_coupon", "createcoupon"]))
async def create_coupon_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴄʀᴇᴀᴛᴇ_ᴄᴏᴜᴘᴏɴ <ᴄᴏɪɴꜱ>"))
        
    try:
        coins = int(message.command[1])
    except ValueError:
        return await message.reply_text(small_caps("ɪɴᴠᴀʟɪᴅ ᴄᴏɪɴ ᴀᴍᴏᴜɴᴛ."))
        
    if coins <= 0:
        return await message.reply_text(small_caps("ᴄᴏɪɴ ᴀᴍᴏᴜɴᴛ ᴍᴜꜱᴛ ʙᴇ ᴘᴏꜱɪᴛɪᴠᴇ."))
        
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return
        
    balance = await db.get_balance(user_id)
    if balance < coins:
        return await message.reply_text(small_caps("ɪɴꜱᴜꜰꜰɪᴄɪᴇɴᴛ ᴄᴏɪɴꜱ ᴛᴏ ᴄʀᴇᴀᴛᴇ ᴄᴏᴜᴘᴏɴ."))
        
    # Deduct from balance
    await db.update_balance(user_id, -coins)
    
    # Generate unique code
    import string
    import secrets
    chars = string.ascii_uppercase + string.digits
    while True:
        code = f"AURALYX-{''.join(secrets.choice(chars) for _ in range(8))}"
        existing = await db.get_coupon(code)
        if not existing:
            break
            
    await db.create_coupon(code, coins, user_id, int(time.time()))
    
    header = fraktur("Coupon Created")
    body = f"» {small_caps('ᴄᴏᴅᴇ')}: <code>{code}</code>\n" \
           f"» {small_caps('ᴠᴀʟᴜᴇ')}: {coins} {small_caps('ᴄᴏɪɴꜱ')}"
           
    await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                             f"<blockquote>{body}</blockquote>")

@Client.on_message(filters.command(["coupon", "coupons"]))
async def claim_coupon_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(small_caps("ᴜꜱᴀɢᴇ: /ᴄᴏᴜᴘᴏɴ <ᴄᴏᴜᴘᴏɴ_ᴄᴏᴅᴇ>"))
        
    code = message.command[1].strip().upper()
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return
        
    coupon = await db.get_coupon(code)
    if not coupon:
        return await message.reply_text(small_caps("ɪɴᴠᴀʟɪᴅ ᴄᴏᴜᴘᴏɴ ᴄᴏᴅᴇ."))
        
    if coupon["claimed_by"] is not None:
        return await message.reply_text(small_caps("ᴛʜɪꜱ ᴄᴏᴜᴘᴏɴ ʜᴀꜱ ᴀʟʀᴇᴀᴅʏ ʙᴇᴇɴ ᴄʟᴀɪᴍᴇᴅ."))
        
    if coupon["creator_id"] == user_id:
        return await message.reply_text(small_caps("ʏᴏᴜ ᴄᴀɴɴᴏᴛ ᴄʟᴀɪᴍ ʏᴏᴜʀ ᴏᴡɴ ᴄᴏᴜᴘᴏɴ."))
        
    # Check expiry (24 hours = 86400 seconds)
    created_at = coupon.get("created_at") or 0
    if created_at > 0 and (int(time.time()) - created_at) > 86400:
        return await message.reply_text(small_caps("ᴛʜɪꜱ ᴄᴏᴜᴘᴏɴ ʜᴀꜱ ᴇxᴘɪʀᴇᴅ."))
        
    # Claim it
    await db.claim_coupon(code, user_id, int(time.time()))
    await db.update_balance(user_id, coupon["coins"])
    
    header = fraktur("Coupon Claimed")
    body = f"» {small_caps('ʏᴏᴜ ʀᴇᴄᴇɪᴠᴇᴅ')}: {coupon['coins']} {small_caps('ᴄᴏɪɴꜱ')}"
    
    await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                             f"<blockquote>{body}</blockquote>")

@Client.on_message(filters.new_chat_members)
async def bot_added_to_group_handler(client: Client, message: Message):
    if not message.new_chat_members:
        return
    try:
        me = await client.get_me()
    except Exception:
        return
    for member in message.new_chat_members:
        if member.id == me.id:
            inviter_id = message.from_user.id if message.from_user else None
            if inviter_id:
                await db.save_group_inviter(message.chat.id, inviter_id)
            break

@Client.on_message(filters.command("claim"))
async def claim_invite_reward_handler(client: Client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return
        
    if message.chat.type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text(small_caps("ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴄᴀɴ ᴏɴʟʏ ʙᴇ ᴜꜱᴇᴅ ɪɴ ɢʀᴏᴜᴘꜱ."))
        
    record = await db.get_group_claim(chat_id)
    inviter_id = None
    claimed = 0
    if record:
        inviter_id = record["inviter_id"]
        claimed = record["claimed"]
    else:
        # Fallback: Find group creator
        try:
            async for m in client.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
                if m.status == enums.ChatMemberStatus.OWNER:
                    inviter_id = m.user.id
                    await db.save_group_inviter(chat_id, inviter_id)
                    break
        except Exception:
            pass
            
    if not inviter_id:
        return await message.reply_text(small_caps("ᴜɴᴀʙʟᴇ ᴛᴏ ᴅᴇᴛᴇʀᴍɪɴᴇ ᴡʜᴏ ᴀᴅᴅᴇᴅ ᴛʜᴇ ʙᴏᴛ."))
        
    if user_id != inviter_id:
        return await message.reply_text(small_caps("ᴏɴʟʏ ᴛʜᴇ ᴜꜱᴇʀ ᴡʜᴏ ᴀᴅᴅᴇᴅ ᴛʜᴇ ʙᴏᴛ ᴄᴀɴ ᴄʟᴀɪᴍ ᴛʜɪꜱ ʀᴇᴡᴀʀᴅ."))
        
    if claimed == 1:
        return await message.reply_text(small_caps("ᴛʜᴇ ɪɴᴠɪᴛᴇ ʀᴇᴡᴀʀᴅ ꜰᴏʀ ᴛʜɪꜱ ɢʀᴏᴜᴘ ʜᴀꜱ ᴀʟʀᴇᴀᴅʏ ʙᴇᴇɴ ᴄʟᴀɪᴍᴇᴅ."))
        
    try:
        await db.mark_group_claimed(chat_id)
        await db.update_balance(user_id, 10000)
        
        header = fraktur("Reward Claimed")
        body = f"» {small_caps('ʏᴏᴜ ʀᴇᴄᴇɪᴠᴇᴅ')}: 10000 {small_caps('ᴄᴏɪɴꜱ ꜰᴏʀ ᴀᴅᴅɪɴɢ ᴛʜᴇ ʙᴏᴛ!')}"
        await message.reply_text(f"<blockquote>{header} ❞</blockquote>\n" \
                                 f"<blockquote>{body}</blockquote>")
    except Exception as e:
        await message.reply_text(f"<blockquote>{fraktur('Error')} ❞\n\n{small_caps(str(e))}</blockquote>")

