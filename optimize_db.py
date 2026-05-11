import sqlite3
import os

conn = sqlite3.connect('data/levels.db')

print("Удаляем колонки...")

conn.execute('''
    CREATE TABLE levels_new AS
    SELECT 
        id, name, author, difficulty, downloads, likes, like_ratio,
        stars, objects, featured, epic, legendary, mythic, platformer,
        game_version, length, coins, verified_coins, copied_id,
        two_player, ldm, cp, upload_date
    FROM levels
''')

print("Новая таблица создана, пересоздаём индексы...")

conn.execute('DROP TABLE levels')
conn.execute('ALTER TABLE levels_new RENAME TO levels')

conn.execute('CREATE INDEX idx_downloads ON levels(downloads)')
conn.execute('CREATE INDEX idx_likes ON levels(likes)')
conn.execute('CREATE INDEX idx_like_ratio ON levels(like_ratio)')
conn.execute('CREATE INDEX idx_author ON levels(author)')
conn.execute('CREATE INDEX idx_name ON levels(name)')
conn.execute('CREATE INDEX idx_difficulty ON levels(difficulty)')

conn.commit()

print("Запускаем VACUUM...")
conn.execute('VACUUM')
conn.commit()
conn.close()

size = os.path.getsize('data/levels.db')
print(f"Готово! Новый размер базы: {size / 1024 / 1024:.1f} МБ")