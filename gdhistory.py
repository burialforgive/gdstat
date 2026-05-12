import sqlite3
import requests
import time
import os
from datetime import datetime

DATA_DIR    = "data"
DB_PATH     = f"{DATA_DIR}/levels.db"
CURSOR_FILE = f"{DATA_DIR}/gdhistory_cursor.txt"
BATCH_SIZE  = 1000
DELAY       = 0.5
BASE_URL    = "https://history.geometrydash.eu/api/v1/search/level/advanced/"

DIFFICULTY_MAP = {
    0: 'Unrated', 1: 'Easy', 2: 'Normal', 3: 'Hard', 4: 'Harder',
    5: 'Insane', 6: 'Easy Demon', 7: 'Medium Demon', 8: 'Hard Demon',
    9: 'Insane Demon', 10: 'Extreme Demon', 11: 'Hard Demon',
    12: 'Extreme Demon', -1: 'Auto'
}
LENGTH_MAP = {0: 'Tiny', 1: 'Short', 2: 'Medium', 3: 'Long', 4: 'XL', 5: 'Plat'}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Оптимизации SQLite для скорости
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=10000")
    return conn

def get_db_count(conn):
    return conn.execute("SELECT COUNT(*) FROM levels").fetchone()[0]

def save_level(conn, level):
    conn.execute("""
        INSERT OR REPLACE INTO levels (
            id, name, author, difficulty, downloads, likes, like_ratio,
            stars, objects, featured, epic, legendary, mythic, platformer,
            game_version, length, coins, verified_coins, copied_id,
            two_player, ldm, cp, upload_date
        ) VALUES (
            :id, :name, :author, :difficulty, :downloads, :likes, :like_ratio,
            :stars, :objects, :featured, :epic, :legendary, :mythic, :platformer,
            :game_version, :length, :coins, :verified_coins, :copied_id,
            :two_player, :ldm, :cp, :upload_date
        )
    """, level)

def parse_level(raw):
    try:
        level_id = int(raw.get('online_id', 0))
        if not level_id:
            return None
        downloads  = max(int(raw.get('cache_downloads') or 1), 1)
        likes      = int(raw.get('cache_likes') or 0)
        epic_val   = int(raw.get('cache_epic') or 0)
        diff_val   = int(raw.get('cache_filter_difficulty') or 0)
        length_val = int(raw.get('cache_length') or 0)
        return {
            'id':             level_id,
            'name':           raw.get('cache_level_name', '') or '',
            'author':         raw.get('cache_username', '') or 'Unknown',
            'difficulty':     DIFFICULTY_MAP.get(diff_val, 'Unrated'),
            'downloads':      downloads,
            'likes':          likes,
            'like_ratio':     round(likes / downloads * 100, 2),
            'stars':          int(raw.get('cache_stars') or 0),
            'objects':        int(raw.get('cache_object_count') or 0),
            'featured':       int(raw.get('cache_featured') or 0) > 0,
            'epic':           epic_val == 1,
            'legendary':      epic_val == 2,
            'mythic':         epic_val == 3,
            'platformer':     length_val == 5,
            'game_version':   str(raw.get('cache_game_version') or ''),
            'length':         LENGTH_MAP.get(length_val, 'Unknown'),
            'coins':          0,
            'verified_coins': False,
            'copied_id':      str(raw.get('cache_original') or '0'),
            'two_player':     bool(raw.get('cache_two_player', False)),
            'ldm':            False,
            'cp':             0,
            'upload_date':    None,
        }
    except:
        return None

def fetch_batch(after_id):
    try:
        params = {
            'limit':  BATCH_SIZE,
            'sort':   'online_id:asc',
            'filter': f'online_id > {after_id}'
        }
        r = requests.get(BASE_URL, params=params, timeout=30)
        if r.status_code != 200:
            print(f"  HTTP {r.status_code}")
            return None
        data = r.json()
        if not data.get('hits') and data.get('success') == False:
            print(f"  Ошибка API: {data.get('error')}")
            return None
        return data.get('hits', [])
    except Exception as e:
        print(f"  Ошибка: {e}")
        return None

def load_cursor():
    if os.path.exists(CURSOR_FILE):
        with open(CURSOR_FILE) as f:
            return int(f.read().strip())
    return 0

def save_cursor(last_id):
    with open(CURSOR_FILE, 'w') as f:
        f.write(str(last_id))

def main():
    print("=" * 60)
    print("GDHistory Bulk Importer — пагинация по ID")
    print(f"Батч: {BATCH_SIZE} | Задержка: {DELAY}с")
    print("=" * 60)

    conn = get_db()

    # Не грузим все ID в память — просто считаем количество
    total_in_db = get_db_count(conn)
    print(f"Уже в базе: {total_in_db:,}")

    cursor = load_cursor()
    print(f"Стартуем с ID > {cursor:,}\n")

    total_saved   = 0
    empty_batches = 0
    errors_in_row = 0

    try:
        while True:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ID > {cursor:,}...", end=' ', flush=True)
            batch = fetch_batch(cursor)

            if batch is None:
                errors_in_row += 1
                wait = min(30 * errors_in_row, 300)
                print(f"Ошибка ({errors_in_row}й раз), ждём {wait}с...")
                time.sleep(wait)
                continue

            errors_in_row = 0

            if len(batch) == 0:
                empty_batches += 1
                print("Пустой батч.")
                if empty_batches >= 3:
                    print("Данные закончились.")
                    break
                time.sleep(DELAY)
                continue

            empty_batches  = 0
            saved_in_batch = 0
            last_id        = cursor

            for raw in batch:
                level = parse_level(raw)
                if not level:
                    continue
                last_id = max(last_id, level['id'])
                save_level(conn, level)
                saved_in_batch += 1
                total_saved += 1

            conn.commit()
            cursor = last_id
            save_cursor(cursor)

            print(
                f"получено {len(batch)} (до ID {last_id:,}) | "
                f"сохранено {saved_in_batch} | итого сессия {total_saved:,}"
            )

            time.sleep(DELAY)

    except KeyboardInterrupt:
        conn.commit()
        save_cursor(cursor)
        print("\nОстановлено.")

    print(f"\nВсего в базе: {get_db_count(conn):,}")
    conn.close()

if __name__ == '__main__':
    main()
