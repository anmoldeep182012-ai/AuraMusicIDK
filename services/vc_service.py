from pyrogram import Client, enums
from pyrogram.types import ChatPrivileges

async def ensure_admin_sync(client: Client, userbot: Client, chat_id: int):
    """Ensure Bot and Userbot promote each other if possible."""
    try:
        # Get Bot and Userbot info
        bot_me = await client.get_me()
        user_me = await userbot.get_me()
        
        # Get their member status
        bot_member = await client.get_chat_member(chat_id, bot_me.id)
        user_member = await client.get_chat_member(chat_id, user_me.id)
        
        # Case 1: Bot is Admin, Userbot is NOT
        if bot_member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            if bot_member.privileges and bot_member.privileges.can_promote_members:
                if user_member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                    await client.promote_chat_member(
                        chat_id, user_me.id,
                        privileges=ChatPrivileges(
                            can_manage_chat=True,
                            can_delete_messages=True,
                            can_manage_video_chats=True,
                            can_invite_users=True,
                            can_promote_members=False
                        )
                    )
        
        # Case 2: Userbot is Admin, Bot is NOT
        if user_member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            if user_member.privileges and user_member.privileges.can_promote_members:
                if bot_member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                    await userbot.promote_chat_member(
                        chat_id, bot_me.id,
                        privileges=ChatPrivileges(
                            can_manage_chat=True,
                            can_delete_messages=True,
                            can_manage_video_chats=True,
                            can_invite_users=True,
                            can_promote_members=True
                        )
                    )
    except Exception as e:
        print(f"Admin Sync Error: {e}")
