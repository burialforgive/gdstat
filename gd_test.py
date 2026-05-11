import requests
import json
from datetime import datetime

def get_levels(page=0):
    response = requests.get(
        f"https://gdbrowser.com/api/search/*?diff=10&type=4&page={page}"
    )
    if response.text == "-1":
        print("Ошибка запроса")
        return []
    return response.json()

def save_snapshot():
    print("Собираем данные...")
    all_levels = []

    for page in range(3):
        print(f"Страница {page + 1}...")
        levels = get_levels(page)
        all_levels.extend(levels)

    timestamp = datetime.now().isoformat()
    for level in all_levels:
        level['collected_at'] = timestamp

    filename = f"levels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_levels, f, ensure_ascii=False, indent=2)

    print(f"\nСохранено {len(all_levels)} уровней в файл: {filename}")

    for level in all_levels:
        downloads = level.get('downloads', 1)
        likes = level.get('likes', 0)
        level['like_ratio'] = round(likes / downloads * 100, 2)

    print("\n--- Быстрая аналитика ---")

    top = sorted(all_levels, key=lambda x: x['like_ratio'], reverse=True)[:5]
    print("\nТоп 5 уровней по соотношению лайков к загрузкам:")
    for i, lvl in enumerate(top, 1):
        print(f"{i}. {lvl['name']} by {lvl['author']} — {lvl['like_ratio']}% лайков")

    print("\nНедооценённые уровни (много загрузок, мало лайков):")
    underrated = [l for l in all_levels if l['downloads'] > 50000]
    underrated = sorted(underrated, key=lambda x: x['like_ratio'])[:5]
    for i, lvl in enumerate(underrated, 1):
        print(f"{i}. {lvl['name']} by {lvl['author']} — {lvl['downloads']} загрузок, {lvl['like_ratio']}% лайков")

    platformers = len([l for l in all_levels if l.get('platformer')])
    classic = len(all_levels) - platformers
    print(f"\nПлатформеры: {platformers} | Классика: {classic}")

save_snapshot()