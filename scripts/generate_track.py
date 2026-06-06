import math
import csv


def generate_main_track():
    # Координаты ключевых точек в метрах (примерный контур "овал с ручкой")
    points = [
        (0, 0),  # старт
        (300, -100),  # поворот направо
        (500, 200),  # дальняя точка
        (300, 500),  # левый поворот
        (-200, 600),  # заход на стадион
        (-400, 300),  # изгиб
        (-350, 50),  # подход к стрельбищу
        (0, 0),  # возврат к старту (замкнули)
    ]

    # Назначение уклонов для каждого сегмента (индекс соответствует сегменту между i и i+1)
    # Подбираем реалистичный рельеф: подъёмы (+) около 8-10%, спуски (-) до 12%
    slopes = [8.5, -5.0, 3.0, 9.0, -11.0, -4.0, 0.0]  # семь сегментов (по числу рёбер)

    segments = []
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)
        segments.append((x1, y1, x2, y2, slopes[i], length))

    # Корректировка общей длины до 4000 м (масштабируем координаты)
    total_length = sum(seg[5] for seg in segments)
    target_length = 4000.0
    scale = target_length / total_length

    scaled_segments = []
    for x1, y1, x2, y2, slope, _ in segments:
        scaled_segments.append((x1 * scale, y1 * scale, x2 * scale, y2 * scale, slope))

    # Запись в CSV
    with open("db/track.csv", "w", newline="") as f:
        writer = csv.writer(f)
        for seg in scaled_segments:
            writer.writerow(seg)

    # Профиль высот
    distance = 0.0
    altitude = 0.0
    profile = [(0.0, altitude)]  # пары (дистанция, высота)
    for x1, y1, x2, y2, slope in scaled_segments:
        dx = x2 - x1
        dy = y2 - y1
        seg_length = math.hypot(dx, dy)
        distance += seg_length
        altitude += seg_length * slope / 100.0
        profile.append((distance, altitude))

    # Сохраним профиль в файл (опционально, для отладки)
    with open("db/track_profile.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["distance_m", "altitude_m"])
        writer.writerows(profile)

    return scaled_segments, profile


import math
import csv


def generate_penalty_loop():
    points = [(0, 0), (50, 0), (50, 50), (0, 0)]  # замкнули
    slopes = [0.0, 0.0, 0.0]  # равнина

    segments = []
    total_length = 0.0
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        dx = x2 - x1
        dy = y2 - y1
        seg_len = math.hypot(dx, dy)
        segments.append((x1, y1, x2, y2, slopes[i], seg_len))
        total_length += seg_len

    # Масштабируем, чтобы общая длина стала ровно 150 м
    target_length = 150.0
    scale = target_length / total_length

    scaled_segments = []
    for x1, y1, x2, y2, slope, _ in segments:
        scaled_segments.append((x1 * scale, y1 * scale, x2 * scale, y2 * scale, slope))

    # Проверка итоговой длины
    check_length = sum(math.hypot(s[2] - s[0], s[3] - s[1]) for s in scaled_segments)

    with open("db/penalty_loop.csv", "w", newline="") as f:
        writer = csv.writer(f)
        for seg in scaled_segments:
            writer.writerow(seg)


if __name__ == "__main__":
    generate_main_track()
    generate_penalty_loop()
