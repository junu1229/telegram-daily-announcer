# Design: Forward Latest Channel Message

## Problem

The bot currently forwards a fixed message (`SOURCE_MESSAGE_ID`) from the source channel. The user wants to forward the most recent message in the source channel at the time of the daily schedule (9 AM KST).

## Solution

Replace APScheduler with `python-telegram-bot`'s built-in `Application` that handles both message listening and scheduling. Store the latest message ID to a JSON file for persistence across restarts.

## Prerequisites

- The bot must be added as an **administrator** of the source channel (required to receive channel posts via polling)

## Architecture

**Current flow:** `bot.py` -> `scheduler.py` (APScheduler cron) -> `message_sender.py` (asyncio.run bridge)

**New flow:** `bot.py` (Application with polling + JobQueue) -> handler stores latest message ID to file -> JobQueue cron trigger -> forward stored message

- `Application.run_polling()` with `allowed_updates=["channel_post"]` to receive source channel messages
- `MessageHandler` filters for `SOURCE_CHANNEL_ID` and writes latest message ID to file
- `JobQueue` with daily trigger replaces APScheduler cron
- `scheduler.py` is deleted

### Message Filtering

Only regular channel posts are tracked (text, photo, video, etc.). Service messages (e.g., "channel photo changed", pin notifications) are ignored via `~filters.StatusUpdate.ALL`.

## Persistent Storage

`latest_message.json` in `data/` subdirectory:

```json
{
  "source_channel_id": -100123456,
  "message_id": 4567,
  "updated_at": "2026-03-19T08:30:00+09:00"
}
```

- Overwritten atomically on every new channel post (write to tempfile + `os.replace`)
- Read at schedule time
- `data/` directory gitignored

## Configuration Changes

- Remove `SOURCE_MESSAGE_ID` from `.env` and `config.py`
- Add `LATEST_MESSAGE_FILE` constant in `config.py` (default: `data/latest_message.json`)
- Add `data/` to `.gitignore`
- Keep all other config unchanged

## Module Boundaries

- **`bot.py`**: Sets up `Application`, registers handler and job. Entry point.
- **`message_sender.py`**: Exports two functions:
  - `save_latest_message(message)` — writes message ID to JSON (called by handler)
  - `forward_latest_message(bot)` — reads JSON, forwards via given `Bot` instance (called by both job callback and test mode)
- **`config.py`**: Constants only.

## File Changes

| File | Action |
|------|--------|
| `bot.py` | Rewrite — `Application` with handler + `JobQueue` |
| `message_sender.py` | Refactor — `save_latest_message()` + `forward_latest_message(bot)` |
| `config.py` | Update — remove `SOURCE_MESSAGE_ID`, add `LATEST_MESSAGE_FILE` |
| `scheduler.py` | Delete — replaced by `JobQueue` |
| `data/latest_message.json` | New (runtime) — auto-created, gitignored |
| `.env.example` | Update — remove `SOURCE_MESSAGE_ID` |
| `.gitignore` | Update — add `data/` |
| `docker-compose.yml` | Update — add volume mount for `data/` |
| `CLAUDE.md` | Update — reflect new architecture |
| `requirements.txt` | Update — remove APScheduler |

## Docker

Add a volume mount in `docker-compose.yml` so `data/latest_message.json` persists across container recreation:

```yaml
volumes:
  - ./data:/app/data
```

## Error Handling

- **No stored message at schedule time**: Log warning, skip.
- **Forward fails** (deleted message, permissions): Log error, skip.
- **Bot restarts**: Reads `data/latest_message.json`, resumes receiving new messages within seconds.

## Test Mode

`python bot.py --test` creates a lightweight `Bot` instance directly (not a full `Application`), reads `data/latest_message.json`, forwards immediately, and exits. If no file exists, prints an error and exits.
