import math
import random
from enum import Enum, auto

V_MAX_UPHILL = 5.5  # м/с на подъёме при навыке 100
V_MAX_FLAT = 8.0  # м/с на равнине при навыке 100
V_MAX_DOWNHILL = 9.5  # м/с на спуске при навыке 100

FATIGUE_RATE = 0.003  # базовая скорость роста усталости (в единицах усталости за секунду)
FATIGUE_FACTOR = {"uphill": 1.5, "flat": 1.0, "downhill": 0.6}  # множители накопления усталости в зависимости от рельефа
K_FATIGUE = 0.15  # насколько сильно усталость замедляет (скорость *= (1 - k*F))

T_BASE_SHOT = 3.0  # базовый интервал между выстрелами, сек
P_HIT_MIN = 0.2  # минимальный шанс попадания даже при нулевом навыке точности


class Athlete:
    """Базовые характеристики спортсмена (не меняются во время гонки)."""

    def __init__(self, athlete_id: str, name: str, country: str, age: int, skills: dict):
        self.id = athlete_id
        self.name = name
        self.country = country
        self.age = age
        self.skills = skills  # ожидаются ключи: uphill, flat, downhill,
        # shoot_speed_prone, shoot_acc_prone,
        # shoot_speed_stand, shoot_acc_stand, finish_sprint

    @staticmethod
    def from_dict(data: dict):
        """Создать объект из словаря (например, прочитанного из JSON)."""
        return Athlete(
            athlete_id=data["id"], name=data["name"], country=data["country"], age=data["age"], skills=data["skills"]
        )


class ShootingState(Enum):
    """Внутренние фазы стрельбы."""

    IDLE = auto()
    AWAITING_SHOT = auto()
    FINISHED = auto()


class AthleteState:
    """Текущее состояние гонки для одного спортсмена."""

    def __init__(self, athlete: Athlete):
        self.athlete = athlete
        self.distance = 0.0  # пройденная дистанция по текущему кругу/сегменту, м
        self.total_distance = 0.0  # общая дистанция за гонку (можно не вести, но удобно для усталости)
        self.fatigue = 0.0  # уровень усталости (0 = свеж)
        self.speed = 0.0  # текущая скорость, м/с (вычисляется при каждом обновлении)
        self.time = 0.0  # общее время гонки спортсмена, сек

        # Стрельба
        self.shooting_state = ShootingState.IDLE
        self.shot_timer = 0.0  # таймер до следующего выстрела
        self.shots_fired = 0  # сколько выстрелов уже сделано
        self.misses = 0  # сколько промахов в текущей серии
        self.shooting_type = None  # 'prone' или 'stand'
        self.shot_interval = 0.0  # интервал между выстрелами (вычисляется при старте стрельбы)
        self.total_misses = 0
        self.shot_results = []

    # -----------------------------------------------------------------
    # Движение
    # -----------------------------------------------------------------
    def _slope_category(self, slope: float) -> str:
        """Определить категорию рельефа по значению уклона (в %)."""
        if slope > 0.5:
            return "uphill"
        elif slope < -0.5:
            return "downhill"
        else:
            return "flat"

    def _base_speed(self, slope: float) -> float:
        """Базовая скорость на данном уклоне без учёта усталости."""
        cat = self._slope_category(slope)
        if cat == "uphill":
            return (self.athlete.skills["uphill"] / 100.0) * V_MAX_UPHILL
        elif cat == "downhill":
            return (self.athlete.skills["downhill"] / 100.0) * V_MAX_DOWNHILL
        else:  # flat
            return (self.athlete.skills["flat"] / 100.0) * V_MAX_FLAT

    def _fatigue_multiplier(self) -> float:
        """Коэффициент замедления из-за накопленной усталости."""
        return max(0.7, 1.0 - K_FATIGUE * self.fatigue)

    def update_movement(self, dt: float, slope: float):
        """
        Продвинуть спортсмена на dt секунд по участку с уклоном slope (%).
        Обновляет пройденную дистанцию, усталость, скорость и общее время.
        """
        cat = self._slope_category(slope)
        base_v = self._base_speed(slope)
        self.speed = base_v * self._fatigue_multiplier()
        dist_delta = self.speed * dt

        self.distance += dist_delta
        self.total_distance += dist_delta
        self.time += dt

        # Рост усталости
        fatigue_gain = FATIGUE_RATE * FATIGUE_FACTOR[cat] * dt
        # Можно также добавить зависимость от дистанции (небольшой коэффициент)
        self.fatigue += fatigue_gain

    # -----------------------------------------------------------------
    # Стрельба
    # -----------------------------------------------------------------
    def start_shooting(self, shooting_type: str):
        """
        Начать стрельбу: сбросить счётчики и вычислить интервал.
        shooting_type = 'prone' или 'stand'
        """
        self.shooting_state = ShootingState.AWAITING_SHOT
        self.shot_timer = 0.0
        self.shots_fired = 0
        self.misses = 0
        self.shot_results = []
        self.shooting_type = shooting_type

        # Определяем навык скорости стрельбы
        if shooting_type == "prone":
            speed_skill = self.athlete.skills["shoot_speed_prone"]
        else:
            speed_skill = self.athlete.skills["shoot_speed_stand"]

        # Время между выстрелами (от 2.8 сек при навыке 0 до 1.2 сек при 100)
        self.shot_interval = T_BASE_SHOT * (1.4 - 0.8 * (speed_skill / 100.0))

    def update_shooting(self, dt: float):
        """
        Обработать dt секунд процесса стрельбы.
        Возвращает True, если серия завершена (можно забирать misses).
        """
        if self.shooting_state != ShootingState.AWAITING_SHOT:
            return False

        self.time += dt  # стрельба идёт в реальном времени
        self.shot_timer += dt

        # Пока не сделаны все 5 выстрелов, ждём интервала и стреляем
        while self.shots_fired < 5 and self.shot_timer >= self.shot_interval:
            self.shot_timer -= self.shot_interval
            self.shots_fired += 1
            # Проверка точности
            if self.shooting_type == "prone":
                acc_skill = self.athlete.skills["shoot_acc_prone"]
            else:
                acc_skill = self.athlete.skills["shoot_acc_stand"]

            hit_prob = P_HIT_MIN + 0.8 * (acc_skill / 100.0)
            hit = random.random() < hit_prob
            self.shot_results.append(hit)
            if not hit:
                self.misses += 1

        if self.shots_fired == 5:
            self.shooting_state = ShootingState.FINISHED
            self.total_misses += self.misses
            return True
        return False

    # -----------------------------------------------------------------
    # Штрафные круги (движение по равнине)
    # -----------------------------------------------------------------
    def update_penalty_loop(self, dt: float, loop_length: float):
        """
        Бег по штрафному кругу. loop_length – полная длина штрафного круга (150 м),
        используется для сброса дистанции при достижении конца.
        Возвращает True, если круг завершён (дистанция обнулена).
        """
        # Движемся с равнинной скоростью (slope = 0)
        self.update_movement(dt, slope=0.0)

        if self.distance >= loop_length:
            self.distance -= loop_length  # начинаем следующий круг или возврат
            return True
        return False

    # -----------------------------------------------------------------
    # Вспомогательные сбросы
    # -----------------------------------------------------------------
    def reset_loop_distance(self):
        """Обнулить счётчик дистанции текущего круга (при завершении основного круга)."""
        self.distance = 0.0

    def finish_race(self):
        """Завершить гонку, очистить стрельбу и т.д. (опционально)."""
        self.shooting_state = ShootingState.IDLE
