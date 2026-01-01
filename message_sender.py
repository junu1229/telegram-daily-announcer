import asyncio
from telegram import Bot
import config


async def send_message():
    """소스 채널의 메시지를 대상 채널로 복사합니다."""
    bot = Bot(token=config.BOT_TOKEN)

    try:
        await bot.copy_message(
            chat_id=config.CHANNEL_ID,
            from_chat_id=config.SOURCE_CHANNEL_ID,
            message_id=config.SOURCE_MESSAGE_ID
        )
        print("공지 발송 완료!")
        return True
    except Exception as e:
        print(f"발송 실패: {e}")
        return False


def send_announcement():
    """스케줄러에서 호출하는 동기 함수"""
    asyncio.run(send_message())
