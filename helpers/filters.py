from pyrogram import filters, enums, Client
from config import Config
from database.db import db

# Role IDs and global lists
OWNER_ID = Config.OWNER_ID

async def is_sudo(_, __, message):
    if not message.from_user:
        return False
    if message.from_user.id == OWNER_ID:
        return True
    sudoers = await db.get_sudoers()
    return message.from_user.id in sudoers or str(message.from_user.id) in sudoers

sudoers = filters.create(is_sudo)

async def is_admin(_, __, message):
    if not message.chat or message.chat.type not in [enums.ChatType.SUPERGROUP, enums.ChatType.GROUP]:
        return False
    
    user_id = message.from_user.id if message.from_user else None
    if not user_id: return False

    # Owner is always allowed
    if user_id == OWNER_ID:
        return True
    
    sudoers_list = await db.get_sudoers()
    if user_id in sudoers_list or str(user_id) in sudoers_list:
        # Determine if it's a control command or a moderation command
        cmd = None
        if message.text and message.text.startswith("/"):
            parts = message.text.split()
            if parts:
                cmd = parts[0][1:].split("@")[0].lower()
        elif message.caption and message.caption.startswith("/"):
            parts = message.caption.split()
            if parts:
                cmd = parts[0][1:].split("@")[0].lower()
                
        control_cmds = {"pause", "p", "resume", "r", "skip", "s", "next", "stop", "end", "cstop"}
        
        if cmd in control_cmds:
            if await db.check_sudo_perm(user_id, "control"):
                return True
        else:
            if await db.check_sudo_perm(user_id, "moderation"):
                return True
            
    # Check for Authorized Users in the chat
    auth_users = await db.get_auth_users(message.chat.id)
    if user_id in auth_users:
        return True
        
    # Standard admin check
    try:
        member = await message.chat.get_member(user_id)
        return member.status in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR]
    except:
        return False

async def check_admin(chat_id: int, user_id: int, client: Client = None, perm: str = "moderation") -> bool:
    """Helper to check if a user is admin/sudo/owner/auth in a chat."""
    if user_id == OWNER_ID:
        return True
    
    sudoers_list = await db.get_sudoers()
    if user_id in sudoers_list or str(user_id) in sudoers_list:
        if await db.check_sudo_perm(user_id, perm):
            return True
        
    auth_users = await db.get_auth_users(chat_id)
    if user_id in auth_users:
        return True
        
    if client:
        try:
            member = await client.get_chat_member(chat_id, user_id)
            return member.status in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR]
        except:
            return False
    return False

admin = filters.create(is_admin)
owner_only = filters.user(OWNER_ID)
