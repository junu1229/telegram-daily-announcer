import sys
from scheduler import start_scheduler
from message_sender import send_announcement


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("테스트 모드: 공지를 즉시 발송합니다.")
        send_announcement()
    else:
        start_scheduler()


if __name__ == "__main__":
    main()
