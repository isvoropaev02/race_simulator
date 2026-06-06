import csv
import math
from typing import List, Tuple


class Segment:
    """Один прямолинейный сегмент трассы."""

    def __init__(self, x1: float, y1: float, x2: float, y2: float, slope: float):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.slope = slope  # уклон в процентах (положит. – подъём)
        dx = x2 - x1
        dy = y2 - y1
        self.length = math.hypot(dx, dy)
        # Угол направления (может пригодиться для стрелочек/отладки)
        self.angle = math.atan2(dy, dx)


class Track:
    """
    Замкнутая трасса, состоящая из линейных сегментов.
    Загружается из CSV (x1,y1,x2,y2,slope).
    """

    def __init__(self, csv_path: str):
        self.segments: List[Segment] = []
        self.total_length: float = 0.0
        self.cumulative_lengths: List[float] = []  # расстояние от старта до начала каждого сегмента
        self.profile: List[Tuple[float, float]] = []  # (дистанция, высота) для рисования профиля
        self._load(csv_path)
        self._compute_profile()
        self._compute_bounds()

    def _load(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                x1, y1, x2, y2, slope = map(float, row)
                seg = Segment(x1, y1, x2, y2, slope)
                self.segments.append(seg)

        # накопленные длины (длина от 0 до начала каждого сегмента)
        cum = 0.0
        self.cumulative_lengths.append(0.0)
        for seg in self.segments:
            cum += seg.length
            self.cumulative_lengths.append(cum)
        self.total_length = cum

    def _compute_profile(self) -> None:
        """Профиль высот: список точек (расстояние от старта, высота)."""
        alt = 0.0
        dist = 0.0
        self.profile.append((0.0, 0.0))
        for seg in self.segments:
            dist += seg.length
            alt += seg.length * seg.slope / 100.0
            self.profile.append((dist, alt))

    def _compute_bounds(self) -> None:
        """Границы координат всех точек (для автоматического масштабирования)."""
        xs, ys = [], []
        for seg in self.segments:
            xs.extend([seg.x1, seg.x2])
            ys.extend([seg.y1, seg.y2])
        self.min_x = min(xs)
        self.max_x = max(xs)
        self.min_y = min(ys)
        self.max_y = max(ys)

    # --------------------------------------------------------------
    # Основные методы для симуляции
    # --------------------------------------------------------------
    def get_segment(self, distance: float) -> Tuple[Segment, float]:
        """
        Для пройденного расстояния distance (0..total_length) возвращает
        текущий сегмент и оставшееся расстояние от его начала (м).
        """
        distance = distance % self.total_length
        # Ищем сегмент, содержащий заданную дистанцию
        for i, seg in enumerate(self.segments):
            if self.cumulative_lengths[i + 1] > distance:
                dist_in_seg = distance - self.cumulative_lengths[i]
                return seg, dist_in_seg
        # крайний случай: distance == total_length
        seg = self.segments[-1]
        return seg, seg.length

    def get_slope_at(self, distance: float) -> float:
        seg, _ = self.get_segment(distance)
        return seg.slope

    def get_point_at(self, distance: float) -> Tuple[float, float]:
        """Координаты (x, y) на трассе для заданного расстояния."""
        seg, dist_in_seg = self.get_segment(distance)
        t = dist_in_seg / seg.length if seg.length > 0 else 0.0
        x = seg.x1 + (seg.x2 - seg.x1) * t
        y = seg.y1 + (seg.y2 - seg.y1) * t
        return x, y

    def get_altitude_at(self, distance: float) -> float:
        """Высота (по профилю) для заданного расстояния."""
        distance = distance % self.total_length
        for i in range(len(self.profile) - 1):
            d1, a1 = self.profile[i]
            d2, a2 = self.profile[i + 1]
            if d1 <= distance <= d2:
                if d2 == d1:
                    return a1
                t = (distance - d1) / (d2 - d1)
                return a1 + (a2 - a1) * t
        return self.profile[-1][1]

    # --------------------------------------------------------------
    # Для отрисовки
    # --------------------------------------------------------------
    def get_drawing_scale(self, screen_width: float, screen_height: float, margin: float = 20.0) -> Tuple[float, float, float]:
        """
        Возвращает scale, offset_x, offset_y, чтобы трасса целиком вписалась
        в прямоугольник screen_width x screen_height с отступом margin.
        """
        width = self.max_x - self.min_x
        height = self.max_y - self.min_y
        scale_x = (screen_width - 2 * margin) / width if width > 0 else 1.0
        scale_y = (screen_height - 2 * margin) / height if height > 0 else 1.0
        scale = min(scale_x, scale_y)
        offset_x = margin + (screen_width - 2 * margin - width * scale) / 2 - self.min_x * scale
        offset_y = margin + (screen_height - 2 * margin - height * scale) / 2 - self.min_y * scale
        return scale, offset_x, offset_y
