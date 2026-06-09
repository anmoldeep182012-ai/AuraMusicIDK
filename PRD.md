# Product Requirements Document (PRD) - Music & Group Management Bot

## 1. Executive Summary
This bot is a production-grade, modular, and asynchronous Telegram bot written in Python 3.11. It combines two major functionalities:
1. **Voice Chat Music Streaming**: Streams YouTube audio and video directly into Telegram Group Voice Chats using `PyTgCalls` and `yt-dlp` without local storage download (direct streaming architecture).
2. **Group Management & Moderation**: Admin panels, warnings, moderation commands, and settings management with a centralized role-based permission system.

---

## 2. Goals & Objectives
- **Zero-Download Music Streaming**: High-quality, low-latency audio/video streaming using direct extraction of YouTube streaming URLs.
- **Robust Group Moderation**: Powerful tools for group admins to control spam, enforce rules, and automate punishments (kicking after warning limits).
- **Extensible Architecture**: Fully modular design using Pyrogram's smart handlers, async sqlite database, and clean abstractions.
- **Enterprise-Grade Logging & Security**: Rate-limiting, command cooldowns, robust exception handling, and persistent audit logs.

---

## 3. Technology Stack & Dependencies
- **Programming Language**: Python 3.11
- **Telegram Bot Framework**: Pyrogram (Async client library)
- **Voice Chat Integration**: PyTgCalls (WebRTC Voice Call client)
- **Stream Extractor**: yt-dlp (Command-line / library wrapper for YouTube URL parsing)
- **Database**: SQLite3 (Standard python library, accessed asynchronously via executors)
- **Environment Management**: python-dotenv
- **Cryptography**: tgcrypto (Performance booster for Pyrogram)
- **Media Engine**: FFmpeg (Pre-installed locally on host machine)

---

## 4. Role & Permission System
The bot uses a centralized permission hierarchy:
```
Owner > Sudo User > Admin > User
```
- **Owner**: Complete system control. Can add/remove Sudo users, run broadcasts, view logs, and restart the bot.
- **Sudo User**: High-privilege global bot operator. Can manage sudo command list, access global monitoring.
- **Admin**: Local group administrator. Can trigger moderation commands (ban, kick, mute, warn), change group settings, and control local music.
- **User**: General group member. Can request songs, view queues, check admin list, and view settings.

### Guardrails
All admin, sudo, and owner commands must pass through centralized permission middleware.
- Unauthorized users trying to access administrative commands must receive:
  ```
  ❌ Access Denied
  You must be a group admin to use this command.
  ```

---

## 5. Functional Requirements

### 5.1. User Commands
- `/start`: Starts the bot, replies with a premium styled greeting.
- `/help`: Returns a dynamic help menu detailing all commands according to user role.
- `/play [query/url]`: Search/play audio stream in voice chat.
- `/vplay [query/url]`: Search/play video + audio stream in voice chat.
- `/queue`: Shows the current active music queue.
- `/ping`: Check bot response latency.
- `/admins`: Lists all administrators in the current group chat.
- `/settings`: Displays the group settings panel (admins only).

### 5.2. Music Control
- `/pause`: Pauses the active stream.
- `/resume`: Resumes the paused stream.
- `/stop`: Stops streaming, clears the queue, and leaves the voice chat.
- `/skip`: Skips the current track and starts playing the next track in the queue.
- `/shuffle`: Shuffles the items in the queue.
- `/loop`: Toggles looping the current track or queue.
- `/volume [1-100]`: Adjusts the playback volume of the stream.

### 5.3. Group Moderation
- `/ban [username/reply]`: Permanently bans a user from the group.
- `/unban [username/reply]`: Unbans a previously banned user.
- `/kick [username/reply]`: Kicks a user from the group.
- `/mute [username/reply]`: Prevents a user from sending text messages.
- `/unmute [username/reply]`: Allows a muted user to send text messages again.
- `/warn [username/reply]`: Warns a user. Automatically kicks them upon reaching the configured warn limit (default: 3).
- `/warnings [username/reply]`: Shows the warnings history of a user.
- `/purge [reply]`: Deletes messages between the replied message and the `/purge` command.
- `/pin [reply]`: Pins the replied message.
- `/unpin`: Unpins the pinned message.
- `/promote`: Promotes a user to administrator.
- `/demote`: Demotes an administrator to user.

### 5.4. Owner Commands
- `/addsudo`: Adds a user to the sudo users list.
- `/delsudo`: Removes a user from the sudo list.
- `/sudolist`: Displays all sudo users.
- `/broadcast [message/reply]`: Broadcasts a text message to all groups where the bot is active.
- `/logs`: Sends the current system log file.
- `/restart`: Safely shuts down the clients, flushes queue, and restarts the process.

### 5.5. Group Settings & Customization
- **Welcome Message**: Configurable welcome message for new joins.
- **Logging Channel**: Dedicated channel/chat ID to forward administrative action logs.
- **Auto-Delete Messages**: Clean up bot replies after a configured interval to avoid chat clutter.
- **Warn Limit**: Number of warnings allowed before a kick is triggered.
- **Music Toggle**: Turn on/off music playback command execution.

---

## 6. Non-Functional Requirements
- **No Pseudocode**: The repository must contain fully implemented, valid Python code.
- **No Song Downloads**: Direct streaming through FFmpeg pipes to preserve server space and bandwidth.
- **Rate-Limiting & Cooldowns**: Protect the bot from spamming and command floods.
- **Exception Safety**: The bot must not crash from API rate limits, invalid YouTube links, missing admin permissions, or network disconnects.
