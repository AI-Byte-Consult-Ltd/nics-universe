import argparse
import time

from universe.world.universe import Universe
from universe.storage import db

STATUS_EVERY_TICKS = 24
AUTOSAVE_EVERY_TICKS = 24


def build_universe(reset: bool) -> Universe:
    if reset:
        db.reset()
        print("Вселенная обнулена. Начинаем заново.\n")

    snapshot = db.load_latest_snapshot()
    if snapshot is not None:
        universe = Universe.from_dict(snapshot)
        print(f"Загружена сохранённая вселенная (тик {universe.tick}, эпоха «{universe.era}»).\n")
        return universe

    universe = Universe()
    universe.genesis()
    return universe


def main():
    parser = argparse.ArgumentParser(description="NICS Self-Evolving Universe")
    parser.add_argument("--reset", action="store_true",
                         help="Стереть сохранённую вселенную и начать с нуля")
    parser.add_argument("--speed", type=float, default=1.0,
                         help="Секунд реального времени на тик (по умолчанию 1.0)")
    parser.add_argument("--fast", action="store_true",
                         help="Без задержки между тиками (для отладки)")
    parser.add_argument("--ticks", type=int, default=0,
                         help="Остановиться после N тиков (0 = бесконечно)")
    args = parser.parse_args()

    print("NICS SELF-EVOLVING UNIVERSE")
    print("============================\n")

    universe = build_universe(reset=args.reset)
    universe.status()

    delay = 0.0 if args.fast else args.speed
    print("Симуляция запущена. Ctrl+C — остановить и сохранить.\n")

    ran = 0
    try:
        while True:
            universe.advance_time(1)
            ran += 1

            if universe.tick % STATUS_EVERY_TICKS == 0:
                universe.status()

            if universe.tick % AUTOSAVE_EVERY_TICKS == 0:
                db.save_snapshot(universe)

            if not universe.living():
                print("Вселенная опустела.")
                break

            if args.ticks and ran >= args.ticks:
                break

            if delay:
                time.sleep(delay)

    except KeyboardInterrupt:
        print("\n\nСимуляция остановлена пользователем.")
        universe.status(detailed=True)

    db.save_snapshot(universe)
    print("Прогресс сохранён. До встречи.")


if __name__ == "__main__":
    main()
