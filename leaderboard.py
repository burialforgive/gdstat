import sqlite3
import time
import os
from datetime import datetime
from robtop import fetch_leaderboard

DATA_DIR = "data"
DB_PATH  = f"{DATA_DIR}/levels.db"

# Снапшот раз в 24 часа
INTERVAL_HOURS = 24

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_tables(conn):
    # Таблица игроков
    conn.execute("""
        CREATE TABLE IF NOT EXISTS players (
            account_id  TEXT PRIMARY KEY,
            username    TEXT,
            player_id   TEXT,
            moderator   INTEGER DEFAULT 0,
            first_seen  TEXT,
            last_seen   TEXT
        )
    """)
    # Таблица снапшотов (история)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS player_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id  TEXT,
            date        TEXT,
            rank        INTEGER,
            stars       INTEGER,
            demons      INTEGER,
            coins       INTEGER,
            user_coins  INTEGER,
            diamonds    INTEGER,
            moons       INTEGER,
            cp          INTEGER,
            UNIQUE(account_id, date)
        )
    """)
    conn.commit()

def save_snapshot(conn, players):
    date = datetime.now().strftime('%Y-%m-%d')
    now  = datetime.now().isoformat()
    new_players = 0
    new_snaps   = 0

    for p in players:
        aid = p['accountID']
        if not aid:
            continue

        # Upsert игрока
        existing = conn.execute(
            'SELECT account_id FROM players WHERE account_id=?', (aid,)
        ).fetchone()

        if existing:
            conn.execute("""
                UPDATE players SET username=?, last_seen=?, moderator=?
                WHERE account_id=?
            """, (p['username'], now, p['moderator'], aid))
        else:
            conn.execute("""
                INSERT INTO players (account_id, username, player_id, moderator, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (aid, p['username'], p['playerID'], p['moderator'], now, now))
            new_players += 1

        # Снапшот (один в день)
        try:
            conn.execute("""
                INSERT INTO player_history
                    (account_id, date, rank, stars, demons, coins, user_coins, diamonds, moons, cp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (aid, date, p['rank'], p['stars'], p['demons'],
                  p['coins'], p['userCoins'], p['diamonds'], p['moons'], p['cp']))
            new_snaps += 1
        except sqlite3.IntegrityError:
            # Снапшот за этот день уже есть — обновляем
            conn.execute("""
                UPDATE player_history
                SET rank=?, stars=?, demons=?, coins=?, user_coins=?, diamonds=?, moons=?, cp=?
                WHERE account_id=? AND date=?
            """, (p['rank'], p['stars'], p['demons'], p['coins'],
                  p['userCoins'], p['diamonds'], p['moons'], p['cp'], aid, date))

    conn.commit()
    return new_players, new_snaps

def main():
    print("=" * 50)
    print("GD Leaderboard Collector")
    print(f"Снапшот каждые {INTERVAL_HOURS} часов")
    print("=" * 50)

    conn = get_db()
    ensure_tables(conn)

    while True:
        now = datetime.now().strftime('%H:%M:%S')
        print(f"\n[{now}] Запрашиваем топ-100...")

        players = fetch_leaderboard(100)

        if not players:
            print("  Не удалось получить лидерборд, повтор через 10 мин")
            time.sleep(600)
            continue

        new_p, new_s = save_snapshot(conn, players)
        total_p = conn.execute('SELECT COUNT(*) FROM players').fetchone()[0]
        total_s = conn.execute('SELECT COUNT(*) FROM player_history').fetchone()[0]

        print(f"  Получено: {len(players)} игроков")
        print(f"  Новых игроков: {new_p} | Снапшотов сохранено: {new_s}")
        print(f"  Всего игроков в БД: {total_p} | Всего снапшотов: {total_s}")
        print(f"  Топ-3: " + " | ".join(
            f"#{p['rank']} {p['username']} ({p['stars']:,}★)" for p in players[:3]
        ))
        print(f"  Следующий снапшот через {INTERVAL_HOURS} часов")

        time.sleep(INTERVAL_HOURS * 3600)

if __name__ == '__main__':
    main()