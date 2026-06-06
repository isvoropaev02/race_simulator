import pygame
from typing import Tuple, Dict, Optional
from src.track import Track

COLOR_BG = (240, 240, 240)
COLOR_TRACK = (30, 30, 200)
COLOR_PENALTY = (200, 50, 50)
COLOR_ATHLETE = (255, 200, 0)
COLOR_PROFILE_FILL = (180, 210, 180)
COLOR_PROFILE_LINE = (60, 100, 60)
COLOR_PROFILE_DOT = (255, 0, 0)
COLOR_TEXT = (20, 20, 20)
COLOR_PANEL_BG = (220, 220, 230)
COLOR_TARGET_HIT = (255, 255, 255)
COLOR_TARGET_MISS = (30, 30, 30)
COLOR_TARGET_PENDING = (100, 100, 100)


class Renderer:
    def __init__(self, screen: pygame.Surface, main_track: Track, penalty_track: Track):
        self.screen = screen
        self.main_track = main_track
        self.penalty_track = penalty_track
        self.font = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 20)
        self.results = []  # <-- НОВОЕ

        # Вычисляем области экрана
        self.width, self.height = screen.get_size()
        # Карта (слева)
        self.map_rect = pygame.Rect(0, 0, int(self.width * 0.68), int(self.height * 0.72))

        # Правая панель делим на три вертикальных блока
        info_width = self.width - self.map_rect.right - 10
        info_height = 200  # <-- Верхний блок с данными
        shooting_height = 80  # <-- Блок с мишенями (только при стрельбе)
        self.info_rect = pygame.Rect(self.map_rect.right + 5, 5, info_width, info_height)
        self.shooting_rect = pygame.Rect(self.map_rect.right + 5, self.info_rect.bottom + 5, info_width, shooting_height)
        self.profile_rect = pygame.Rect(0, self.map_rect.bottom + 5, self.width, self.height - self.map_rect.bottom - 10)
        leaderboard_top = self.shooting_rect.bottom + 5
        leaderboard_bottom = min(self.map_rect.bottom - 5, self.height)
        if leaderboard_bottom > leaderboard_top:
            self.leaderboard_rect = pygame.Rect(
                self.map_rect.right + 5, leaderboard_top, info_width, leaderboard_bottom - leaderboard_top
            )
        else:
            self.leaderboard_rect = pygame.Rect(0, 0, 0, 0)  # нет места – не показываем

        # Масштаб карты (объединённый бокс трасс)
        margin = 30
        map_w, map_h = self.map_rect.size
        overall_min_x = min(self.main_track.min_x, self.penalty_track.min_x)
        overall_max_x = max(self.main_track.max_x, self.penalty_track.max_x)
        overall_min_y = min(self.main_track.min_y, self.penalty_track.min_y)
        overall_max_y = max(self.main_track.max_y, self.penalty_track.max_y)
        self.scale, self.offset_x, self.offset_y = self._compute_scale_offset_from_bounds(
            overall_min_x, overall_max_x, overall_min_y, overall_max_y, map_w, map_h, margin
        )

    def set_results(self, results: list) -> None:  # <-- НОВОЕ
        self.results = results

    # Вспомогательные методы вычисления масштаба (без изменений)
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
        sx = int(x * self.scale + self.offset_x) + self.map_rect.left
        sy = int(y * self.scale + self.offset_y) + self.map_rect.top
        return sx, sy

    # ================================================================
    # Главный метод отрисовки
    # ================================================================
    def draw(self, status: Dict, dt_real: float = 0):
        self.screen.fill(COLOR_BG)
        self._draw_map(status)
        self._draw_profile(status)
        self._draw_info(status)
        self._draw_shooting(status)  # <-- НОВОЕ
        self._draw_leaderboard()  # <-- НОВОЕ

    # ================================================================
    # Карта (без изменений)
    # ================================================================
    def _draw_map(self, status: Dict):
        pygame.draw.rect(self.screen, (255, 255, 255), self.map_rect)

        for seg in self.main_track.segments:
            start = self._to_screen(seg.x1, seg.y1)
            end = self._to_screen(seg.x2, seg.y2)
            pygame.draw.line(self.screen, COLOR_TRACK, start, end, 3)

        for seg in self.penalty_track.segments:
            start = self._to_screen(seg.x1, seg.y1)
            end = self._to_screen(seg.x2, seg.y2)
            pygame.draw.line(self.screen, COLOR_PENALTY, start, end, 2)

        pos = status.get("position")
        if pos:
            screen_pos = self._to_screen(pos[0], pos[1])
            pygame.draw.circle(self.screen, COLOR_ATHLETE, screen_pos, 7)

    # ================================================================
    # Профиль (без изменений)
    # ================================================================
    def _draw_profile(self, status: Dict):
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, self.profile_rect)
        prof_rect = self.profile_rect.inflate(-10, -10)
        profile = self.main_track.profile
        if not profile:
            return

        max_dist = self.main_track.total_length
        min_alt = min(p[1] for p in profile)
        max_alt = max(p[1] for p in profile)
        if max_alt == min_alt:
            max_alt = min_alt + 1

        def prof_to_screen(d, a):
            x = prof_rect.left + (d / max_dist) * prof_rect.width
            y = prof_rect.bottom - ((a - min_alt) / (max_alt - min_alt)) * prof_rect.height
            return x, y

        points = [prof_to_screen(p[0], p[1]) for p in profile]
        points.append((prof_rect.right, prof_rect.bottom))
        points.append((prof_rect.left, prof_rect.bottom))
        pygame.draw.polygon(self.screen, COLOR_PROFILE_FILL, points)
        if len(points) >= 2:
            pygame.draw.lines(self.screen, COLOR_PROFILE_LINE, False, points[:-2], 2)

        dist = status.get("distance", 0)
        if dist is not None:
            alt = self.main_track.get_altitude_at(dist)
            dot_x, dot_y = prof_to_screen(dist, alt)
            pygame.draw.circle(self.screen, COLOR_PROFILE_DOT, (int(dot_x), int(dot_y)), 5)

    # ================================================================
    # Информация о спортсмене (верхний блок) – убрана детализация стрельбы
    # ================================================================
    def _draw_info(self, status: Dict):
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, self.info_rect)

        lines = []
        if status:
            name = status.get("athlete_name", "")
            country = status.get("country", "")
            age = status.get("age", "")
            lines.append(f"{name} ({country})")

            t = status.get("time", 0.0)
            minutes = int(t // 60)
            seconds = t % 60
            lines.append(f"Time: {minutes}:{seconds:05.2f}")
            lines.append(f"State: {status.get('state', '')}")

            # Стрельбу отсюда убрали, теперь только краткая сводка (опционально)
            shooting = status.get("shooting", False)
            if shooting:
                lines.append("Shooting...")
            # Штрафные круги
            penalty = status.get("penalty_loops_left", 0)
            if penalty > 0:
                lines.append(f"Penalty loops left: {penalty}")
            # Скорость и усталость
            speed = status.get("speed", 0.0)
            lines.append(f"Speed: {speed:.2f} m/s")
            fatigue = status.get("fatigue", 0.0)
            lines.append(f"Fatigue: {fatigue:.3f}")

        y = self.info_rect.top + 8
        for line in lines:
            text_surf = self.font.render(line, True, COLOR_TEXT)
            self.screen.blit(text_surf, (self.info_rect.left + 8, y))
            y += 22

    # ================================================================
    # Мишени (новый метод)
    # ================================================================
    def _draw_shooting(self, status: Dict):
        shooting = status.get("shooting", False)
        if not shooting:
            return  # не рисуем, если не стреляет

        pygame.draw.rect(self.screen, COLOR_PANEL_BG, self.shooting_rect)

        shot_results = status.get("shot_results", [])
        shots_fired = status.get("shots_fired", 0)

        # Параметры кружков
        radius = 12
        spacing = 28
        total_w = 5 * (2 * radius) + 4 * spacing
        start_x = self.shooting_rect.left + (self.shooting_rect.width - total_w) // 2 + radius
        y = self.shooting_rect.centery

        for i in range(5):
            x = start_x + i * (2 * radius + spacing)
            if i < shots_fired:
                # Есть результат
                if shot_results[i]:
                    color = COLOR_TARGET_HIT
                else:
                    color = COLOR_TARGET_MISS
            else:
                color = COLOR_TARGET_PENDING

            pygame.draw.circle(self.screen, color, (int(x), y), radius)
            pygame.draw.circle(self.screen, (0, 0, 0), (int(x), y), radius, 1)  # обводка

    # ================================================================
    # Таблица лидеров (новый метод)
    # ================================================================
    def _draw_leaderboard(self):
        if self.leaderboard_rect.height <= 0:
            return
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, self.leaderboard_rect)
        title = self.font_small.render("Leaderboard", True, COLOR_TEXT)
        self.screen.blit(title, (self.leaderboard_rect.left + 8, self.leaderboard_rect.top + 5))

        if not self.results:
            return

        # Сортировка по времени
        sorted_results = sorted(self.results, key=lambda r: r["time"])
        y = self.leaderboard_rect.top + 28
        for place, r in enumerate(sorted_results, start=1):
            minutes = int(r["time"] // 60)
            seconds = r["time"] % 60
            line = f"{place}. {r['name']} ({r['country']})  misses:{r['misses']}  {minutes}:{seconds:05.2f}"
            text = self.font_small.render(line, True, COLOR_TEXT)
            self.screen.blit(text, (self.leaderboard_rect.left + 8, y))
            y += 20
            if y > self.leaderboard_rect.bottom - 10:
                break
