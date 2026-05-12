import sqlite3
import os

SRC = "data/levels.db"
DST = "data/site.db"
TOP = 1000  # сколько брать из каждой категории

def build():
    print("Строим site.db...")

    if os.path.exists(DST):
        os.remove(DST)
        print("Старый site.db удалён")

    src = sqlite3.connect(SRC)
    src.row_factory = sqlite3.Row
    dst = sqlite3.connect(DST)

    # Создаём таблицу
    dst.execute("""
        CREATE TABLE levels (
            id INTEGER PRIMARY KEY,
            name TEXT, author TEXT, difficulty TEXT,
            downloads INTEGER DEFAULT 0, likes INTEGER DEFAULT 0,
            like_ratio REAL DEFAULT 0, stars INTEGER DEFAULT 0,
            objects INTEGER DEFAULT 0, featured INTEGER DEFAULT 0,
            epic INTEGER DEFAULT 0, legendary INTEGER DEFAULT 0,
            mythic INTEGER DEFAULT 0, platformer INTEGER DEFAULT 0,
            game_version TEXT, length TEXT, coins INTEGER DEFAULT 0,
            verified_coins INTEGER DEFAULT 0, copied_id TEXT,
            two_player INTEGER DEFAULT 0, ldm INTEGER DEFAULT 0,
            cp INTEGER DEFAULT 0, upload_date TEXT
        )
    """)

    def insert_batch(rows):
        dst.executemany("""
            INSERT OR IGNORE INTO levels VALUES (
                :id,:name,:author,:difficulty,:downloads,:likes,:like_ratio,
                :stars,:objects,:featured,:epic,:legendary,:mythic,:platformer,
                :game_version,:length,:coins,:verified_coins,:copied_id,
                :two_player,:ldm,:cp,:upload_date
            )
        """, [dict(r) for r in rows])

    # Топ по загрузкам — первые и последние 1000
    print("  Топ по загрузкам...")
    insert_batch(src.execute(f"SELECT * FROM levels ORDER BY downloads DESC LIMIT {TOP}").fetchall())
    insert_batch(src.execute(f"SELECT * FROM levels ORDER BY downloads ASC LIMIT {TOP}").fetchall())

    # Топ по лайкам — первые и последние 1000
    print("  Топ по лайкам...")
    insert_batch(src.execute(f"SELECT * FROM levels ORDER BY likes DESC LIMIT {TOP}").fetchall())
    insert_batch(src.execute(f"SELECT * FROM levels ORDER BY likes ASC LIMIT {TOP}").fetchall())

    # Топ по % лайков (минимум 5000 загрузок) — первые и последние 1000
    print("  Топ по % лайков...")
    insert_batch(src.execute(f"SELECT * FROM levels WHERE downloads >= 5000 ORDER BY like_ratio DESC LIMIT {TOP}").fetchall())
    insert_batch(src.execute(f"SELECT * FROM levels WHERE downloads >= 5000 ORDER BY like_ratio ASC LIMIT {TOP}").fetchall())

    dst.commit()

    # Индексы
    print("  Создаём индексы...")
    dst.execute("CREATE INDEX idx_downloads  ON levels(downloads)")
    dst.execute("CREATE INDEX idx_likes      ON levels(likes)")
    dst.execute("CREATE INDEX idx_like_ratio ON levels(like_ratio)")
    dst.execute("CREATE INDEX idx_stars      ON levels(stars)")
    dst.commit()

    # Статистика
    count = dst.execute("SELECT COUNT(*) FROM levels").fetchone()[0]
    src.close()
    dst.close()

    size = os.path.getsize(DST) / 1024 / 1024
    print(f"\nГотово!")
    print(f"  Уровней в site.db: {count:,}")
    print(f"  Размер: {size:.1f} МБ")

if __name__ == '__main__':
    build()