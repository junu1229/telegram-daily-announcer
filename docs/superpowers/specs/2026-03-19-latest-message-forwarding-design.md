# Design: Forward Latest Channel Message

## Problem

The bot currently forwards a fixed message (`SOURCE_MESSAGE_ID`) from the source channel. The user wants to forward the most recent message in the source channel at the time of the daily schedule (9 AM KST).

## Solution

Replace APScheduler with `python-telegram-bot`'s built-in `Application` that handles both message listening and scheduling. Store the latest message ID to a JSON file for persistence across restarts.

## Architecture

**Current flow:** `bot.py` -> `scheduler.py` (APScheduler cron) -> `message_sender.py` (asyncio.run bridge)

**New flow:** `bot.py` (Application with polling + JobQueue) -> handler stores latest message ID to file -> JobQueue cron trigger -> forward stored message

The `Application` object replaces both the APScheduler scheduler and the manual async bridging. `scheduler.py` is deleted.

## Persistent Storage

`latest_message.json` in project root:

```json
{
  "source_channel_id": "-100123456",
  "message_id": 4567,
  "updated_at": "2026-03-19T08:30:00+09:00"
}
```

- Overwritten on every new message in the source channel
- Read at schedule time
- Gitignored

## Configuration Changes

- Remove `SOURCE_MESSAGE_ID` from `.env` and `config.py`
- Add `LATEST_MESSAGE_FILE` constant in `config.py` (path to `latest_message.json`)
- Add `latest_message.json` to `.gitignore`
- Keep all other config unchanged

## File Changes

| File | Action |
|------|--------|
| `bot.py` | Rewrite — `Application` with handler + `JobQueue` |
| `message_sender.py` | Refactor — read from JSON, forward via bot context |
| `config.py` | Update — remove `SOURCE_MESSAGE_ID`, add `LATEST_MESSAGE_FILE` |
| `scheduler.py` | Delete — replaced by `JobQueue` |
| `latest_message.json` | New (runtime) — auto-created, gitignored |
| `.env.example` | Update — remove `SOURCE_MESSAGE_ID` |
| `.gitignore` | Update — add `latest_message.json` |
| `CLAUDE.md` | Update — reflect new architecture |
| `requirements.txt` | Update — remove APScheduler |

## Error Handling

- **No stored message at schedule time**: Log warning, skip.
- **Forward fails** (deleted message, permissions): Log error, skip.
- **Bot restarts**: Reads `latest_message.json`, resumes receiving new messages within seconds.

## Test Mode

`python bot.py --test` reads `latest_message.json` and forwards immediately. If no file exists, prints an error and exits.
