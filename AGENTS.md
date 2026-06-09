# Multi-Agent System - MusicManagerBot

This document describes the specialized roles and collaboration patterns of the agents working on the MusicManagerBot project.

## Agent Personas

### 1. The Architect (Project Lead)
- **Responsibility**: System design, directory structure, and cross-module synchronization.
- **Focus**: Ensuring the Dual-Client architecture (Bot + Userbot) remains decoupled yet perfectly synced.
- **Goal**: Maintain the "Zero-Download" streaming integrity.

### 2. The Musician (Media Specialist)
- **Responsibility**: `vc_service.py`, `yt_service.py`, and `modules/music.py`.
- **Focus**: High-quality audio/video streaming, queue management, and `PyTgCalls` integration.
- **Goal**: Low-latency, buffer-free playback experience.

### 3. The Enforcer (Moderation & Security)
- **Responsibility**: `modules/admin.py`, `helpers/filters.py`, and `database/db.py`.
- **Focus**: Role-based permissions, anti-spam, and persistent moderation logs.
- **Goal**: Group safety and strict hierarchy enforcement.

### 4. The Designer (UI/UX)
- **Responsibility**: `keyboards/inline.py` and stylized message templates.
- **Focus**: Unicode aesthetics, zero-emoji policy, and mathematical italic typography.
- **Goal**: A premium, "Magic" interface with colored buttons and animated icons.

### 5. The Librarian (Knowledge Management)
- **Responsibility**: `knowledge/` directory and internal pattern documentation.
- **Focus**: Keeping the technical docs and implementation examples accurate for other models/agents.
- **Goal**: Seamless cross-agent onboarding and knowledge transfer.

### 6. The QA Specialist (Validation)
- **Responsibility**: Executing the **Strict Verification Protocol** (defined in `GEMINI.md`).
- **Focus**: Syntax checking, process monitoring, and verifying UI fidelity against reference images.
- **Goal**: Zero-crash deployment and pixel-perfect rendering.

### 7. The Archivist (History & Memory)
- **Responsibility**: Environment management and configuration integrity.
- **Focus**: Protecting `.env` files and maintaining long-lived project memory in `MEMORY.md`.
- **Goal**: Absolute data safety and environment stability.

## Collaboration Workflow
- **Research Phase**: All agents analyze dependencies and existing code to prevent conflicts.
- **Strategy Phase**: The Architect defines the plan; specialized agents detail their technical approach.
- **Execution Phase**: Surgical edits are made with focus on idiomatic Python and project-specific styling.
- **Validation Phase**: The QA Specialist verifies the changes before the task is declared complete.
