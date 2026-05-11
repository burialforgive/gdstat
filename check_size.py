import sqlite3
import os

conn = sqlite3.connect('data/levels.db')

db_size = os.path.getsize('data/levels.db')
print(f"Размер базы: {db_size / 1024 / 1024:.1f} МБ")

count = conn.execute('SELECT COUNT(*) FROM levels').fetchone()[0]
print(f"Записей: {count:,}\n")

# Текстовые поля
print("=== Текстовые поля ===")
for col in ['name', 'author', 'difficulty', 'length', 'game_version', 
            'song_name', 'song_author', 'song_size', 'description',
            'copied_id', 'collect_at', 'upload_date', 'source']:
    try:
        avg = conn.execute(f'SELECT AVG(LENGTH({col})) FROM levels').fetchone()[0]
        total_mb = (avg or 0) * count / 1024 / 1024
        print(f"{col}: среднее {avg:.1f} символов = ~{total_mb:.1f} МБ")
    except:
        print(f"{col}: нет колонки")

# Числовые поля
print("\n=== Числовые поля (по 4-8 байт каждое) ===")
int_cols = ['id', 'downloads', 'likes', 'stars', 'objects', 'coins',
            'verified_coins', 'featured', 'epic', 'legendary', 'mythic',
            'platformer', 'two_player', 'ldm', 'cp', 'version', 'like_ratio']
print(f"{len(int_cols)} числовых колонок × 4-8 байт × {count:,} записей = ~{len(int_cols) * 6 * count / 1024 / 1024:.1f} МБ")

conn.close()