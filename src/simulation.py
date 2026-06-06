from enum import Enum, auto
from src.athlete import Athlete, AthleteState, FATIGUE_FACTOR, FATIGUE_RATE
from src.track import Track


class RaceState(Enum):
    SKIING_LOOP_1 = auto()
    SHOOTING_PRONE = auto()
    SKIING_LOOP_2 = auto()
    SHOOTING_STAND = auto()
    SKIING_LOOP_3 = auto()
    PENALTY_LOOP = auto()
    FINISHED = auto()


class RaceSimulation:
    """
    Управляет гонкой одного спортсмена по трассе.
    Получает dt в реальных секундах, преобразует в sim-секунды
    с разным time_scale для лыжной части и стрельбы.
    """

    def __init__(self, main_track: Track, penalty_track: Track, time_scale_ski: float = 10.0):
        """
        main_track: основная трасса (3 круга)
        penalty_track: штрафной круг (150 м равнины)
        time_scale_ski: ускорение на лыжных участках (и штрафных кругах)
        """
        self.main_track = main_track
        self.penalty_track = penalty_track
        self.time_scale_ski = time_scale_ski
        self.time_scale_shooting = 1.0  # стрельба всегда в реальном времени

        self.state = RaceState.SKIING_LOOP_1
        self.athlete_state = AthleteState(Athlete(athlete_id="", name="", country="", age=0, skills={}))
        self.penalty_loops_remaining = 0

        self.loop_counter = 0  # сколько основных кругов завершено
        self.finished = False

    def start_athlete(self, athlete: Athlete):
        """Подготовить нового спортсмена и начать гонку."""
        self.athlete_state = AthleteState(athlete)
        self.state = RaceState.SKIING_LOOP_1
        self.loop_counter = 0
        self.penalty_loops_remaining = 0
        self.finished = False

    def update(self, dt_real: float):
        """
        Продвинуть симуляцию на dt_real секунд реального времени.
        Возвращает словарь с текущими показателями для отрисовки.
        """
        if self.finished or self.athlete_state is None:
            return self._get_status()

        # Определяем текущий временной масштаб
        if self.state in (RaceState.SHOOTING_PRONE, RaceState.SHOOTING_STAND):
            dt_sim = dt_real * self.time_scale_shooting
        else:
            dt_sim = dt_real * self.time_scale_ski

        if self.state in (RaceState.SKIING_LOOP_1, RaceState.SKIING_LOOP_2, RaceState.SKIING_LOOP_3):
            self._update_skiing(dt_sim)
        elif self.state in (RaceState.SHOOTING_PRONE, RaceState.SHOOTING_STAND):
            self._update_shooting(dt_sim)
        elif self.state == RaceState.PENALTY_LOOP:
            self._update_penalty_loop(dt_sim)

        return self._get_status()

    # -----------------------------------------------------------------
    # Внутренние обработчики этапов
    # -----------------------------------------------------------------
    def _update_skiing(self, dt_sim: float):
        """Лыжное движение по основному кругу."""
        athlete = self.athlete_state
        track = self.main_track

        dist = athlete.distance
        while dt_sim > 0:
            # Текущий сегмент и его длина
            seg, dist_in_seg = track.get_segment(dist)
            remaining_in_seg = seg.length - dist_in_seg

            # Скорость и время до конца сегмента
            athlete.speed = athlete._base_speed(seg.slope) * athlete._fatigue_multiplier()
            if athlete.speed <= 0:
                break
            time_to_seg_end = remaining_in_seg / athlete.speed

            if time_to_seg_end <= dt_sim:
                # Перемещаемся точно до конца сегмента
                athlete.distance += remaining_in_seg
                athlete.total_distance += remaining_in_seg
                athlete.time += time_to_seg_end
                athlete.fatigue += FATIGUE_RATE * FATIGUE_FACTOR[athlete._slope_category(seg.slope)] * time_to_seg_end
                dt_sim -= time_to_seg_end
                dist += remaining_in_seg

                # Проверка завершения круга
                if athlete.distance >= track.total_length:
                    athlete.distance -= track.total_length
                    dist = 0.0
                    self._finish_loop()
                    break  # выходим из цикла, состояние изменилось
            else:
                # Оставшегося времени не хватает до конца сегмента
                move = athlete.speed * dt_sim
                athlete.distance += move
                athlete.total_distance += move
                athlete.time += dt_sim
                athlete.fatigue += FATIGUE_RATE * FATIGUE_FACTOR[athlete._slope_category(seg.slope)] * dt_sim
                dt_sim = 0

    def _finish_loop(self):
        """Завершение основного круга и переход к стрельбе или финишу."""
        self.loop_counter += 1
        athlete = self.athlete_state
        athlete.reset_loop_distance()

        if self.loop_counter == 1:
            self.state = RaceState.SHOOTING_PRONE
            athlete.start_shooting("prone")
        elif self.loop_counter == 2:
            self.state = RaceState.SHOOTING_STAND
            athlete.start_shooting("stand")
        elif self.loop_counter == 3:
            self.state = RaceState.FINISHED
            self.finished = True
            athlete.finish_race()

    def _update_shooting(self, dt_sim: float):
        """Обработка стрельбы."""
        athlete = self.athlete_state
        finished = athlete.update_shooting(dt_sim)
        if finished:
            # После окончания стрельбы учитываем штрафные круги
            self.penalty_loops_remaining = athlete.misses
            if self.penalty_loops_remaining > 0:
                athlete.reset_loop_distance()  # начнём штрафной круг
                self.state = RaceState.PENALTY_LOOP
            else:
                # Переход к следующему лыжному кругу
                self._advance_to_next_skiing()

    def _update_penalty_loop(self, dt_sim: float):
        """Бег по одному штрафному кругу (150 м)."""
        athlete = self.athlete_state
        loop_len = self.penalty_track.total_length  # должно быть 150 м
        while dt_sim > 0 and self.penalty_loops_remaining > 0:
            # Штрафной круг – равнина, slope=0
            seg, dist_in_seg = self.penalty_track.get_segment(athlete.distance)
            remaining_in_seg = seg.length - dist_in_seg
            base_v = (athlete.athlete.skills["flat"] / 100.0) * 8.0
            athlete.speed = base_v * athlete._fatigue_multiplier()
            if athlete.speed <= 0:
                break
            time_to_seg_end = remaining_in_seg / athlete.speed

            if time_to_seg_end <= dt_sim:
                athlete.distance += remaining_in_seg
                athlete.total_distance += remaining_in_seg
                athlete.time += time_to_seg_end
                athlete.fatigue += FATIGUE_RATE * 1.0 * time_to_seg_end
                dt_sim -= time_to_seg_end

                if athlete.distance >= loop_len:
                    athlete.distance -= loop_len
                    self.penalty_loops_remaining -= 1
                    if self.penalty_loops_remaining == 0:
                        # Все штрафы отбеганы, идём на следующий круг
                        athlete.reset_loop_distance()
                        self._advance_to_next_skiing()
                        break
            else:
                move = athlete.speed * dt_sim
                athlete.distance += move
                athlete.total_distance += move
                athlete.time += dt_sim
                athlete.fatigue += FATIGUE_RATE * 1.0 * dt_sim
                dt_sim = 0

    def _advance_to_next_skiing(self):
        """Переход к следующему лыжному кругу после стрельбы/штрафов."""
        if self.loop_counter == 1:
            self.state = RaceState.SKIING_LOOP_2
        elif self.loop_counter == 2:
            self.state = RaceState.SKIING_LOOP_3
        # после 3-го круга был бы финиш, но _advance вызывается только до финиша

    # -----------------------------------------------------------------
    # Получение данных для отрисовки
    # -----------------------------------------------------------------
    def _get_status(self) -> dict:
        """Текущие данные, нужные визуализации и интерфейсу."""
        if self.athlete_state is None:
            return {"finished": self.finished}

        athlete = self.athlete_state
        # Позиция на трассе (координаты)
        if self.state == RaceState.PENALTY_LOOP:
            x, y = self.penalty_track.get_point_at(athlete.distance)
        else:
            x, y = self.main_track.get_point_at(athlete.distance % self.main_track.total_length)

        return {
            "finished": self.finished,
            "athlete_name": athlete.athlete.name,
            "country": athlete.athlete.country,
            "age": athlete.athlete.age,
            "time": athlete.time,  # симуляционное время гонки, сек
            "distance": athlete.distance,
            "state": self.state.name,
            "position": (x, y),
            "fatigue": athlete.fatigue,
            "speed": athlete.speed,
            "shooting": athlete.shooting_state,
            "shooting_type": athlete.shooting_type,
            "shots_fired": athlete.shots_fired,
            "misses": athlete.misses,
            "penalty_loops_left": self.penalty_loops_remaining,
            "loop": self.loop_counter,
            "total_misses": athlete.total_misses,
            "shot_results": athlete.shot_results,
        }
