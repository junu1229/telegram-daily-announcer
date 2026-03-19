import asyncio
import sys
import zoneinfo
from datetime import time

from telegram import Bot, Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

import config
from message_sender import forward_latest_message, save_latest_message


async def debug_all_posts(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Debug: log all incoming messages (channel posts and group messages)."""
    msg = update.channel_post or update.message
    if msg:
        print(f"[DEBUG] Received from chat: id={msg.chat.id}, type={msg.chat.type}, username={msg.chat.username}, title={msg.chat.title}")


async def handle_source_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Store the latest message ID when a new post arrives in the source chat."""
    msg = update.channel_post or update.message
    if msg:
        save_latest_message(msg)


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
    if not config.BOT_TOKEN or not config.CHANNEL_ID or not config.SOURCE_CHANNEL_ID:
        sys.exit("Error: BOT_TOKEN, CHANNEL_ID, and SOURCE_CHANNEL_ID must be set in .env")

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
    # Support both channel posts and group messages
    update_type_filter = filters.UpdateType.CHANNEL_POST | filters.UpdateType.MESSAGE
    source_filter = (
        update_type_filter & chat_filter & ~filters.StatusUpdate.ALL
    )
    # Debug handler: log ALL incoming posts/messages (no filter)
    application.add_handler(MessageHandler(update_type_filter, debug_all_posts), group=-1)
    application.add_handler(MessageHandler(source_filter, handle_source_message))

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

    application.run_polling(allowed_updates=["channel_post", "message"])


if __name__ == "__main__":
    main()
