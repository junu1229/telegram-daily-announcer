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
