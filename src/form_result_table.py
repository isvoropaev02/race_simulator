from tabulate import tabulate
import matplotlib.pyplot as plt
from datetime import datetime


def build_leaderboard_rows(results):
    """Формирует список строк для таблицы: [место, имя, страна, промахи, время]."""
    sorted_res = sorted(results, key=lambda r: r["time"])
    first_time = sorted_res[0]["time"]
    table_rows = []

    for place, r in enumerate(sorted_res, start=1):
        name = r["name"][:20]
        country = r["country"][:8]
        misses = r["misses"]
        t = r["time"]

        if place == 1:
            minutes = int(t // 60)
            seconds = t % 60
            time_str = f"{minutes}:{seconds:05.2f}"
        else:
            diff = t - first_time
            minutes = int(diff // 60)
            seconds = diff % 60
            time_str = f"+{minutes}.{seconds:04.1f}"

        table_rows.append([place, name, country, misses, time_str])

    return table_rows


def print_pretty_results(results):
    """Красивая таблица в консоли."""
    if not results:
        print("Нет результатов.")
        return

    headers = ["Pos", "Name", "Country", "Misses", "Time"]
    rows = build_leaderboard_rows(results)
    print("\n" + tabulate(rows, headers=headers, tablefmt="grid", stralign="center"))


def export_results_png(results):
    """Сохраняет таблицу в PNG через matplotlib."""
    if not results:
        return

    suffix = datetime.now().strftime("%Y_%m_%d_%H_%M")
    filename = "results/results" + suffix + ".png"

    headers = ["Pos", "Name", "Country", "Misses", "Time"]
    rows = build_leaderboard_rows(results)
    all_data = [headers] + rows

    # Максимальная ширина текста в каждом столбце (в символах)
    col_widths_chars = [0] * len(headers)
    for row in all_data:
        for i, cell in enumerate(row):
            col_widths_chars[i] = max(col_widths_chars[i], len(str(cell)))
    # Небольшой отступ
    col_widths_chars = [w + 2 for w in col_widths_chars]

    total_chars = sum(col_widths_chars)
    # Пропорциональные доли для matplotlib
    col_widths_frac = [w / total_chars for w in col_widths_chars]

    # Размер фигуры: ширина пропорциональна общей длине текста,
    # высота – количеству строк
    fig_width = total_chars * 0.12 + 1  # 0.12 дюйма на символ + запас
    fig_height = 0.4 * len(all_data) + 1

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.axis("off")

    table = ax.table(cellText=all_data, cellLoc="center", loc="center", colWidths=col_widths_frac)
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 1.5)  # вертикальный масштаб

    # Стилизация заголовка
    for i in range(len(headers)):
        cell = table[0, i]
        cell.set_facecolor("#40466e")
        cell.set_text_props(color="white", weight="bold")

    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[INFO] Results saved to {filename}.")
