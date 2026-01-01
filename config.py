import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
SOURCE_CHANNEL_ID = os.getenv("SOURCE_CHANNEL_ID")
SOURCE_MESSAGE_ID = int(os.getenv("SOURCE_MESSAGE_ID", "0"))

SCHEDULE_HOUR = 9
SCHEDULE_MINUTE = 0
TIMEZONE = "Asia/Seoul"
