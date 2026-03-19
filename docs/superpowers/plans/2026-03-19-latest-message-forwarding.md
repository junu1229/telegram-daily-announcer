# Latest Message Forwarding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace fixed message forwarding with automatic forwarding of the latest channel post, using python-telegram-bot's Application for both listening and scheduling.

**Architecture:** The bot runs as a `python-telegram-bot` `Application` with polling. A `MessageHandler` listens to the source channel and persists the latest message ID to `data/latest_message.json` (atomic write). A `JobQueue.run_daily` job forwards that message at 9 AM KST. `scheduler.py` and standalone APScheduler are removed.

**Tech Stack:** python-telegram-bot 20.7 with `[job-queue]` extra, python-dotenv

**Spec:** `docs/superpowers/specs/2026-03-19-latest-message-forwarding-design.md`

---

### Task 1: Update configuration files

**Files:**
- Modify: `config.py`
- Modify: `requirements.txt`
- Modify: `.env.example`
- Modify: `.gitignore`
- Modify: `docker-compose.yml`

- [ ] **Step 1: Update `config.py`**

Remove `SOURCE_MESSAGE_ID`, add `LATEST_MESSAGE_FILE`:

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
SOURCE_CHANNEL_ID = os.getenv("SOURCE_CHANNEL_ID")

SCHEDULE_HOUR = 9
SCHEDULE_MINUTE = 0
TIMEZONE = "Asia/Seoul"

LATEST_MESSAGE_FILE = Path(__file__).parent / "data" / "latest_message.json"
```

- [ ] **Step 2: Update `requirements.txt`**

Replace `python-telegram-bot==20.7` with the `[job-queue]` extra (which bundles APScheduler internally), and remove standalone APScheduler:

```
python-telegram-bot[job-queue]==20.7
python-dotenv==1.0.0
```

- [ ] **Step 3: Update `.env.example`**

Remove `SOURCE_MESSAGE_ID`:

```
# Telegram bot token from @BotFather
BOT_TOKEN=

# Target channel (e.g., @channel_name or numeric ID)
CHANNEL_ID=@

# Source channel to copy message from (bot must be admin of this channel)
SOURCE_CHANNEL_ID=@
```

- [ ] **Step 4: Update `.gitignore`**

Add `data/` directory:

```
.env
venv/
__pycache__/
*.pyc
*.log
.DS_Store
data/
```

- [ ] **Step 5: Update `docker-compose.yml`**

Add volume mount for persistent storage:

```yaml
services:
  bot:
    build: .
    env_file:
      - .env
    restart: unless-stopped
    volumes:
      - ./data:/app/data
```

- [ ] **Step 6: Commit**

```bash
git add config.py requirements.txt .env.example .gitignore docker-compose.yml
git commit -m "Update config for latest message forwarding"
```

---

### Task 2: Rewrite `message_sender.py`

**Files:**
- Modify: `message_sender.py`

This module exports two functions:
- `save_latest_message(message)` — atomically writes message ID to JSON
- `forward_latest_message(bot)` — reads JSON, forwards message via Bot instance

- [ ] **Step 1: Rewrite `message_sender.py`**

```python
import json
import os
import tempfile
from datetime import datetime, timezone

from telegram import Bot, Message

import config


def save_latest_message(message: Message) -> None:
    """Save the latest message ID to JSON file (atomic write)."""
    data = {
        "source_channel_id": message.chat.id,
        "message_id": message.message_id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    config.LATEST_MESSAGE_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Atomic write: write to temp file, then rename
    fd, tmp_path = tempfile.mkstemp(
        dir=config.LATEST_MESSAGE_FILE.parent, suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f)
        os.replace(tmp_path, config.LATEST_MESSAGE_FILE)
    except BaseException:
        os.unlink(tmp_path)
        raise

    print(f"Latest message saved: ID {message.message_id}")


async def forward_latest_message(bot: Bot) -> bool:
    """Read latest message ID from JSON and forward it."""
    if not config.LATEST_MESSAGE_FILE.exists():
        print("No latest message file found. Skipping.")
        return False

    try:
        with open(config.LATEST_MESSAGE_FILE) as f:
            data = json.load(f)
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Failed to read latest message file: {e}")
        return False

    try:
        await bot.forward_message(
            chat_id=config.CHANNEL_ID,
            from_chat_id=data["source_channel_id"],
            message_id=data["message_id"],
        )
        print(f"Forwarded message {data['message_id']}!")
        return True
    except Exception as e:
        print(f"Forward failed: {e}")
        return False
```

- [ ] **Step 2: Commit**

```bash
git add message_sender.py
git commit -m "Rewrite message_sender with save/forward functions"
```

---

### Task 3: Rewrite `bot.py`

**Files:**
- Modify: `bot.py`

Sets up `Application` with:
- A `MessageHandler` that filters channel posts from `SOURCE_CHANNEL_ID` (excluding service messages) and calls `save_latest_message`
- A `JobQueue.run_daily` job that calls `forward_latest_message` at 9 AM KST
- Test mode that creates a lightweight `Bot` instance and forwards immediately

- [ ] **Step 1: Rewrite `bot.py`**

```python
import asyncio
import sys
import zoneinfo
from datetime import time

from telegram import Bot, Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

import config
from message_sender import forward_latest_message, save_latest_message


async def handle_channel_post(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Store the latest message ID when a new post arrives in the source channel."""
    save_latest_message(update.channel_post)


async def scheduled_forward(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Forward the latest stored message on schedule."""
    await forward_latest_message(context.bot)


def run_test() -> None:
    """Test mode: forward latest message immediately and exit."""
    bot = Bot(token=config.BOT_TOKEN)
    result = asyncio.run(forward_latest_message(bot))
    if not result:
        sys.exit(1)


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Test mode: forwarding latest message now.")
        run_test()
        return

    application = Application.builder().token(config.BOT_TOKEN).build()

    # Handler: listen for channel posts from source channel (exclude service messages)
    # SOURCE_CHANNEL_ID can be "@username" or numeric ID like "-1001234567"
    src = config.SOURCE_CHANNEL_ID
    if src.lstrip("-").isdigit():
        chat_filter = filters.Chat(chat_id=int(src))
    else:
        chat_filter = filters.Chat(username=src.lstrip("@"))
    source_filter = (
        filters.UpdateType.CHANNEL_POST & chat_filter & ~filters.StatusUpdate.ALL
    )
    application.add_handler(MessageHandler(source_filter, handle_channel_post))

    # Job: forward latest message daily
    tz = zoneinfo.ZoneInfo(config.TIMEZONE)
    application.job_queue.run_daily(
        scheduled_forward,
        time=time(hour=config.SCHEDULE_HOUR, minute=config.SCHEDULE_MINUTE, tzinfo=tz),
        name="daily_announcement",
    )

    print(f"Bot started!")
    print(f"Listening for posts in {config.SOURCE_CHANNEL_ID}")
    print(
        f"Forwarding daily at {config.SCHEDULE_HOUR}:{config.SCHEDULE_MINUTE:02d} ({config.TIMEZONE})"
    )
    print("Press Ctrl+C to stop.")

    application.run_polling(allowed_updates=["channel_post"])


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add bot.py
git commit -m "Rewrite bot.py with Application, handler, and JobQueue"
```

---

### Task 4: Delete `scheduler.py`

**Files:**
- Delete: `scheduler.py`

- [ ] **Step 1: Delete `scheduler.py`**

```bash
git rm scheduler.py
```

- [ ] **Step 2: Commit**

```bash
git commit -m "Remove scheduler.py, replaced by Application JobQueue"
```

---

### Task 5: Update `CLAUDE.md`

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update `CLAUDE.md`**

Replace the full contents with:

```markdown
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Telegram bot that forwards the latest message from a source channel to a target channel on a daily schedule (default: 9:00 AM KST). The bot listens for new posts in the source channel and stores the latest message ID for forwarding.

## Prerequisites

- The bot must be an **admin** of the source channel (required to receive channel posts)

## Commands

```bash
# Setup
cp .env.example .env   # Fill in your bot token and channel IDs

# Install dependencies (requires Python 3.13+)
pip install -r requirements.txt

# Run bot (listens for messages + forwards on schedule)
python bot.py

# Test mode - forwards the latest stored message immediately
python bot.py --test
```

### Docker

```bash
make build    # Build Docker image
make up       # Start container (detached)
make down     # Stop container
make logs     # View logs
make test     # Run in test mode
make clean    # Clean up Docker resources
make install  # pip install (after activating venv)
```

## Architecture

The bot uses `python-telegram-bot`'s `Application` for both message listening (polling) and scheduling (`JobQueue`).

- A `MessageHandler` watches the source channel and saves the latest message ID to `data/latest_message.json` (atomic write)
- A `JobQueue.run_daily` job forwards the stored message at the scheduled time

**Flow:** `bot.py` (Application) → handler saves latest ID → `JobQueue` daily trigger → `message_sender.py` forwards

## Configuration

Environment variables loaded from `.env` (see `.env.example`):
- `BOT_TOKEN`: Telegram bot token from @BotFather
- `CHANNEL_ID`: Target channel (e.g., `@channel_name` or numeric ID)
- `SOURCE_CHANNEL_ID`: Source channel to listen to (bot must be admin)

Hardcoded constants in `config.py` (edit file directly to change):
- `SCHEDULE_HOUR`, `SCHEDULE_MINUTE`: When to send (default 9:00)
- `TIMEZONE`: Timezone for scheduling (default `Asia/Seoul`)
- `LATEST_MESSAGE_FILE`: Path to stored message ID (default `data/latest_message.json`)
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "Update CLAUDE.md for new architecture"
```

---

### Task 6: Manual verification

- [ ] **Step 1: Verify imports and syntax**

```bash
python -c "import bot; import message_sender; import config; print('All imports OK')"
```

Expected: `All imports OK`

- [ ] **Step 2: Verify test mode error handling (no data file)**

```bash
python bot.py --test
```

Expected: prints "No latest message file found. Skipping." and exits with code 1

- [ ] **Step 3: Verify bot starts (Ctrl+C to stop)**

```bash
timeout 5 python bot.py || true
```

Expected: prints "Bot started!" and listening info, then exits after timeout
