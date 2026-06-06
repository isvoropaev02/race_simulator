import json
import pygame
from pathlib import Path
from src.athlete import Athlete
from src.track import Track
from src.simulation import RaceSimulation
from src.renderer import Renderer
from src.form_result_table import export_results_png, print_pretty_results
from src.logger import logger

SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 800
FPS = 30
TIME_SCALE_SKI = 200.0
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
            logger.warning(f"Sportsman with id: '{aid}' not found in athletes.json.")
            continue
        athlete_list.append(athletes_db[aid])
    return athlete_list


def run():
    athletes_db = load_athletes(ATHLETES_FILE)
    logger.info(f"Loaded {len(athletes_db)} sportsmen.")
    main_track = Track(TRACK_FILE)
    logger.info(f"Main track length: {main_track.total_length:.0f} m, {len(main_track.segments)} segments.")
    penalty_track = Track(PENALTY_FILE)
    logger.info(f"Penalty loop length: {penalty_track.total_length:.0f} m.")

    race_athletes = load_race_athletes(RACE_SETUP_FILE, athletes_db)
    if not race_athletes:
        logger.error("No athletes in race_setup.json.")
        return
    logger.info(f"Total participants: {len(race_athletes)}")

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Biathlon Sprint Simulator")
    clock = pygame.time.Clock()
    renderer = Renderer(screen, main_track, penalty_track)

    results = []
    for idx, athlete in enumerate(race_athletes, start=1):
        logger.info(f"Started {idx}/{len(race_athletes)}: {athlete.name} ({athlete.country})")

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

            # Передаём актуальные результаты в рендерер для таблицы лидеров
            renderer.set_results(results)  # <-- новое

            renderer.draw(status)
            pygame.display.flip()

            if status["finished"]:
                # Запись результата с суммарными промахами
                result = {
                    "name": athlete.name,
                    "country": athlete.country,
                    "time": status["time"],
                    "misses": status["total_misses"],  # <-- изменено
                }
                results.append(result)
                # Небольшая пауза, чтобы увидеть финиш на экране
                pygame.time.wait(1500)
                running = False

    renderer.set_results(results)
    renderer.draw({})
    print_pretty_results(results)
    export_results_png(results)
    pygame.time.wait(2000)
    pygame.quit()


if __name__ == "__main__":
    run()
