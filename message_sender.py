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
