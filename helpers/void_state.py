import time
from config import Config
from helpers.styling import small_caps

class VoidState:
    observe_active = False
    phantom_active = False
    ghost_watches = {}       # owner_id -> chat_id
    blackbox_recording = False
    blackbox_start = 0
    blackbox_events = []

async def trigger_void_event(client, event_type: str, description: str):
    # Record for blackbox
    if VoidState.blackbox_recording:
        # Check if 5 minutes expired (300 seconds)
        if time.time() - VoidState.blackbox_start > 300:
            VoidState.blackbox_recording = False
        else:
            VoidState.blackbox_events.append({
                "timestamp": int(time.time()),
                "type": event_type,
                "description": description
            })
            
    # Send for observe log stream
    if VoidState.observe_active:
        try:
            log_text = f"<blockquote>[<b>{event_type.upper()}</b>]</blockquote>\n" \
                       f"<blockquote>{description}</blockquote>"
            await client.send_message(Config.OWNER_ID, log_text)
        except Exception:
            pass
