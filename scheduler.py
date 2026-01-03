from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from message_sender import send_announcement
import config


def start_scheduler():
    """매일 지정된 시간에 공지를 발송하는 스케줄러를 시작합니다."""
    scheduler = BlockingScheduler(timezone=config.TIMEZONE)

    scheduler.add_job(
        send_announcement,
        CronTrigger(hour=config.SCHEDULE_HOUR, minute=config.SCHEDULE_MINUTE, timezone=config.TIMEZONE),
        id="daily_announcement"
    )

    print(f"스케줄러 시작!")
    print(f"매일 {config.SCHEDULE_HOUR}:{config.SCHEDULE_MINUTE:02d} ({config.TIMEZONE})에 공지 발송")
    print("종료하려면 Ctrl+C를 누르세요.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n스케줄러 종료")
