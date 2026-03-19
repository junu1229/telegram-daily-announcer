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
