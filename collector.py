import requests
import json
import time
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Все категории которые будем собирать
SEARCH_CATEGORIES = [
    # (тип, сложность, название)
    ("4", "10", "demons_extreme"),    # экстремальные демоны
    ("4", "9",  "demons_insane"),     # insane демоны
    ("4", "8",  "demons_hard"),       # hard демоны
    ("4", "7",  "demons_medium"),     # medium демоны
    ("4", "6",  "demons_easy"),       # easy демоны
    ("1", "",   "most_downloaded"),   # самые скачиваемые
    ("2", "",   "most_liked"),        # самые лайкнутые
    ("3", "",   "trending"),          # трендовые
    ("5", "",   "recent"),            # новые рейтинговые
    ("6", "",   "featured"),          # featured
    ("16","",   "hall_of_fame"),      # hall of fame
    ("17","",   "gdworld"),           # GD World
]

def fetch_page(category_type, difficulty, category_name, page):
    """Загружает одну страницу одной категории"""
    try:
        url = f"https://gdbrowser.com/api/search/*?type={category_type}&page={page}"
        if difficulty:
            url += f"&diff={difficulty}"
        
        response = requests.get(url, timeout=15)
        
        if response.text == "-1" or not response.text:
            return []
        
        levels = response.json()
        
        # Добавляем метаданные к каждому уровню
        timestamp = datetime.now().isoformat()
        for level in levels:
            downloads = max(level.get('downloads', 1), 1)
            likes = level.get('likes', 0)
            level['like_ratio'] = round(likes / downloads * 100, 2)
            level['collected_at'] = timestamp
            level['category'] = category_name
        
        return levels
    except Exception as e:
        return []

def collect_all():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Начинаем сбор...")
    
    all_levels = {}  # словарь по ID чтобы не было дублей
    tasks = []
    
    # Формируем список всех задач
    # Для каждой категории берём 10 страниц = 100 уровней
    PAGES_PER_CATEGORY = 10
    for cat_type, diff, cat_name in SEARCH_CATEGORIES:
        for page in range(PAGES_PER_CATEGORY):
            tasks.append((cat_type, diff, cat_name, page))
    
    total_tasks = len(tasks)
    completed = 0
    
    # Параллельные запросы — 5 одновременно
    # Больше не надо чтобы не перегружать сервер
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(fetch_page, t[0], t[1], t[2], t[3]): t 
            for t in tasks
        }
        
        for future in as_completed(futures):
            levels = future.result()
            for level in levels:
                level_id = level.get('id')
                if level_id:
                    all_levels[level_id] = level
            
            completed += 1
            if completed % 10 == 0:
                print(f"  Прогресс: {completed}/{total_tasks} запросов, {len(all_levels)} уникальных уровней")
            
            # Маленькая пауза между запросами
            time.sleep(0.2)
    
    levels_list = list(all_levels.values())
    
    # Сохраняем снапшот с временной меткой
    filename = os.path.join(
        DATA_DIR, 
        f"levels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(levels_list, f, ensure_ascii=False, indent=2)
    
    # Обновляем последний снапшот для сайта
    latest = os.path.join(DATA_DIR, "levels_latest.json")
    with open(latest, 'w', encoding='utf-8') as f:
        json.dump(levels_list, f, ensure_ascii=False, indent=2)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Готово: {len(levels_list)} уникальных уровней")
    
    # Быстрая статистика
    mythic = len([l for l in levels_list if l.get('mythic')])
    legendary = len([l for l in levels_list if l.get('legendary')])
    epic = len([l for l in levels_list if l.get('epic')])
    platformers = len([l for l in levels_list if l.get('platformer')])
    
    print(f"  Mythic: {mythic} | Legendary: {legendary} | Epic: {epic}")
    print(f"  Платформеры: {platformers} | Классика: {len(levels_list) - platformers}")
    
    return levels_list

def collect_players(usernames):
    """Собирает данные игроков параллельно"""
    def fetch_player(username):
        try:
            r = requests.get(
                f"https://gdbrowser.com/api/profile/{username}", 
                timeout=10
            )
            if r.status_code != 200:
                return None
            data = r.json()
            data['collected_at'] = datetime.now().isoformat()
            return data
        except:
            return None
    
    players = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(fetch_player, u): u for u in usernames}
        for future in as_completed(futures):
            result = future.result()
            if result:
                players.append(result)
                print(f"  Игрок: {result.get('username')}")
    
    if players:
        latest = os.path.join(DATA_DIR, "players_latest.json")
        with open(latest, 'w', encoding='utf-8') as f:
            json.dump(players, f, ensure_ascii=False, indent=2)

TRACKED_PLAYERS = [
    "Serponge", "Sunix", "Exen", "Npesta", "Zoink",
    "Wulzy", "Dorami", "Trick", "Chloe", "wokecat"
]

# Интервал между полными сборами
INTERVAL_MINUTES = 15

print("=" * 50)
print("GD Stats Collector")
print(f"Категорий: {len(SEARCH_CATEGORIES)}")
print(f"Страниц на категорию: 10")
print(f"Максимум уровней за цикл: ~{len(SEARCH_CATEGORIES) * 10 * 10} (с учётом дублей меньше)")
print(f"Интервал: {INTERVAL_MINUTES} минут")
print("=" * 50)

# Первый сбор сразу
collect_all()
collect_players(TRACKED_PLAYERS)

while True:
    print(f"\nСледующий сбор через {INTERVAL_MINUTES} минут...")
    time.sleep(INTERVAL_MINUTES * 60)
    collect_all()
    collect_players(TRACKED_PLAYERS)