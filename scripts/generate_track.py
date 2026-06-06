import math
import csv


def generate_main_track():
    # Координаты ключевых точек в метрах (примерный контур "овал с ручкой")
    # points = [
    #     (0, 0),
    #     (300, -100),
    #     (500, 200),
    #     (300, 500),
    #     (350, 650),
    #     (-200, 600),
    #     (-400, 300),
    #     (-350, 50),
    #     (0, 0),
    # ]
    # slopes = [8.5, -5.0, 3.0, -1.0, 9.0, -11.0, -4.0, 0.0]
    points = [
        (0, 0),
        (10, 80),
        (50, 112),
        (114, 42),
        (180, 48),
        (208, 92),
        (169, 173),
        (73, 197),
        (-160, 195),
        (-165, 163),
        (-96, 150),
        (-111, 128),
        (-262, 132),
        (-293, 103),
        (-269, 74),
        (-140, 80),
        (-121, 45),
        (-115, -37),
        (-5, -33),
        (0, 0),
    ]
    altitudes = [100, 120, 150, 130, 90, 110, 250, 230, 380, 400, 230, 150, 170, 220, 200, 210, 180, 110, 105, 100]

    assert len(points) == len(altitudes), "Число точек и высот должно совпадать"

    segments = []
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)
        # Автоматический расчёт уклона (%)
        delta_h = altitudes[i + 1] - altitudes[i]
        slope = 100.0 * delta_h / length if length > 0 else 0.0
        segments.append((x1, y1, x2, y2, slope, length))

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
    altitude = altitudes[0]  # начинаем с высоты первой точки
    profile = [(0.0, altitude)]
    for i, (x1, y1, x2, y2, slope) in enumerate(scaled_segments):
        dx = x2 - x1
        dy = y2 - y1
        seg_length = math.hypot(dx, dy)
        distance += seg_length
        altitude += seg_length * slope / 100.0  # равно altitudes[i+1] после масштабирования?
        # из-за масштаба координат и неизменных уклонов высота изменится пропорционально
        profile.append((distance, altitude))

    with open("db/track_profile.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["distance_m", "altitude_m"])
        writer.writerows(profile)

    return scaled_segments, profile


def generate_penalty_loop():
    # points = [(0, 0), (40, 25), (50, 50), (40, 60), (0, 75), (-20, 40), (0, 0)]  # замкнули
    points = [(0, 0), (-16, 36), (-42, 52), (-80, 50), (-110, 32), (-94, 5), (-64, -18), (-26, -12), (0, 0)]
    slopes = [0.0] * (len(points) - 1)  # равнина

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
