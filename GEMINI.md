# MusicManagerBot - Project Instructions

## Core Mandates

### 1. Aesthetic Integrity
- **Zero Emojis**: Do NOT use emojis anywhere in the bot's responses or buttons unless explicitly requested by the user for a specific exception.
- **Unicode Styling**: Consistently use Unicode Small Caps for buttons and Mathematical Fraktur/Spaced text for headers as established in `modules/base.py`.
- **Decorative Elements**: Use box-drawing characters and horizontal dividers (`━━━━━━━━`) for a premium layout.

### 2. Architectural Standards
- **Modular Handlers**: Keep commands organized in their respective `modules/` files.
- **Dual-Client Sync**: Always consider how a change affects both the Bot and the Userbot.
- **Non-Blocking DB**: All database operations must be wrapped in thread pool executors to avoid blocking the `asyncio` loop.

## Strict Verification Protocol
Before declaring a task "Done" or asking for feedback, you **MUST**:
1. **Full Code Audit**: Review all modified files for syntax errors, missing imports, or logic flaws.
2. **Execution Test**: Attempt to run `python main.py` (or the relevant entry point).
3. **Error Handling**:
   - If a **Simple/Non-Breaking Error** occurs (e.g., missing import, typo), fix it immediately without over-engineering.
   - If a **Complex Error** occurs that requires a strategy change, update the user before proceeding.
4. **Finality**: Only state that you are ready for feedback once the bot starts successfully without immediate crashes and the specific logic of the task has been verified against the code.

## File Hierarchy
1. `PRD.md`: Feature requirements.
2. `Overview.md`: System architecture.
3. `AGENTS.md`: Specialized roles.
4. `GEMINI.md`: (This file) Strict coding and validation mandates.
