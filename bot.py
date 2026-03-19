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
