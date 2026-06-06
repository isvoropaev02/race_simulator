import pygame
from typing import Tuple, Dict, Optional
from src.track import Track

# Цветовая схема (можно настроить под себя)
COLOR_BG = (240, 240, 240)
COLOR_TRACK = (30, 30, 200)
COLOR_PENALTY = (200, 50, 50)
COLOR_ATHLETE = (255, 200, 0)
COLOR_PROFILE_FILL = (180, 210, 180)
COLOR_PROFILE_LINE = (60, 100, 60)
COLOR_PROFILE_DOT = (255, 0, 0)
COLOR_TEXT = (20, 20, 20)
COLOR_PANEL_BG = (220, 220, 230)


class Renderer:
    def __init__(self, screen: pygame.Surface, main_track: Track, penalty_track: Track):
        self.screen = screen
        self.main_track = main_track
        self.penalty_track = penalty_track
        self.font = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 20)

        # Вычисляем области экрана
        self.width, self.height = screen.get_size()
        self.map_rect = pygame.Rect(0, 0, int(self.width * 0.68), int(self.height * 0.72))
        self.info_rect = pygame.Rect(self.map_rect.right + 5, 5, self.width - self.map_rect.right - 10, self.map_rect.height)
        self.profile_rect = pygame.Rect(0, self.map_rect.bottom + 5, self.width, self.height - self.map_rect.bottom - 10)

        # Масштаб для карты
        margin = 30
        map_w, map_h = self.map_rect.size
        self.scale, self.offset_x, self.offset_y = self._compute_scale_offset(self.main_track, map_w, map_h, margin)
        # Штрафной круг тоже будем рисовать в тех же координатах (он в метрах)
        self.penalty_scale, self.penalty_off_x, self.penalty_off_y = self._compute_scale_offset(
            self.penalty_track, map_w, map_h, margin
        )
        # Но для удобства используем общий масштаб, если он подходит (оба в одной системе координат)
        # Предположим, что penalty_track задан в тех же метрах, что и main_track,
        # и его координаты укладываются в те же границы. Тогда берём общий scale,
        # но чтобы penalty точно вписался, пересчитаем общий bounding box.
        # Проще объединить границы обоих треков:
        overall_min_x = min(self.main_track.min_x, self.penalty_track.min_x)
        overall_max_x = max(self.main_track.max_x, self.penalty_track.max_x)
        overall_min_y = min(self.main_track.min_y, self.penalty_track.min_y)
        overall_max_y = max(self.main_track.max_y, self.penalty_track.max_y)
        self.scale, self.offset_x, self.offset_y = self._compute_scale_offset_from_bounds(
            overall_min_x, overall_max_x, overall_min_y, overall_max_y, map_w, map_h, margin
        )

    def _compute_scale_offset(self, track: Track, map_w: int, map_h: int, margin: int):
        return track.get_drawing_scale(map_w, map_h, margin)

    def _compute_scale_offset_from_bounds(self, min_x, max_x, min_y, max_y, map_w, map_h, margin):
        width = max_x - min_x
        height = max_y - min_y
        if width == 0 or height == 0:
            return 1.0, margin, margin
        scale = min((map_w - 2 * margin) / width, (map_h - 2 * margin) / height)
        offset_x = margin + (map_w - 2 * margin - width * scale) / 2 - min_x * scale
        offset_y = margin + (map_h - 2 * margin - height * scale) / 2 - min_y * scale
        return scale, offset_x, offset_y

    def _to_screen(self, x: float, y: float) -> Tuple[int, int]:
        """Преобразование метровых координат в пиксели карты."""
        sx = int(x * self.scale + self.offset_x) + self.map_rect.left
        sy = int(y * self.scale + self.offset_y) + self.map_rect.top
        return sx, sy

    def draw(self, status: Dict, dt_real: float = 0):
        """Главный метод отрисовки. status — словарь от RaceSimulation._get_status()."""
        self.screen.fill(COLOR_BG)
        self._draw_map(status)
        self._draw_profile(status)
        self._draw_info(status)
        # pygame.display.flip() вызывать не будем — это оставим главному циклу main.py

    def _draw_map(self, status: Dict):
        # Заливаем панель карты
        pygame.draw.rect(self.screen, (255, 255, 255), self.map_rect)

        # Рисуем основную трассу
        for seg in self.main_track.segments:
            start = self._to_screen(seg.x1, seg.y1)
            end = self._to_screen(seg.x2, seg.y2)
            pygame.draw.line(self.screen, COLOR_TRACK, start, end, 3)

        # Рисуем штрафной круг
        for seg in self.penalty_track.segments:
            start = self._to_screen(seg.x1, seg.y1)
            end = self._to_screen(seg.x2, seg.y2)
            pygame.draw.line(self.screen, COLOR_PENALTY, start, end, 2)

        # Позиция спортсмена
        pos = status.get("position")
        if pos:
            screen_pos = self._to_screen(pos[0], pos[1])
            pygame.draw.circle(self.screen, COLOR_ATHLETE, screen_pos, 7)

    def _draw_profile(self, status: Dict):
        # Заливаем панель профиля
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, self.profile_rect)
        prof_rect = self.profile_rect.inflate(-10, -10)  # небольшой отступ

        # Получаем профиль основной трассы
        profile = self.main_track.profile
        if not profile:
            return

        # Границы профиля
        max_dist = self.main_track.total_length
        min_alt = min(p[1] for p in profile)
        max_alt = max(p[1] for p in profile)
        if max_alt == min_alt:
            max_alt = min_alt + 1

        # Функция для пересчёта координат профиля в пиксели панели
        def prof_to_screen(d, a):
            x = prof_rect.left + (d / max_dist) * prof_rect.width
            y = prof_rect.bottom - ((a - min_alt) / (max_alt - min_alt)) * prof_rect.height
            return x, y

        # Рисуем заливку под профилем
        points = [prof_to_screen(p[0], p[1]) for p in profile]
        points.append((prof_rect.right, prof_rect.bottom))
        points.append((prof_rect.left, prof_rect.bottom))
        pygame.draw.polygon(self.screen, COLOR_PROFILE_FILL, points)

        # Линия профиля
        if len(points) >= 2:
            pygame.draw.lines(self.screen, COLOR_PROFILE_LINE, False, points[:-2], 2)

        # Текущая позиция на профиле (пройденная дистанция)
        dist = status.get("distance", 0)
        if dist is not None:
            # Получим высоту для текущей дистанции
            alt = self.main_track.get_altitude_at(dist)
            dot_x, dot_y = prof_to_screen(dist, alt)
            pygame.draw.circle(self.screen, COLOR_PROFILE_DOT, (int(dot_x), int(dot_y)), 5)

    def _draw_info(self, status: Dict):
        # Панель информации
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, self.info_rect)

        lines = []
        if status:
            name = status.get("athlete_name", "")
            country = status.get("country", "")
            age = status.get("age", "")
            lines.append(f"{name} ({country})")
            lines.append(f"Age: {age}")
            # Время
            t = status.get("time", 0.0)
            minutes = int(t // 60)
            seconds = t % 60
            lines.append(f"Time: {minutes}:{seconds:05.2f}")
            # Состояние
            lines.append(f"State: {status.get('state', '')}")
            # Стрельба
            shooting = status.get("shooting", False)
            if shooting:
                stype = status.get("shooting_type", "")
                shots = status.get("shots_fired", 0)
                misses = status.get("misses", 0)
                lines.append(f"Shooting: {stype}  {shots}/5  misses:{misses}")
            # Штрафные круги
            penalty = status.get("penalty_loops_left", 0)
            if penalty > 0:
                lines.append(f"Penalty loops left: {penalty}")
            # Скорость
            speed = status.get("speed", 0.0)
            lines.append(f"Speed: {speed:.2f} m/s")
            # Усталость
            fatigue = status.get("fatigue", 0.0)
            lines.append(f"Fatigue: {fatigue:.3f}")

        y = self.info_rect.top + 8
        for line in lines:
            text_surf = self.font.render(line, True, COLOR_TEXT)
            self.screen.blit(text_surf, (self.info_rect.left + 8, y))
            y += 22
