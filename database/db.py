import aiosqlite
import json
from config import Config

class Database:
    def __init__(self):
        self.db_path = Config.DB_PATH

    async def init(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)"
            )
            await db.execute(
                "CREATE TABLE IF NOT EXISTS sudoers (user_id INTEGER PRIMARY KEY)"
            )
            await db.execute(
                "CREATE TABLE IF NOT EXISTS warns (user_id INTEGER, chat_id INTEGER, count INTEGER, PRIMARY KEY (user_id, chat_id))"
            )
            await db.execute(
                "CREATE TABLE IF NOT EXISTS global_bans (user_id INTEGER PRIMARY KEY, reason TEXT)"
            )
            await db.execute(
                "CREATE TABLE IF NOT EXISTS served_chats (chat_id INTEGER PRIMARY KEY)"
            )
            await db.execute(
                "CREATE TABLE IF NOT EXISTS served_users (user_id INTEGER PRIMARY KEY)"
            )
            await db.execute(
                "CREATE TABLE IF NOT EXISTS user_playlists (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT)"
            )
            await db.execute(
                "CREATE TABLE IF NOT EXISTS playlist_tracks (id INTEGER PRIMARY KEY AUTOINCREMENT, playlist_id INTEGER, title TEXT, url TEXT)"
            )
            await db.execute(
                "CREATE TABLE IF NOT EXISTS users_economy (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, kills INTEGER DEFAULT 0)"
            )
            await db.execute(
                "CREATE TABLE IF NOT EXISTS daily_claims (user_id INTEGER PRIMARY KEY, last_claim INTEGER)"
            )
            await db.execute(
                "CREATE TABLE IF NOT EXISTS auth_users (user_id INTEGER, chat_id INTEGER, PRIMARY KEY (user_id, chat_id))"
            )
            await db.execute(
                "CREATE TABLE IF NOT EXISTS blacklisted_chats (chat_id INTEGER PRIMARY KEY)"
            )
            await db.execute(
                "CREATE TABLE IF NOT EXISTS blacklisted_users (user_id INTEGER PRIMARY KEY)"
            )
            await db.commit()

    # Auth Management
    async def add_auth_user(self, user_id: int, chat_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR IGNORE INTO auth_users (user_id, chat_id) VALUES (?, ?)", (user_id, chat_id))
            await db.commit()

    async def remove_auth_user(self, user_id: int, chat_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM auth_users WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            await db.commit()

    async def get_auth_users(self, chat_id: int) -> list[int]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id FROM auth_users WHERE chat_id = ?", (chat_id,)) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    # Blacklist Management
    async def blacklist_chat(self, chat_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR IGNORE INTO blacklisted_chats (chat_id) VALUES (?)", (chat_id,))
            await db.commit()

    async def whitelist_chat(self, chat_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM blacklisted_chats WHERE chat_id = ?", (chat_id,))
            await db.commit()

    async def get_blacklisted_chats(self) -> list[int]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT chat_id FROM blacklisted_chats") as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def blacklist_user(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR IGNORE INTO blacklisted_users (user_id) VALUES (?)", (user_id,))
            await db.commit()

    async def whitelist_user(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM blacklisted_users WHERE user_id = ?", (user_id,))
            await db.commit()

    async def get_blacklisted_users(self) -> list[int]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id FROM blacklisted_users") as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    # Global Ban Management
    async def gban_user(self, user_id: int, reason: str = "No reason"):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR REPLACE INTO global_bans (user_id, reason) VALUES (?, ?)", (user_id, reason))
            await db.commit()

    async def ungban_user(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM global_bans WHERE user_id = ?", (user_id,))
            await db.commit()

    async def get_gbanned_users(self) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id, reason FROM global_bans") as cursor:
                rows = await cursor.fetchall()
                return [{"user_id": row[0], "reason": row[1]} for row in rows]

    # Economy Management
    async def get_balance(self, user_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT balance FROM users_economy WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row: return row[0]
                await db.execute("INSERT OR IGNORE INTO users_economy (user_id, balance) VALUES (?, ?)", (user_id, 0))
                await db.commit()
                return 0

    async def update_balance(self, user_id: int, amount: int):
        current = await self.get_balance(user_id)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR REPLACE INTO users_economy (user_id, balance, kills) VALUES (?, ?, (SELECT kills FROM users_economy WHERE user_id = ?))", (user_id, current + amount, user_id))
            await db.commit()

    async def get_daily_claim(self, user_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT last_claim FROM daily_claims WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def set_daily_claim(self, user_id: int, timestamp: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR REPLACE INTO daily_claims (user_id, last_claim) VALUES (?, ?)", (user_id, timestamp))
            await db.commit()

    async def get_top_rich(self, limit: int = 10) -> list[tuple[int, int]]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id, balance FROM users_economy ORDER BY balance DESC LIMIT ?", (limit,)) as cursor:
                return await cursor.fetchall()

    async def get_top_kills(self, limit: int = 10) -> list[tuple[int, int]]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id, kills FROM users_economy ORDER BY kills DESC LIMIT ?", (limit,)) as cursor:
                return await cursor.fetchall()

    async def add_kill(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users_economy SET kills = kills + 1 WHERE user_id = ?", (user_id,))
            await db.commit()

    # Chat Tracking
    async def add_served_chat(self, chat_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR IGNORE INTO served_chats (chat_id) VALUES (?)", (chat_id,))
            await db.commit()

    async def get_served_chats(self) -> list[int]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT chat_id FROM served_chats") as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def add_served_user(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR IGNORE INTO served_users (user_id) VALUES (?)", (user_id,))
            await db.commit()

    async def get_served_users(self) -> list[int]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id FROM served_users") as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def set_setting(self, key: str, value: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
            await db.commit()

    async def get_setting(self, key: str, default: str = None):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else default

    # Sudo Management
    async def add_sudo(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR IGNORE INTO sudoers (user_id) VALUES (?)", (user_id,))
            await db.commit()

    async def remove_sudo(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM sudoers WHERE user_id = ?", (user_id,))
            await db.commit()

    async def get_sudoers(self) -> list[int]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id FROM sudoers") as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    # Warning Management
    async def get_warns(self, user_id: int, chat_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT count FROM warns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def add_warn(self, user_id: int, chat_id: int):
        count = await self.get_warns(user_id, chat_id) + 1
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR REPLACE INTO warns (user_id, chat_id, count) VALUES (?, ?, ?)", (user_id, chat_id, count))
            await db.commit()
        return count

    async def reset_warns(self, user_id: int, chat_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM warns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            await db.commit()

    # Playlist Management
    async def create_playlist(self, user_id: int, name: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT INTO user_playlists (user_id, name) VALUES (?, ?)", (user_id, name))
            await db.commit()

    async def get_playlists(self, user_id: int) -> list[str]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT name FROM user_playlists WHERE user_id = ?", (user_id,)) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def add_to_playlist(self, user_id: int, name: str, title: str, url: str):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT id FROM user_playlists WHERE user_id = ? AND name = ?", (user_id, name)) as cursor:
                row = await cursor.fetchone()
                if row:
                    playlist_id = row[0]
                    await db.execute("INSERT INTO playlist_tracks (playlist_id, title, url) VALUES (?, ?, ?)", (playlist_id, title, url))
                    await db.commit()

    async def get_playlist_tracks(self, user_id: int, name: str) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT t.title, t.url FROM playlist_tracks t JOIN user_playlists p ON t.playlist_id = p.id WHERE p.user_id = ? AND p.name = ?", 
                (user_id, name)
            ) as cursor:
                rows = await cursor.fetchall()
                return [{"title": row[0], "url": row[1]} for row in rows]

db = Database()
