# main.py
import sys
import json
import pygame
from pathlib import Path
from src.athlete import Athlete
from src.track import Track
from src.simulation import RaceSimulation
from src.renderer import Renderer

SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 800
FPS = 30
TIME_SCALE_SKI = 9.0  # ускорение лыжной части (подобрано для ~4 мин показа)
ATHLETES_FILE = "db/athletes.json"
TRACK_FILE = "db/track.csv"
PENALTY_FILE = "db/penalty_loop.csv"
RACE_SETUP_FILE = "db/race_setup.json"


def load_athletes(filepath: str) -> dict:
    """Загружаем спортсменов из JSON, возвращаем словарь id -> Athlete."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    athletes = {}
    for item in data["athletes"]:
        a = Athlete.from_dict(item)
        athletes[a.id] = a
    return athletes


def load_race_athletes(filepath: str, athletes_db: dict) -> list:
    """Читаем список id участников, возвращаем список объектов Athlete."""
    with open(filepath, "r", encoding="utf-8") as f:
        race_data = json.load(f)
    athlete_list = []
    for aid in race_data["athletes"]:
        if aid not in athletes_db:
            print(f"Внимание: спортсмен с id '{aid}' не найден в базе, пропущен.")
            continue
        athlete_list.append(athletes_db[aid])
    return athlete_list


def run():
    # ---------- Загрузка данных ----------
    print("Загрузка спортсменов...")
    athletes_db = load_athletes(ATHLETES_FILE)
    print(f"Загружено {len(athletes_db)} спортсменов.")

    print("Загрузка трасс...")
    main_track = Track(TRACK_FILE)
    print(f"Основная трасса: {main_track.total_length:.0f} м, {len(main_track.segments)} сегментов.")
    penalty_track = Track(PENALTY_FILE)
    print(f"Штрафной круг: {penalty_track.total_length:.0f} м.")

    print("Загрузка состава гонки...")
    race_athletes = load_race_athletes(RACE_SETUP_FILE, athletes_db)
    if not race_athletes:
        print("Нет участников для гонки. Проверьте race_setup.json.")
        return
    print(f"Участников: {len(race_athletes)}")

    # ---------- Инициализация Pygame ----------
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Biathlon Sprint Simulator")
    clock = pygame.time.Clock()
    renderer = Renderer(screen, main_track, penalty_track)

    # ---------- Проведение гонок ----------
    results = []  # список словарей с итогами

    for idx, athlete in enumerate(race_athletes, start=1):
        print(f"\n=== Старт спортсмена {idx}/{len(race_athletes)}: {athlete.name} ({athlete.country}) ===")

        sim = RaceSimulation(main_track, penalty_track, time_scale_ski=TIME_SCALE_SKI)
        sim.start_athlete(athlete)

        # Главный цикл одной гонки
        running = True
        while running:
            dt_real = clock.tick(FPS) / 1000.0  # секунды реального времени

            # Обработка событий (выход)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            # Обновление симуляции
            status = sim.update(dt_real)
            renderer.draw(status)

            pygame.display.flip()

            if status["finished"]:
                # Запись результата
                result = {"name": athlete.name, "country": athlete.country, "time": status["time"]}
                results.append(result)
                print(f"Финиш: {athlete.name} — {status['time']:.1f} сек.")
                # Небольшая пауза, чтобы увидеть финиш на экране
                pygame.time.wait(1500)
                running = False

    # ---------- Итоговый протокол ----------
    print("\n=== Итоговый протокол ===")
    # Сортировка по времени
    results.sort(key=lambda r: r["time"])
    for place, r in enumerate(results, start=1):
        minutes = int(r["time"] // 60)
        seconds = r["time"] % 60
        print(f"{place}. {r['name']} ({r['country']}) — {minutes}:{seconds:05.2f}")

    # Завершение работы
    pygame.time.wait(2000)
    pygame.quit()


if __name__ == "__main__":
    run()
