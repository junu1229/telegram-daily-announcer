.PHONY: build up down logs test install clean

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

test:
	docker compose run --rm bot python bot.py --test

install:
	pip install -r requirements.txt

clean:
	docker compose down --rmi local -v
