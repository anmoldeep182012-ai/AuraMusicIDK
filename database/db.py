import aiosqlite
import json
import os
from config import Config

try:
    import asyncpg
except ImportError:
    asyncpg = None

try:
    from motor.motor_asyncio import AsyncIOMotorClient
except ImportError:
    AsyncIOMotorClient = None

class Database:
    def __init__(self):
        # Cloud platforms set DATABASE_URL, fallback to DB_PATH
        self.db_path = os.getenv("MONGO_URI") or Config.MONGO_URI or os.getenv("DATABASE_URL") or Config.DB_PATH
        if not self.db_path:
            self.db_path = "tg_bot.db"
        self.is_mongo = self.db_path.startswith(("mongodb://", "mongodb+srv://"))
        self.is_postgres = not self.is_mongo and self.db_path.startswith(("postgres://", "postgresql://"))
        self.pool = None
        self._served_chats = set()
        self._served_users = set()
        self._sudoers = set()
        self._settings = {}

    async def init(self):
        if self.is_mongo:
            if not AsyncIOMotorClient:
                raise ImportError("MongoDB URL detected but 'motor' is not installed.")
            self.client = AsyncIOMotorClient(self.db_path)
            self.db = self.client["music_bot_db"]
            # Collections
            self.c_settings = self.db["settings"]
            self.c_sudoers = self.db["sudoers"]
            self.c_warns = self.db["warns"]
            self.c_global_bans = self.db["global_bans"]
            self.c_served_chats = self.db["served_chats"]
            self.c_served_users = self.db["served_users"]
            self.c_playlists = self.db["user_playlists"]
            self.c_economy = self.db["users_economy"]
            self.c_daily_claims = self.db["daily_claims"]
            self.c_auth_users = self.db["auth_users"]
            self.c_blacklisted_chats = self.db["blacklisted_chats"]
            self.c_blacklisted_users = self.db["blacklisted_users"]
            self.c_coupons = self.db["coupons"]
            self.c_group_claims = self.db["group_claims"]
            self.c_stream_cache = self.db["stream_cache"]
            self.c_chats = self.db["chats"]

            # Create TTL Index (2 hours)
            await self.c_stream_cache.create_index("created_at", expireAfterSeconds=7200)
        elif self.is_postgres:
            if not asyncpg:
                raise ImportError("PostgreSQL database URL detected but 'asyncpg' is not installed.")
            db_url = self.db_path
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            # Create connection pool
            self.pool = await asyncpg.create_pool(db_url)
            async with self.pool.acquire() as conn:
                await conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
                await conn.execute("CREATE TABLE IF NOT EXISTS sudoers (user_id BIGINT PRIMARY KEY)")
                await conn.execute("CREATE TABLE IF NOT EXISTS warns (user_id BIGINT, chat_id BIGINT, count INTEGER, PRIMARY KEY (user_id, chat_id))")
                await conn.execute("CREATE TABLE IF NOT EXISTS global_bans (user_id BIGINT PRIMARY KEY, reason TEXT)")
                await conn.execute("CREATE TABLE IF NOT EXISTS served_chats (chat_id BIGINT PRIMARY KEY)")
                await conn.execute("CREATE TABLE IF NOT EXISTS served_users (user_id BIGINT PRIMARY KEY)")
                await conn.execute("CREATE TABLE IF NOT EXISTS user_playlists (id SERIAL PRIMARY KEY, user_id BIGINT, name TEXT)")
                await conn.execute("CREATE TABLE IF NOT EXISTS playlist_tracks (id SERIAL PRIMARY KEY, playlist_id INTEGER, title TEXT, url TEXT)")
                await conn.execute("CREATE TABLE IF NOT EXISTS users_economy (user_id BIGINT PRIMARY KEY, balance BIGINT DEFAULT 0, kills INTEGER DEFAULT 0, xp INTEGER DEFAULT 0, protection_until BIGINT DEFAULT 0)")
                await conn.execute("CREATE TABLE IF NOT EXISTS daily_claims (user_id BIGINT PRIMARY KEY, last_claim BIGINT)")
                await conn.execute("CREATE TABLE IF NOT EXISTS auth_users (user_id BIGINT, chat_id BIGINT, PRIMARY KEY (user_id, chat_id))")
                await conn.execute("CREATE TABLE IF NOT EXISTS blacklisted_chats (chat_id BIGINT PRIMARY KEY)")
                await conn.execute("CREATE TABLE IF NOT EXISTS blacklisted_users (user_id BIGINT PRIMARY KEY)")
                await conn.execute("CREATE TABLE IF NOT EXISTS coupons (code TEXT PRIMARY KEY, coins BIGINT, creator_id BIGINT, claimed_by BIGINT DEFAULT NULL, claimed_at BIGINT DEFAULT NULL, created_at BIGINT DEFAULT 0)")
                await conn.execute("CREATE TABLE IF NOT EXISTS group_claims (chat_id BIGINT PRIMARY KEY, inviter_id BIGINT, claimed INTEGER DEFAULT 0)")
                await conn.execute("CREATE TABLE IF NOT EXISTS chats_queue (chat_id BIGINT PRIMARY KEY, queue TEXT)")
                await conn.execute("CREATE TABLE IF NOT EXISTS stream_cache (query TEXT, is_video BOOLEAN, url TEXT, audio_url TEXT, title TEXT, duration TEXT, duration_sec INTEGER, thumbnail TEXT, yt_url TEXT, created_at BIGINT, PRIMARY KEY (query, is_video))")
        else:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
                await db.execute("CREATE TABLE IF NOT EXISTS sudoers (user_id INTEGER PRIMARY KEY)")
                await db.execute("CREATE TABLE IF NOT EXISTS warns (user_id INTEGER, chat_id INTEGER, count INTEGER, PRIMARY KEY (user_id, chat_id))")
                await db.execute("CREATE TABLE IF NOT EXISTS global_bans (user_id INTEGER PRIMARY KEY, reason TEXT)")
                await db.execute("CREATE TABLE IF NOT EXISTS served_chats (chat_id INTEGER PRIMARY KEY)")
                await db.execute("CREATE TABLE IF NOT EXISTS served_users (user_id INTEGER PRIMARY KEY)")
                await db.execute("CREATE TABLE IF NOT EXISTS user_playlists (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT)")
                await db.execute("CREATE TABLE IF NOT EXISTS playlist_tracks (id INTEGER PRIMARY KEY AUTOINCREMENT, playlist_id INTEGER, title TEXT, url TEXT)")
                await db.execute("CREATE TABLE IF NOT EXISTS users_economy (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, kills INTEGER DEFAULT 0, xp INTEGER DEFAULT 0, protection_until INTEGER DEFAULT 0)")
                await db.execute("CREATE TABLE IF NOT EXISTS daily_claims (user_id INTEGER PRIMARY KEY, last_claim INTEGER)")
                await db.execute("CREATE TABLE IF NOT EXISTS auth_users (user_id INTEGER, chat_id INTEGER, PRIMARY KEY (user_id, chat_id))")
                await db.execute("CREATE TABLE IF NOT EXISTS blacklisted_chats (chat_id INTEGER PRIMARY KEY)")
                await db.execute("CREATE TABLE IF NOT EXISTS blacklisted_users (user_id INTEGER PRIMARY KEY)")
                await db.execute("CREATE TABLE IF NOT EXISTS coupons (code TEXT PRIMARY KEY, coins INTEGER, creator_id INTEGER, claimed_by INTEGER DEFAULT NULL, claimed_at INTEGER DEFAULT NULL, created_at INTEGER DEFAULT 0)")
                await db.execute("CREATE TABLE IF NOT EXISTS group_claims (chat_id INTEGER PRIMARY KEY, inviter_id INTEGER, claimed INTEGER DEFAULT 0)")
                await db.execute("CREATE TABLE IF NOT EXISTS chats_queue (chat_id INTEGER PRIMARY KEY, queue TEXT)")
                await db.execute("CREATE TABLE IF NOT EXISTS stream_cache (query TEXT, is_video INTEGER, url TEXT, audio_url TEXT, title TEXT, duration TEXT, duration_sec INTEGER, thumbnail TEXT, yt_url TEXT, created_at INTEGER, PRIMARY KEY (query, is_video))")
                await db.commit()

        # Load caches
        if self.is_mongo:
            chats = await self.c_served_chats.find({}).to_list(length=None)
            self._served_chats = set(doc["_id"] for doc in chats)
            
            users = await self.c_served_users.find({}).to_list(length=None)
            self._served_users = set(doc["_id"] for doc in users)
            
            sudos = await self.c_sudoers.find({}).to_list(length=None)
            self._sudoers = set(doc["_id"] for doc in sudos)
            
            settings = await self.c_settings.find({}).to_list(length=None)
            self._settings = {doc["_id"]: doc["value"] for doc in settings}
        else:
            chats = await self._fetch("SELECT chat_id FROM served_chats")
            self._served_chats = set(row[0] for row in chats)
            
            users = await self._fetch("SELECT user_id FROM served_users")
            self._served_users = set(row[0] for row in users)
            
            sudos = await self._fetch("SELECT user_id FROM sudoers")
            self._sudoers = set(row[0] for row in sudos)
            
            settings = await self._fetch("SELECT key, value FROM settings")
            self._settings = {row[0]: row[1] for row in settings}

        # Migration to add created_at if not present
        if not self.is_mongo:
            try:
                if self.is_postgres:
                    async with self.pool.acquire() as conn:
                        await conn.execute("ALTER TABLE coupons ADD COLUMN IF NOT EXISTS created_at BIGINT DEFAULT 0")
                else:
                    async with aiosqlite.connect(self.db_path) as db_conn:
                        await db_conn.execute("ALTER TABLE coupons ADD COLUMN created_at INTEGER DEFAULT 0")
                        await db_conn.commit()
            except Exception:
                pass

    def _translate_sql(self, sql: str) -> str:
        if not self.is_postgres:
            return sql
        
        # Convert placeholders ? to $1, $2, ...
        placeholder_count = 0
        while "?" in sql:
            placeholder_count += 1
            sql = sql.replace("?", f"${placeholder_count}", 1)
            
        # Replace INSERT OR IGNORE
        if "INSERT OR IGNORE INTO" in sql:
            sql = sql.replace("INSERT OR IGNORE INTO", "INSERT INTO") + " ON CONFLICT DO NOTHING"
            
        # Replace INSERT OR REPLACE
        if "INSERT OR REPLACE INTO" in sql:
            if "global_bans" in sql:
                sql = sql.replace("INSERT OR REPLACE INTO global_bans", "INSERT INTO global_bans") + " ON CONFLICT (user_id) DO UPDATE SET reason = EXCLUDED.reason"
            elif "daily_claims" in sql:
                sql = sql.replace("INSERT OR REPLACE INTO daily_claims", "INSERT INTO daily_claims") + " ON CONFLICT (user_id) DO UPDATE SET last_claim = EXCLUDED.last_claim"
            elif "settings" in sql:
                sql = sql.replace("INSERT OR REPLACE INTO settings", "INSERT INTO settings") + " ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
            elif "warns" in sql:
                sql = sql.replace("INSERT OR REPLACE INTO warns", "INSERT INTO warns") + " ON CONFLICT (user_id, chat_id) DO UPDATE SET count = EXCLUDED.count"
                
        return sql

    async def _execute(self, sql: str, *args):
        sql = self._translate_sql(sql)
        if self.is_postgres:
            async with self.pool.acquire() as conn:
                await conn.execute(sql, *args)
        else:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(sql, args)
                await db.commit()

    async def _fetch(self, sql: str, *args) -> list:
        sql = self._translate_sql(sql)
        if self.is_postgres:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(sql, *args)
                return [list(r.values()) for r in rows]
        else:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(sql, args) as cursor:
                    return await cursor.fetchall()

    async def _fetchrow(self, sql: str, *args):
        sql = self._translate_sql(sql)
        if self.is_postgres:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(sql, *args)
                return list(row.values()) if row else None
        else:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(sql, args) as cursor:
                    return await cursor.fetchone()

    # Auth Management
    async def add_auth_user(self, user_id: int, chat_id: int):
        if self.is_mongo:
            await self.c_auth_users.update_one(
                {"_id": f"{user_id}_{chat_id}"},
                {"$set": {"user_id": user_id, "chat_id": chat_id}},
                upsert=True
            )
        else:
            await self._execute("INSERT OR IGNORE INTO auth_users (user_id, chat_id) VALUES (?, ?)", user_id, chat_id)

    async def remove_auth_user(self, user_id: int, chat_id: int):
        if self.is_mongo:
            await self.c_auth_users.delete_one({"_id": f"{user_id}_{chat_id}"})
        else:
            await self._execute("DELETE FROM auth_users WHERE user_id = ? AND chat_id = ?", user_id, chat_id)

    async def get_auth_users(self, chat_id: int) -> list[int]:
        if self.is_mongo:
            cursor = self.c_auth_users.find({"chat_id": chat_id})
            rows = await cursor.to_list(length=None)
            return [r["user_id"] for r in rows]
        else:
            rows = await self._fetch("SELECT user_id FROM auth_users WHERE chat_id = ?", chat_id)
            return [row[0] for row in rows]

    # Blacklist Management
    async def blacklist_chat(self, chat_id: int):
        if self.is_mongo:
            await self.c_blacklisted_chats.update_one({"_id": chat_id}, {"$set": {}}, upsert=True)
        else:
            await self._execute("INSERT OR IGNORE INTO blacklisted_chats (chat_id) VALUES (?)", chat_id)

    async def whitelist_chat(self, chat_id: int):
        if self.is_mongo:
            await self.c_blacklisted_chats.delete_one({"_id": chat_id})
        else:
            await self._execute("DELETE FROM blacklisted_chats WHERE chat_id = ?", chat_id)

    async def get_blacklisted_chats(self) -> list[int]:
        if self.is_mongo:
            rows = await self.c_blacklisted_chats.find({}).to_list(length=None)
            return [r["_id"] for r in rows]
        else:
            rows = await self._fetch("SELECT chat_id FROM blacklisted_chats")
            return [row[0] for row in rows]

    async def blacklist_user(self, user_id: int):
        if self.is_mongo:
            await self.c_blacklisted_users.update_one({"_id": user_id}, {"$set": {}}, upsert=True)
        else:
            await self._execute("INSERT OR IGNORE INTO blacklisted_users (user_id) VALUES (?)", user_id)

    async def whitelist_user(self, user_id: int):
        if self.is_mongo:
            await self.c_blacklisted_users.delete_one({"_id": user_id})
        else:
            await self._execute("DELETE FROM blacklisted_users WHERE user_id = ?", user_id)

    async def get_blacklisted_users(self) -> list[int]:
        if self.is_mongo:
            rows = await self.c_blacklisted_users.find({}).to_list(length=None)
            return [r["_id"] for r in rows]
        else:
            rows = await self._fetch("SELECT user_id FROM blacklisted_users")
            return [row[0] for row in rows]

    # Global Ban Management
    async def gban_user(self, user_id: int, reason: str = "No reason"):
        if self.is_mongo:
            await self.c_global_bans.update_one(
                {"_id": user_id},
                {"$set": {"reason": reason}},
                upsert=True
            )
        else:
            await self._execute("INSERT OR REPLACE INTO global_bans (user_id, reason) VALUES (?, ?)", user_id, reason)

    async def ungban_user(self, user_id: int):
        if self.is_mongo:
            await self.c_global_bans.delete_one({"_id": user_id})
        else:
            await self._execute("DELETE FROM global_bans WHERE user_id = ?", user_id)

    async def get_gbanned_users(self) -> list[dict]:
        if self.is_mongo:
            rows = await self.c_global_bans.find({}).to_list(length=None)
            return [{"user_id": r["_id"], "reason": r["reason"]} for r in rows]
        else:
            rows = await self._fetch("SELECT user_id, reason FROM global_bans")
            return [{"user_id": row[0], "reason": row[1]} for row in rows]

    # Economy Management
    async def get_balance(self, user_id: int) -> int:
        if self.is_mongo:
            doc = await self.c_economy.find_one({"_id": user_id})
            if doc:
                return doc.get("balance", 0)
            await self.c_economy.update_one(
                {"_id": user_id},
                {"$set": {"balance": 0, "kills": 0, "xp": 0, "protection_until": 0}},
                upsert=True
            )
            return 0
        else:
            row = await self._fetchrow("SELECT balance FROM users_economy WHERE user_id = ?", user_id)
            if row: return row[0]
            await self._execute("INSERT OR IGNORE INTO users_economy (user_id, balance) VALUES (?, 0)", user_id)
            return 0

    async def update_balance(self, user_id: int, amount: int):
        if self.is_mongo:
            await self.get_balance(user_id) # ensure row exists
            await self.c_economy.update_one(
                {"_id": user_id},
                {"$inc": {"balance": amount}}
            )
        else:
            await self.get_balance(user_id) # ensure row exists
            await self._execute("UPDATE users_economy SET balance = COALESCE(balance, 0) + ? WHERE user_id = ?", amount, user_id)

    async def get_daily_claim(self, user_id: int) -> int:
        if self.is_mongo:
            doc = await self.c_daily_claims.find_one({"_id": user_id})
            return doc.get("last_claim", 0) if doc else 0
        else:
            row = await self._fetchrow("SELECT last_claim FROM daily_claims WHERE user_id = ?", user_id)
            return row[0] if row else 0

    async def set_daily_claim(self, user_id: int, timestamp: int):
        if self.is_mongo:
            await self.c_daily_claims.update_one(
                {"_id": user_id},
                {"$set": {"last_claim": timestamp}},
                upsert=True
            )
        else:
            await self._execute("INSERT OR REPLACE INTO daily_claims (user_id, last_claim) VALUES (?, ?)", user_id, timestamp)

    async def get_top_rich(self, limit: int = 10) -> list[tuple[int, int]]:
        if self.is_mongo:
            cursor = self.c_economy.find({}).sort("balance", -1).limit(limit)
            rows = await cursor.to_list(length=None)
            return [(r["_id"], r.get("balance", 0)) for r in rows]
        else:
            rows = await self._fetch("SELECT user_id, balance FROM users_economy ORDER BY balance DESC LIMIT ?", limit)
            return [tuple(row) for row in rows]

    async def get_top_kills(self, limit: int = 10) -> list[tuple[int, int]]:
        if self.is_mongo:
            cursor = self.c_economy.find({}).sort("kills", -1).limit(limit)
            rows = await cursor.to_list(length=None)
            return [(r["_id"], r.get("kills", 0)) for r in rows]
        else:
            rows = await self._fetch("SELECT user_id, kills FROM users_economy ORDER BY kills DESC LIMIT ?", limit)
            return [tuple(row) for row in rows]

    async def add_kill(self, user_id: int):
        if self.is_mongo:
            await self.get_balance(user_id) # ensure row exists
            await self.c_economy.update_one(
                {"_id": user_id},
                {"$inc": {"kills": 1}}
            )
        else:
            await self.get_balance(user_id) # ensure row exists
            await self._execute("UPDATE users_economy SET kills = COALESCE(kills, 0) + 1 WHERE user_id = ?", user_id)

    # Chat Tracking
    async def add_served_chat(self, chat_id: int):
        if chat_id in self._served_chats:
            return
        self._served_chats.add(chat_id)
        if self.is_mongo:
            await self.c_served_chats.update_one({"_id": chat_id}, {"$set": {}}, upsert=True)
        else:
            await self._execute("INSERT OR IGNORE INTO served_chats (chat_id) VALUES (?)", chat_id)

    async def get_served_chats(self) -> list[int]:
        return list(self._served_chats)

    async def add_served_user(self, user_id: int):
        if user_id in self._served_users:
            return
        self._served_users.add(user_id)
        if self.is_mongo:
            await self.c_served_users.update_one({"_id": user_id}, {"$set": {}}, upsert=True)
        else:
            await self._execute("INSERT OR IGNORE INTO served_users (user_id) VALUES (?)", user_id)

    async def get_served_users(self) -> list[int]:
        return list(self._served_users)

    async def set_setting(self, key: str, value: str):
        self._settings[key] = value
        if self.is_mongo:
            await self.c_settings.update_one({"_id": key}, {"$set": {"value": value}}, upsert=True)
        else:
            await self._execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", key, value)

    async def get_setting(self, key: str, default: str = None):
        return self._settings.get(key, default)

    # Sudo Management
    async def add_sudo(self, user_id: int):
        self._sudoers.add(user_id)
        if self.is_mongo:
            await self.c_sudoers.update_one({"_id": user_id}, {"$set": {}}, upsert=True)
        else:
            await self._execute("INSERT OR IGNORE INTO sudoers (user_id) VALUES (?)", user_id)

    async def remove_sudo(self, user_id: int):
        if user_id in self._sudoers:
            self._sudoers.remove(user_id)
        if self.is_mongo:
            await self.c_sudoers.delete_one({"_id": user_id})
        else:
            await self._execute("DELETE FROM sudoers WHERE user_id = ?", user_id)

    async def get_sudoers(self) -> list[int]:
        return list(self._sudoers)

    # Warning Management
    async def get_warns(self, user_id: int, chat_id: int) -> int:
        if self.is_mongo:
            doc = await self.c_warns.find_one({"_id": f"{user_id}_{chat_id}"})
            return doc.get("count", 0) if doc else 0
        else:
            row = await self._fetchrow("SELECT count FROM warns WHERE user_id = ? AND chat_id = ?", user_id, chat_id)
            return row[0] if row else 0

    async def add_warn(self, user_id: int, chat_id: int):
        count = await self.get_warns(user_id, chat_id) + 1
        if self.is_mongo:
            await self.c_warns.update_one(
                {"_id": f"{user_id}_{chat_id}"},
                {"$set": {"user_id": user_id, "chat_id": chat_id, "count": count}},
                upsert=True
            )
        else:
            await self._execute("INSERT OR REPLACE INTO warns (user_id, chat_id, count) VALUES (?, ?, ?)", user_id, chat_id, count)
        return count

    async def reset_warns(self, user_id: int, chat_id: int):
        if self.is_mongo:
            await self.c_warns.delete_one({"_id": f"{user_id}_{chat_id}"})
        else:
            await self._execute("DELETE FROM warns WHERE user_id = ? AND chat_id = ?", user_id, chat_id)

    # Playlist Management
    async def create_playlist(self, user_id: int, name: str):
        if self.is_mongo:
            await self.c_playlists.update_one(
                {"_id": f"{user_id}_{name}"},
                {"$set": {"user_id": user_id, "name": name, "tracks": []}},
                upsert=True
            )
        else:
            await self._execute("INSERT INTO user_playlists (user_id, name) VALUES (?, ?)", user_id, name)

    async def get_playlists(self, user_id: int) -> list[str]:
        if self.is_mongo:
            rows = await self.c_playlists.find({"user_id": user_id}).to_list(length=None)
            return [r["name"] for r in rows]
        else:
            rows = await self._fetch("SELECT name FROM user_playlists WHERE user_id = ?", user_id)
            return [row[0] for row in rows]

    async def add_to_playlist(self, user_id: int, name: str, title: str, url: str):
        if self.is_mongo:
            await self.c_playlists.update_one(
                {"_id": f"{user_id}_{name}"},
                {"$push": {"tracks": {"title": title, "url": url}}},
                upsert=True
            )
        else:
            row = await self._fetchrow("SELECT id FROM user_playlists WHERE user_id = ? AND name = ?", user_id, name)
            if row:
                playlist_id = row[0]
                await self._execute("INSERT INTO playlist_tracks (playlist_id, title, url) VALUES (?, ?, ?)", playlist_id, title, url)

    async def get_playlist_tracks(self, user_id: int, name: str) -> list[dict]:
        if self.is_mongo:
            doc = await self.c_playlists.find_one({"_id": f"{user_id}_{name}"})
            return doc.get("tracks", []) if doc else []
        else:
            rows = await self._fetch(
                "SELECT t.title, t.url FROM playlist_tracks t JOIN user_playlists p ON t.playlist_id = p.id WHERE p.user_id = ? AND p.name = ?", 
                user_id, name
            )
            return [{"title": row[0], "url": row[1]} for row in rows]

    async def get_xp(self, user_id: int) -> int:
        if self.is_mongo:
            doc = await self.c_economy.find_one({"_id": user_id})
            if doc:
                return doc.get("xp", 0)
            await self.c_economy.update_one(
                {"_id": user_id},
                {"$set": {"balance": 0, "kills": 0, "xp": 0, "protection_until": 0}},
                upsert=True
            )
            return 0
        else:
            row = await self._fetchrow("SELECT xp FROM users_economy WHERE user_id = ?", user_id)
            if row: return row[0] if row[0] is not None else 0
            await self._execute("INSERT OR IGNORE INTO users_economy (user_id, balance, xp) VALUES (?, 0, 0)", user_id)
            return 0

    async def update_xp(self, user_id: int, amount: int):
        if self.is_mongo:
            await self.get_xp(user_id) # ensure row exists
            await self.c_economy.update_one(
                {"_id": user_id},
                {"$inc": {"xp": amount}}
            )
        else:
            await self.get_xp(user_id) # ensure row exists
            await self._execute("UPDATE users_economy SET xp = COALESCE(xp, 0) + ? WHERE user_id = ?", amount, user_id)

    async def get_protection(self, user_id: int) -> int:
        if self.is_mongo:
            doc = await self.c_economy.find_one({"_id": user_id})
            if doc:
                return doc.get("protection_until", 0)
            await self.c_economy.update_one(
                {"_id": user_id},
                {"$set": {"balance": 0, "kills": 0, "xp": 0, "protection_until": 0}},
                upsert=True
            )
            return 0
        else:
            row = await self._fetchrow("SELECT protection_until FROM users_economy WHERE user_id = ?", user_id)
            if row: return row[0] if row[0] is not None else 0
            await self._execute("INSERT OR IGNORE INTO users_economy (user_id, balance, protection_until) VALUES (?, 0, 0)", user_id)
            return 0

    async def set_protection(self, user_id: int, protection_until: int):
        if self.is_mongo:
            await self.get_protection(user_id) # ensure row exists
            await self.c_economy.update_one(
                {"_id": user_id},
                {"$set": {"protection_until": protection_until}}
            )
        else:
            await self.get_protection(user_id) # ensure row exists
            await self._execute("UPDATE users_economy SET protection_until = ? WHERE user_id = ?", protection_until, user_id)

    async def is_premium(self, user_id: int) -> bool:
        if user_id == Config.OWNER_ID or user_id in self._sudoers:
            return True
        val = await self.get_setting(f"premium_{user_id}")
        return val == "true"

    async def set_premium(self, user_id: int, is_premium: bool = True):
        val = "true" if is_premium else "false"
        await self.set_setting(f"premium_{user_id}", val)

    async def set_balance(self, user_id: int, amount: int):
        if self.is_mongo:
            await self.get_balance(user_id) # ensure row exists
            await self.c_economy.update_one(
                {"_id": user_id},
                {"$set": {"balance": amount}}
            )
        else:
            await self.get_balance(user_id) # ensure row exists
            await self._execute("UPDATE users_economy SET balance = ? WHERE user_id = ?", amount, user_id)

    async def set_xp(self, user_id: int, amount: int):
        if self.is_mongo:
            await self.get_xp(user_id) # ensure row exists
            await self.c_economy.update_one(
                {"_id": user_id},
                {"$set": {"xp": amount}}
            )
        else:
            await self.get_xp(user_id) # ensure row exists
            await self._execute("UPDATE users_economy SET xp = ? WHERE user_id = ?", amount, user_id)

    async def set_kills(self, user_id: int, amount: int):
        if self.is_mongo:
            await self.get_balance(user_id) # ensure row exists
            await self.c_economy.update_one(
                {"_id": user_id},
                {"$set": {"kills": amount}}
            )
        else:
            await self.get_balance(user_id) # ensure row exists
            await self._execute("UPDATE users_economy SET kills = ? WHERE user_id = ?", amount, user_id)

    async def create_coupon(self, code: str, coins: int, creator_id: int, timestamp: int):
        if self.is_mongo:
            await self.c_coupons.update_one(
                {"_id": code},
                {"$set": {
                    "coins": coins,
                    "creator_id": creator_id,
                    "claimed_by": None,
                    "claimed_at": None,
                    "created_at": timestamp
                }},
                upsert=True
            )
        else:
            await self._execute("INSERT INTO coupons (code, coins, creator_id, created_at) VALUES (?, ?, ?, ?)", code, coins, creator_id, timestamp)

    async def get_coupon(self, code: str) -> dict:
        if self.is_mongo:
            doc = await self.c_coupons.find_one({"_id": code})
            if doc:
                return {
                    "code": doc["_id"],
                    "coins": doc["coins"],
                    "creator_id": doc["creator_id"],
                    "claimed_by": doc.get("claimed_by"),
                    "created_at": doc.get("created_at", 0)
                }
            return None
        else:
            row = await self._fetchrow("SELECT code, coins, creator_id, claimed_by, created_at FROM coupons WHERE code = ?", code)
            if row:
                return {"code": row[0], "coins": row[1], "creator_id": row[2], "claimed_by": row[3], "created_at": row[4]}
            return None

    async def claim_coupon(self, code: str, user_id: int, timestamp: int):
        if self.is_mongo:
            await self.c_coupons.update_one(
                {"_id": code},
                {"$set": {"claimed_by": user_id, "claimed_at": timestamp}}
            )
        else:
            await self._execute("UPDATE coupons SET claimed_by = ?, claimed_at = ? WHERE code = ?", user_id, timestamp, code)

    async def save_group_inviter(self, chat_id: int, inviter_id: int):
        if self.is_mongo:
            await self.c_group_claims.update_one(
                {"_id": chat_id},
                {"$setOnInsert": {"inviter_id": inviter_id, "claimed": 0}},
                upsert=True
            )
        else:
            if self.is_postgres:
                await self._execute("INSERT INTO group_claims (chat_id, inviter_id, claimed) VALUES (?, ?, 0) ON CONFLICT (chat_id) DO NOTHING", chat_id, inviter_id)
            else:
                await self._execute("INSERT OR IGNORE INTO group_claims (chat_id, inviter_id, claimed) VALUES (?, ?, 0)", chat_id, inviter_id)

    async def get_group_claim(self, chat_id: int) -> dict:
        if self.is_mongo:
            doc = await self.c_group_claims.find_one({"_id": chat_id})
            if doc:
                return {"inviter_id": doc["inviter_id"], "claimed": doc["claimed"]}
            return None
        else:
            row = await self._fetchrow("SELECT inviter_id, claimed FROM group_claims WHERE chat_id = ?", chat_id)
            if row:
                return {"inviter_id": row[0], "claimed": row[1]}
            return None

    async def mark_group_claimed(self, chat_id: int):
        if self.is_mongo:
            await self.c_group_claims.update_one(
                {"_id": chat_id},
                {"$set": {"claimed": 1}}
            )
        else:
            await self._execute("UPDATE group_claims SET claimed = 1 WHERE chat_id = ?", chat_id)

    # Persistent Queue operations
    async def get_queue(self, chat_id: int) -> list:
        if self.is_mongo:
            doc = await self.c_chats.find_one({"_id": chat_id})
            return doc.get("queue", []) if doc else []
        else:
            row = await self._fetchrow("SELECT queue FROM chats_queue WHERE chat_id = ?", chat_id)
            return json.loads(row[0]) if (row and row[0]) else []

    async def set_queue(self, chat_id: int, queue: list):
        if self.is_mongo:
            await self.c_chats.update_one({"_id": chat_id}, {"$set": {"queue": queue}}, upsert=True)
        else:
            queue_json = json.dumps(queue)
            if self.is_postgres:
                await self._execute(
                    "INSERT INTO chats_queue (chat_id, queue) VALUES (?, ?) ON CONFLICT (chat_id) DO UPDATE SET queue = EXCLUDED.queue",
                    chat_id, queue_json
                )
            else:
                await self._execute(
                    "INSERT OR REPLACE INTO chats_queue (chat_id, queue) VALUES (?, ?)",
                    chat_id, queue_json
                )

    async def add_to_queue(self, chat_id: int, track: dict):
        if self.is_mongo:
            await self.c_chats.update_one({"_id": chat_id}, {"$push": {"queue": track}}, upsert=True)
        else:
            queue = await self.get_queue(chat_id)
            queue.append(track)
            await self.set_queue(chat_id, queue)

    async def add_multiple_to_queue(self, chat_id: int, tracks: list):
        if self.is_mongo:
            await self.c_chats.update_one({"_id": chat_id}, {"$push": {"queue": {"$each": tracks}}}, upsert=True)
        else:
            queue = await self.get_queue(chat_id)
            queue.extend(tracks)
            await self.set_queue(chat_id, queue)

    async def remove_first_track(self, chat_id: int):
        if self.is_mongo:
            await self.c_chats.update_one({"_id": chat_id}, {"$pop": {"queue": -1}})
        else:
            queue = await self.get_queue(chat_id)
            if queue:
                queue.pop(0)
                await self.set_queue(chat_id, queue)

    async def clear_queue(self, chat_id: int):
        if self.is_mongo:
            await self.c_chats.update_one({"_id": chat_id}, {"$set": {"queue": []}}, upsert=True)
        else:
            await self.set_queue(chat_id, [])

    async def load_all_queues(self) -> dict:
        queues = {}
        if self.is_mongo:
            cursor = self.c_chats.find({"queue": {"$exists": True, "$ne": []}})
            rows = await cursor.to_list(length=None)
            for r in rows:
                queues[r["_id"]] = r["queue"]
        else:
            rows = await self._fetch("SELECT chat_id, queue FROM chats_queue")
            for r in rows:
                if r[1]:
                    try:
                        q = json.loads(r[1])
                        if q:
                            queues[r[0]] = q
                    except Exception:
                        pass
        return queues

    # Stream caching helpers
    async def get_cached_stream(self, query: str, is_video: bool) -> dict:
        if self.is_mongo:
            cache_id = f"{query}_{is_video}"
            doc = await self.c_stream_cache.find_one({"_id": cache_id})
            if doc:
                return {
                    "url": doc["url"],
                    "audio_url": doc.get("audio_url"),
                    "title": doc["title"],
                    "duration": doc["duration"],
                    "duration_sec": doc.get("duration_sec", 0),
                    "thumbnail": doc.get("thumbnail"),
                    "is_video": doc["is_video"],
                    "yt_url": doc.get("yt_url")
                }
        else:
            import time
            now = int(time.time())
            row = await self._fetchrow(
                "SELECT url, audio_url, title, duration, duration_sec, thumbnail, yt_url, created_at FROM stream_cache WHERE query = ? AND is_video = ?", 
                query, 1 if is_video else 0
            )
            if row:
                created_at = row[7]
                if now - created_at < 7200:
                    return {
                        "url": row[0],
                        "audio_url": row[1],
                        "title": row[2],
                        "duration": row[3],
                        "duration_sec": row[4],
                        "thumbnail": row[5],
                        "is_video": is_video,
                        "yt_url": row[6]
                    }
                else:
                    await self._execute("DELETE FROM stream_cache WHERE query = ? AND is_video = ?", query, 1 if is_video else 0)
        return None

    async def set_cached_stream(self, query: str, track_info: dict):
        if self.is_mongo:
            from datetime import datetime
            cache_id = f"{query}_{track_info['is_video']}"
            doc = {
                "_id": cache_id,
                "query": query,
                "url": track_info["url"],
                "audio_url": track_info.get("audio_url"),
                "title": track_info["title"],
                "duration": track_info["duration"],
                "duration_sec": track_info.get("duration_sec", 0),
                "thumbnail": track_info.get("thumbnail"),
                "is_video": track_info["is_video"],
                "yt_url": track_info.get("yt_url"),
                "created_at": datetime.utcnow()
            }
            await self.c_stream_cache.replace_one({"_id": cache_id}, doc, upsert=True)
        else:
            import time
            now = int(time.time())
            is_video_val = 1 if track_info["is_video"] else 0
            if self.is_postgres:
                await self._execute(
                    "INSERT INTO stream_cache (query, is_video, url, audio_url, title, duration, duration_sec, thumbnail, yt_url, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT (query, is_video) DO UPDATE SET url = EXCLUDED.url, audio_url = EXCLUDED.audio_url, title = EXCLUDED.title, duration = EXCLUDED.duration, duration_sec = EXCLUDED.duration_sec, thumbnail = EXCLUDED.thumbnail, yt_url = EXCLUDED.yt_url, created_at = EXCLUDED.created_at",
                    query, is_video_val, track_info["url"], track_info.get("audio_url"), track_info["title"], track_info["duration"], track_info.get("duration_sec", 0), track_info.get("thumbnail"), track_info.get("yt_url"), now
                )
            else:
                await self._execute(
                    "INSERT OR REPLACE INTO stream_cache (query, is_video, url, audio_url, title, duration, duration_sec, thumbnail, yt_url, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    query, is_video_val, track_info["url"], track_info.get("audio_url"), track_info["title"], track_info["duration"], track_info.get("duration_sec", 0), track_info.get("thumbnail"), track_info.get("yt_url"), now
                )

db = Database()



