import json
import os
import time
import asyncio
from pyrogram import Client, enums
from pyrogram.errors import FloodWait

class AnimationEngine:
    def __init__(self):
        self._last_update = {}

    async def safe_edit(self, client: Client, chat_id: int, message_id: int, target_text: str, reply_markup=None):
        now = time.time()
        key = f"{chat_id}:{message_id}"
        
        # Enforce strict 1.5s rate mitigation window per active UI message
        if now - self._last_update.get(key, 0) < 1.5:
            return

        try:
            await client.edit_message_text(
                chat_id, 
                message_id, 
                target_text, 
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            )
            self._last_update[key] = now
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
            # Retry once after sleep
            try:
                await client.edit_message_text(chat_id, message_id, target_text, reply_markup=reply_markup)
            except:
                pass
        except Exception:
            pass

animator = AnimationEngine()

def convert_json_to_netscape(json_file: str, output_file: str):
    if not os.path.exists(json_file):
        return None
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        if not content:
            return None

        # Check if the file is already in Netscape format
        if "# Netscape HTTP Cookie File" in content or "\t" in content:
            out_dir = os.path.dirname(output_file)
            if out_dir and not os.path.exists(out_dir):
                os.makedirs(out_dir, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return output_file

        # Attempt to clean up copy-paste junk (e.g., line numbers like '1,' before '[')
        if not content.startswith('['):
            first_bracket = content.find('[')
            last_bracket = content.rfind(']')
            if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
                content = content[first_bracket:last_bracket+1]
                
        cookies = json.loads(content)
        
        # Ensure parent dir exists
        out_dir = os.path.dirname(output_file)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
            
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Netscape HTTP Cookie File\n")
            f.write("# http://curl.haxx.se/rfc/cookie_spec.html\n")
            f.write("# This is a generated file!  Do not edit.\n\n")
            
            for cookie in cookies:
                domain = cookie.get('domain', '')
                flag = 'TRUE' if domain.startswith('.') else 'FALSE'
                path = cookie.get('path', '/')
                secure = 'TRUE' if cookie.get('secure', False) else 'FALSE'
                
                # Gracefully convert expiration to integer
                exp_val = cookie.get('expirationDate', 0)
                try:
                    expiration = int(float(exp_val))
                except (ValueError, TypeError):
                    expiration = 0
                    
                name = cookie.get('name', '')
                value = cookie.get('value', '')
                
                if not name: continue
                
                f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expiration}\t{name}\t{value}\n")
        
        return output_file
    except Exception as e:
        print(f"Cookie Conversion Error: {e}")
        return None

async def sync_served_chats_from_userbot(userbot_client: Client):
    """Sync all groups, channels and private chats from userbot dialogs to the database."""
    try:
        from database.db import db
        from pyrogram import enums
        
        chat_count = 0
        user_count = 0
        
        async for dialog in userbot_client.get_dialogs():
            if not dialog.chat:
                continue
            chat_id = dialog.chat.id
            chat_type = dialog.chat.type
            
            if chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL]:
                if chat_id not in db._served_chats:
                    await db.add_served_chat(chat_id)
                    chat_count += 1
            elif chat_type == enums.ChatType.PRIVATE:
                if chat_id not in db._served_users:
                    await db.add_served_user(chat_id)
                    user_count += 1
                    
        print(f"Synced {chat_count} chats and {user_count} users from userbot dialogs.")
    except Exception as e:
        print(f"Error syncing dialogs: {e}")

