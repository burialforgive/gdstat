import json
import os
import sqlite3

DATA_DIR = "data"
SOURCE_FILE = os.path.join(DATA_DIR, "all_levels.json")
DB_FILE = os.path.join(DATA_DIR, "levels.db")

print("Читаем JSON... (подождите)")
with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
    levels = json.load(f)
print(f"Загружено: {len(levels):,} уровней")

# Создаём базу данных
print("Создаём базу данных...")
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Создаём таблицу
c.execute('''
    CREATE TABLE IF NOT EXISTS levels (
        id INTEGER PRIMARY KEY,
        name TEXT,
        author TEXT,
        difficulty TEXT,
        downloads INTEGER DEFAULT 0,
        likes INTEGER DEFAULT 0,
        like_ratio REAL DEFAULT 0,
        stars INTEGER DEFAULT 0,
        objects INTEGER DEFAULT 0,
        featured INTEGER DEFAULT 0,
        epic INTEGER DEFAULT 0,
        legendary INTEGER DEFAULT 0,
        mythic INTEGER DEFAULT 0,
        platformer INTEGER DEFAULT 0,
        game_version TEXT,
        song_name TEXT,
        song_author TEXT,
        length TEXT,
        coins INTEGER DEFAULT 0,
        verified_coins INTEGER DEFAULT 0,
        cp INTEGER DEFAULT 0,
        two_player INTEGER DEFAULT 0,
        ldm INTEGER DEFAULT 0,
        copied_id TEXT,
        description TEXT,
        source TEXT,
        collected_at TEXT
    )
''')

# Создаём индексы для быстрого поиска
c.execute('CREATE INDEX IF NOT EXISTS idx_downloads ON levels(downloads)')
c.execute('CREATE INDEX IF NOT EXISTS idx_likes ON levels(likes)')
c.execute('CREATE INDEX IF NOT EXISTS idx_like_ratio ON levels(like_ratio)')
c.execute('CREATE INDEX IF NOT EXISTS idx_author ON levels(author)')
c.execute('CREATE INDEX IF NOT EXISTS idx_name ON levels(name)')
c.execute('CREATE INDEX IF NOT EXISTS idx_difficulty ON levels(difficulty)')

print("Заполняем базу данных...")

batch = []
for i, lvl in enumerate(levels):
    if not isinstance(lvl, dict):
        continue
    
    batch.append((
        lvl.get('id'),
        lvl.get('name', ''),
        lvl.get('author', ''),
        lvl.get('difficulty', ''),
        lvl.get('downloads', 0),
        lvl.get('likes', 0),
        lvl.get('like_ratio', 0),
        lvl.get('stars', 0),
        lvl.get('objects', 0),
        1 if lvl.get('featured') else 0,
        1 if lvl.get('epic') else 0,
        1 if lvl.get('legendary') else 0,
        1 if lvl.get('mythic') else 0,
        1 if lvl.get('platformer') else 0,
        str(lvl.get('gameVersion', '')),
        lvl.get('songName', ''),
        lvl.get('songAuthor', ''),
        lvl.get('length', ''),
        lvl.get('coins', 0),
        1 if lvl.get('verifiedCoins') else 0,
        lvl.get('cp', 0),
        1 if lvl.get('twoPlayer') else 0,
        1 if lvl.get('ldm') else 0,
        str(lvl.get('copiedID', '0')),
        lvl.get('description', ''),
        lvl.get('source', ''),
        lvl.get('collected_at', '')
    ))
    
    # Вставляем пачками по 10000
    if len(batch) >= 10000:
        c.executemany('''
            INSERT OR REPLACE INTO levels VALUES (
                ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
            )
        ''', batch)
        conn.commit()
        batch = []
        print(f"  Записано: {i+1:,} / {len(levels):,}")

# Последняя пачка
if batch:
    c.executemany('''
        INSERT OR REPLACE INTO levels VALUES (
            ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
        )
    ''', batch)
    conn.commit()

# Проверяем
count = c.execute('SELECT COUNT(*) FROM levels').fetchone()[0]
print(f"\nГотово! В базе: {count:,} уровней")
print(f"Размер БД: {os.path.getsize(DB_FILE) / 1024 / 1024:.1f} МБ")

conn.close()