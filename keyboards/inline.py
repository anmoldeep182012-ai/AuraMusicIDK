# Inline keyboards for specialized panels
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import enums
from helpers.styling import small_caps, fraktur


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Sudo Panel Keyboards
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def sudo_main_panel():
    """Main sudo control panel keyboard with exclusive features."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(small_caps("ꜱʏꜱᴛᴇᴍ ꜱᴛᴀᴛꜱ"), callback_data="sudo_stats", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton(small_caps("ᴀᴄᴛɪᴠᴇ ꜱᴛʀᴇᴀᴍꜱ"), callback_data="sudo_streams", style=enums.ButtonStyle.PRIMARY)
        ],
        [
            InlineKeyboardButton(small_caps("ꜱᴇʀᴠᴇᴅ ᴄʜᴀᴛꜱ"), callback_data="sudo_chats", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton(small_caps("ɢʟᴏʙᴀʟ ᴄᴏɴᴛʀᴏʟ"), callback_data="sudo_gcontrol", style=enums.ButtonStyle.PRIMARY)
        ],
        [
            InlineKeyboardButton(small_caps("ᴄʟᴏꜱᴇ ᴘᴀɴᴇʟ"), callback_data="sudo_close", style=enums.ButtonStyle.DANGER)
        ]
    ])


def sudo_streams_panel(active_chats):
    """Active streams sub-panel with per-group control buttons.
    
    Args:
        active_chats: list of (chat_id, title, track_count) tuples
    """
    rows = []
    for chat_id, title, count in active_chats[:8]:
        short_title = title[:18] + ".." if len(title) > 20 else title
        rows.append([
            InlineKeyboardButton(
                f"{short_title} ({count})",
                callback_data=f"sudo_gc_{chat_id}",
                style=enums.ButtonStyle.DEFAULT
            )
        ])
    rows.append([
        InlineKeyboardButton(small_caps("ʀᴇꜰʀᴇꜱʜ"), callback_data="sudo_streams", style=enums.ButtonStyle.DEFAULT),
        InlineKeyboardButton(small_caps("ʙᴀᴄᴋ"), callback_data="sudo_back", style=enums.ButtonStyle.PRIMARY)
    ])
    return InlineKeyboardMarkup(rows)


def sudo_group_control_panel(chat_id):
    """Per-group music control panel for sudo users."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(small_caps("ᴘᴀᴜꜱᴇ"), callback_data=f"sudo_do_pause_{chat_id}", style=enums.ButtonStyle.DEFAULT),
            InlineKeyboardButton(small_caps("ʀᴇꜱᴜᴍᴇ"), callback_data=f"sudo_do_resume_{chat_id}", style=enums.ButtonStyle.SUCCESS),
            InlineKeyboardButton(small_caps("ꜱᴋɪᴘ"), callback_data=f"sudo_do_skip_{chat_id}", style=enums.ButtonStyle.DEFAULT)
        ],
        [
            InlineKeyboardButton(small_caps("ꜱᴛᴏᴘ"), callback_data=f"sudo_do_stop_{chat_id}", style=enums.ButtonStyle.DANGER),
            InlineKeyboardButton(small_caps("ꜱʜᴜꜰꜰʟᴇ"), callback_data=f"sudo_do_shuffle_{chat_id}", style=enums.ButtonStyle.DEFAULT)
        ],
        [
            InlineKeyboardButton(small_caps("ʙᴀᴄᴋ ᴛᴏ ꜱᴛʀᴇᴀᴍꜱ"), callback_data="sudo_streams", style=enums.ButtonStyle.PRIMARY)
        ]
    ])


def sudo_stats_panel():
    """Stats sub-panel with back."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(small_caps("ʀᴇꜰʀᴇꜱʜ"), callback_data="sudo_stats", style=enums.ButtonStyle.DEFAULT),
            InlineKeyboardButton(small_caps("ʙᴀᴄᴋ"), callback_data="sudo_back", style=enums.ButtonStyle.PRIMARY)
        ]
    ])


def sudo_chats_panel(page=0, total_pages=1):
    """Served chats sub-panel with pagination."""
    rows = []
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(small_caps("ᴘʀᴇᴠ"), callback_data=f"sudo_chats_{page - 1}", style=enums.ButtonStyle.DEFAULT))
    nav.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop", style=enums.ButtonStyle.DEFAULT))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(small_caps("ɴᴇxᴛ"), callback_data=f"sudo_chats_{page + 1}", style=enums.ButtonStyle.DEFAULT))
    if nav:
        rows.append(nav)
    rows.append([
        InlineKeyboardButton(small_caps("ʙᴀᴄᴋ ᴛᴏ ᴘᴀɴᴇʟ"), callback_data="sudo_back", style=enums.ButtonStyle.PRIMARY)
    ])
    return InlineKeyboardMarkup(rows)


def sudo_gcontrol_panel():
    """Global control sub-panel."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(small_caps("ꜰᴏʀᴄᴇ ʟᴇᴀᴠᴇ ᴀʟʟ"), callback_data="sudo_forceleave", style=enums.ButtonStyle.DANGER)
        ],
        [
            InlineKeyboardButton(small_caps("ʙᴀᴄᴋ ᴛᴏ ᴘᴀɴᴇʟ"), callback_data="sudo_back", style=enums.ButtonStyle.PRIMARY)
        ]
    ])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Confirmation Dialog Keyboards
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def confirm_action(action_data: str):
    """Generic confirmation keyboard with Confirm/Cancel buttons.
    
    Args:
        action_data: The callback data suffix for the confirm action.
                     Full callback will be 'confirmed_{action_data}'.
    """
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(small_caps("ᴄᴏɴꜰɪʀᴍ"), callback_data=f"confirmed_{action_data}", style=enums.ButtonStyle.SUCCESS),
            InlineKeyboardButton(small_caps("ᴄᴀɴᴄᴇʟ"), callback_data="cancel_confirm", style=enums.ButtonStyle.DANGER)
        ]
    ])
