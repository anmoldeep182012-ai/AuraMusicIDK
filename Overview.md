
# Bot Name

┌ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ ─────────────────────────•
│ ʜᴇʏ, ㅤ username (of who started the bot)ㅤㅤ 
│ ɪ ᴀᴍ ⌜ ᴀᴜʀᴀʟʏx x ᴍᴜꜱɪᴄ ⌟
└──────────────────────────────────────•

ᴀ ᴜ ʀ ᴀ ʟ ʏ x
ᴜᴘᴛɪᴍᴇ: 0ʜ:0ᴍ:26
ꜱᴇʀᴠᴇʀ ꜱᴛᴏʀᴀɢᴇ: 62.4%
ᴄᴘᴜ ʟᴏᴀᴅ: 26.2%
ᴇɴᴊᴏʏ ᴘʀᴇᴍɪᴜᴍ ʟɪꜱᴛᴇɴɪɴɢ ᴇxᴘᴇʀɪᴇɴᴄᴇ
╌──────────────────────────────────────•
ᴘᴏᴡᴇʀᴇᴅ » ꜱᴇxᴜᴀᴛɪᴄ | ɢɪɢɢᴀ ɴɪɢɢᴀ
╌──────────────────────────────────────•
@AuralyxXMusic_Bot

 # OverView
 This bot is made for Group Management and Music Streaming on VC(VoiceChat).

  Directory Structure

The codebase is organized into modular directories to keep code decoupled and maintainable:

```
MusicManagerBot/
├── main.py                # Main orchestrator (starts Bot and Userbot clients)
├── config.py              # Application configuration and validation
├── requirements.txt      # Python dependencies
├── .env.example           # Example configuration template
├── PRD.md                 # Product Requirements Document
├── Overview.md            # System Overview (This file)
├── Flow.md                # System flowcharts and process diagrams
├── AGENTS.md              # Multi-agent system description
├── setup.bat              # Setup script for Windows dependencies
├── run.bat                # Windows execution script
├── database/              # SQLite database manager and schemas
│   ├── __init__.py
│   └── db.py              # Async-wrapped database interface
├── modules/               # Pyrogram updates and command handlers
│   ├── __init__.py
│   ├── base.py            # Start, help, ping handlers
│   ├── admin.py           # Moderation commands (ban, kick, mute, warn, etc.)
│   ├── music.py           # Playback commands (play, pause, stop, etc.)
│   └── owner.py           # Owner operations (addsudo, logs, restart, etc.)
├── helpers/               # Helper modules
│   ├── __init__.py
│   ├── filters.py         # Permission and role filters
│   └── decorator.py       # Centralized rate-limiting and error decorators
├── services/              # External services
│   ├── __init__.py
│   ├── yt_service.py      # yt-dlp search and stream extractor
│   └── vc_service.py      # PyTgCalls voice chat manager
├── keyboards/             # Inline/reply keyboards
│   ├── __init__.py
│   └── inline.py          # Admin panel keyboards and shortcuts
├── logs/                  # Text log files (created at runtime)
└── data/                  # Persistent database storage (SQLite)
```

---

## 2. Dual-Client Architecture

Telegram does not support bots streaming media directly in Voice Chats. Therefore, a **Dual-Client Architecture** is required:

```
                  ┌──────────────────────────────┐
                  │  Telegram API (Latest API)   │
                  └───────────┬──────────────────┘
            ┌─────────────────┴─────────────────┐
            ▼                                   ▼
─────────────────────── ────────────────────────────────┐
│                    ⌜ ᴀᴜʀᴀʟʏx x ᴍᴜꜱɪᴄ ⌟               │
│ (Orchestrates Group Management + Streams Music Audio)│
└───────────────────────────┬────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
      [ Hydrogram ]               [ Py-Tgcalls ]
 (Handles Text Commands,       (Handles WebRTC Voice
  Mutes, Kicks, & Userbot)       Chat Audio Streaming)
```

### Shared State & Sync
- Both client loops run under the same `asyncio` event loop in `main.py`.
- Communication is achieved through a shared service manager (`vc_service.py`), allowing the Bot client to command the Userbot client (e.g., skip, play, pause).

  # Command FLow

    ┌──────────────────────────┐
                     │   User Sends a Command   │
                     │  (e.g., /play, /ban, ..) │
                     └────────────┬─────────────┘
                                  │
                                  ▼
                     ┌──────────────────────────┐
                     │   Hydrogram Dispatcher  │
                     │  Filters Type of Account │
                     └────────────┬─────────────┘
                                  │
         ┌────────────────────────┴────────────────────────┐
         │                                                 │
         ▼                                                 ▼
┌────────────────────────────────┐               ┌────────────────────────────────┐
│       Bot Token Instance       │               │     Userbot Client Session     │
│       (@YourMusic_Bot)         │               │     (+12345678... / String)    │
└────────┬───────────────────────┘               └────────┬───────────────────────┘
         │                                                 │
         ├───────────────────────┐                         │
         ▼                       ▼                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌────────────────────────────────┐
│Group Management │     │  Text Response  │     │   Py-Tgcalls Audio Engine      │
│(Admin Tasks)    │     │  & Formatting   │     └────────┬───────────────────────┘
└────────┬────────┘     └────────┬────────┘              │
         │                       │                         │
         │  • /ban, /mute        │  • Monospaced Stats     │  • Spawns FFmpeg loop
         │  • Delete spam        │  • Colored Buttons      │  • Feeds live WebRTC stream
         │  • Manage topics      │  • ||Text Spoilers||    │  • Join/Leave Group VC
         ▼                       ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Telegram Supergroup Voice Chat                         │
│             (Group views text interface while listening to music stream)        │
└─────────────────────────────────────────────────────────────────────────────────┘
Flow BreakdownUser Action: A user interacts with your bot in a Telegram group by typing a text command or pressing an interactive button.Hydrogram Layer: The Python application interceptor catches the incoming update and routes it to the specific account type configured to handle that specific task.Bot Instance Execution:Admin Queries: Standard bot API handles heavy moderation actions like restriction or deleting messages.Formatting Engine: Generates your MarkdownV2/HTML content (monospaced telemetry charts, colored control pads, text masks).Userbot Client Execution:Media Handling: When a user requests music, the userbot processes the source URL.Py-Tgcalls Core: The client logs straight into the group's ongoing voice channel as a participant, running an active FFmpeg process to feed audio packets continuously down the line.
