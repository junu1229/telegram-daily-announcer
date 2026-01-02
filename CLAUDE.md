# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Telegram bot that copies a message from a source channel to a target channel on a daily schedule (default: 9:00 AM KST).

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run scheduler (production mode - sends at scheduled time daily)
python bot.py

# Test mode - sends announcement immediately
python bot.py --test
```

## Architecture

The bot uses APScheduler's `BlockingScheduler` with cron triggers for daily execution. Since python-telegram-bot is async but APScheduler callbacks are sync, `message_sender.py` uses `asyncio.run()` to bridge them.

**Flow:** `bot.py` → `scheduler.py` (cron trigger) → `message_sender.py` (async Telegram API)

## Configuration

Environment variables loaded from `.env` (see `.env.example`):
- `BOT_TOKEN`: Telegram bot token from @BotFather
- `CHANNEL_ID`: Target channel (e.g., `@channel_name` or numeric ID)
- `SOURCE_CHANNEL_ID`: Source channel to copy message from
- `SOURCE_MESSAGE_ID`: Message ID to copy

Schedule settings in `config.py`:
- `SCHEDULE_HOUR`, `SCHEDULE_MINUTE`: When to send (default 9:00)
- `TIMEZONE`: Timezone for scheduling (default `Asia/Seoul`)
