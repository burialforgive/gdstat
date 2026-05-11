from flask import Flask, render_template, jsonify, redirect, request
import requests
import json
import os
import sqlite3
import time

app = Flask(__name__)
DATA_DIR = "data"
DB_FILE = os.path.join(DATA_DIR, "levels.db")

_valid_ids_cache = []

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def row_to_dict(row):
    if row is None:
        return None
    d = dict(row)
    d['featured'] = bool(d.get('featured'))
    d['epic'] = bool(d.get('epic'))
    d['legendary'] = bool(d.get('legendary'))
    d['mythic'] = bool(d.get('mythic'))
    d['platformer'] = bool(d.get('platformer'))
    d['verifiedCoins'] = bool(d.get('verified_coins'))
    d['twoPlayer'] = bool(d.get('two_player'))
    d['ldm'] = bool(d.get('ldm'))
    d['gameVersion'] = d.get('game_version', '')
    d['copiedID'] = d.get('copied_id', '0')
    d['downloads'] = d.get('downloads', 0)
    d['likes'] = d.get('likes', 0)
    d['like_ratio'] = d.get('like_ratio', 0)
    d['length'] = d.get('length', '')
    d['objects'] = d.get('objects', 0)
    return d

def get_valid_ids():
    global _valid_ids_cache
    if _valid_ids_cache:
        return _valid_ids_cache
    conn = get_db()
    rows = conn.execute(
        'SELECT id FROM levels WHERE downloads > 1000 ORDER BY RANDOM() LIMIT 5000'
    ).fetchall()
    conn.close()
    _valid_ids_cache = [r['id'] for r in rows]
    return _valid_ids_cache

@app.route('/')
def index():
    conn = get_db()

    total = conn.execute('SELECT COUNT(*) FROM levels').fetchone()[0]
    platformers = conn.execute('SELECT COUNT(*) FROM levels WHERE platformer=1').fetchone()[0]
    avg_ratio = conn.execute('SELECT AVG(like_ratio) FROM levels WHERE downloads > 100').fetchone()[0] or 0

    top_levels = conn.execute('''
        SELECT * FROM levels
        WHERE downloads >= 5000
        ORDER BY like_ratio DESC
        LIMIT 10
    ''').fetchall()

    conn.close()

    return render_template('index.html',
        total_levels=total,
        platformers=platformers,
        classic=total - platformers,
        avg_ratio=round(avg_ratio, 2),
        top_levels=[row_to_dict(r) for r in top_levels],
    )

import time

_stats_cache = None
_stats_cache_time = 0
STATS_CACHE_TTL = 3600  # обновляем раз в час

_stats_cache = None
_stats_cache_time = 0
STATS_CACHE_TTL = 3600

@app.route('/stats')
def global_stats():
    global _stats_cache, _stats_cache_time

    if _stats_cache and (time.time() - _stats_cache_time) < STATS_CACHE_TTL:
        return _stats_cache

    conn = get_db()

    # ───────────────────────────────────────────
    # Один запрос вместо 15 — всё считается за один проход
    # ───────────────────────────────────────────
    row = conn.execute('''
        SELECT
            COUNT(*)                                         AS total,
            SUM(CASE WHEN platformer=1 THEN 1 ELSE 0 END)   AS platformers,
            SUM(downloads)                                   AS total_downloads,
            SUM(likes)                                       AS total_likes,
            SUM(CASE WHEN likes < 0 THEN 1 ELSE 0 END)      AS negative_count,
            SUM(CASE WHEN mythic=1 THEN 1 ELSE 0 END)        AS mythic_count,
            SUM(CASE WHEN legendary=1 THEN 1 ELSE 0 END)     AS legendary_count,
            SUM(CASE WHEN epic=1 THEN 1 ELSE 0 END)          AS epic_count,
            SUM(CASE WHEN stars > 0 THEN 1 ELSE 0 END)       AS rated_count,
            SUM(CASE WHEN likes > 0 THEN 1 ELSE 0 END)       AS likes_gt0,
            SUM(CASE WHEN likes >= 10 THEN 1 ELSE 0 END)     AS likes_gt10,
            SUM(CASE WHEN likes >= 100 THEN 1 ELSE 0 END)    AS likes_gt100,
            SUM(CASE WHEN likes >= 1000 THEN 1 ELSE 0 END)   AS likes_gt1000,
            SUM(CASE WHEN featured=1 THEN 1 ELSE 0 END)      AS featured_count,
            AVG(CASE WHEN downloads > 100 THEN like_ratio END) AS avg_ratio
        FROM levels
    ''').fetchone()

    total            = row['total'] or 0
    platformers      = row['platformers'] or 0
    total_downloads  = row['total_downloads'] or 0
    total_likes      = row['total_likes'] or 0
    negative_count   = row['negative_count'] or 0
    mythic_count     = row['mythic_count'] or 0
    legendary_count  = row['legendary_count'] or 0
    epic_count       = row['epic_count'] or 0
    rated_count      = row['rated_count'] or 0
    avg_ratio        = row['avg_ratio'] or 0

    chances = [
        ("Получить хотя бы 1 лайк",    round((row['likes_gt0']   or 0) / max(total, 1) * 100, 1)),
        ("Получить 10+ лайков",         round((row['likes_gt10']  or 0) / max(total, 1) * 100, 1)),
        ("Получить 100+ лайков",        round((row['likes_gt100'] or 0) / max(total, 1) * 100, 1)),
        ("Получить 1000+ лайков",       round((row['likes_gt1000']or 0) / max(total, 1) * 100, 1)),
        ("Попасть в Featured",          round((row['featured_count'] or 0) / max(total, 1) * 100, 2)),
        ("Попасть в Epic",              round(epic_count / max(total, 1) * 100, 2)),
        ("Уйти в минус (дизлайки)",     round(negative_count / max(total, 1) * 100, 1)),
    ]

    # Группировки — быстрые благодаря индексам
    diff_rows = conn.execute(
        'SELECT difficulty, COUNT(*) as cnt FROM levels GROUP BY difficulty ORDER BY cnt DESC'
    ).fetchall()
    diff_colors = {
        'Auto': '#9ca3af', 'Easy': '#34d399', 'Normal': '#60a5fa',
        'Hard': '#f59e0b', 'Harder': '#fb923c', 'Insane': '#f87171',
        'Easy Demon': '#c084fc', 'Medium Demon': '#a78bfa',
        'Hard Demon': '#818cf8', 'Insane Demon': '#6366f1',
        'Extreme Demon': '#4f46e5'
    }
    difficulties = [(r['difficulty'], r['cnt'], diff_colors.get(r['difficulty'], '#555')) for r in diff_rows]

    ver_rows = conn.execute(
        'SELECT game_version, COUNT(*) as cnt FROM levels GROUP BY game_version ORDER BY cnt DESC LIMIT 8'
    ).fetchall()
    versions = [(r['game_version'], r['cnt']) for r in ver_rows]

    anomalies = conn.execute(
        'SELECT * FROM levels WHERE likes > downloads AND downloads > 0 ORDER BY like_ratio DESC LIMIT 5'
    ).fetchall()
    most_downloaded = conn.execute(
        'SELECT * FROM levels ORDER BY downloads DESC LIMIT 5'
    ).fetchall()

    conn.close()

    registered_count   = 1807152
    unregistered_count = 145032

    result = render_template('stats.html',
        total=total,
        platformers=platformers,
        classic=total - platformers,
        avg_ratio=round(avg_ratio, 2),
        total_downloads=total_downloads,
        registered_count=registered_count,
        unregistered_count=unregistered_count,
        total_likes=total_likes,
        negative_count=negative_count,
        mythic_count=mythic_count,
        legendary_count=legendary_count,
        epic_count=epic_count,
        avg_objects=0,
        max_objects=0,
        chances=chances,
        difficulties=difficulties,
        versions=versions,
        rated_count=rated_count,
        anomalies=[row_to_dict(r) for r in anomalies],
        most_downloaded=[row_to_dict(r) for r in most_downloaded]
    )

    _stats_cache = result
    _stats_cache_time = time.time()
    return result

from robtop import fetch_level, fetch_player, search_levels

@app.route('/level/<int:level_id>')
def level_page(level_id):
    conn = get_db()
    
    # Сначала получаем свежие данные с серверов RobTop
    data = fetch_level(level_id, conn)
    
    if not data:
        # Если сервер не отвечает — берём из нашей базы
        row = conn.execute('SELECT * FROM levels WHERE id=?', (level_id,)).fetchone()
        conn.close()
        if row:
            data = row_to_dict(row)
            return render_template('level.html', level=data)
        return render_template('level.html', level=None, error="Уровень не найден")
    
    conn.close()
    return render_template('level.html', level=data)

@app.route('/player/<username>')
def player_page(username):
    player = fetch_player(username)
    if not player:
        return "Игрок не найден", 404
    player['socials'] = any([player.get('youtube'), player.get('twitter'), player.get('twitch')])
    return render_template('player.html', player=player)

@app.route('/api/player/<username>')
def player_api(username):
    player = fetch_player(username)
    if not player:
        return jsonify({'error': 'not found'})
    return jsonify(player)

@app.route('/api/search/levels')
def search_levels_api():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    results = search_levels(query)
    return jsonify(results)

@app.route('/api/levels')
def api_levels():
    order = request.args.get('order', 'desc')
    period = request.args.get('period', 'all')
    offset = int(request.args.get('offset', 0))
    limit = min(int(request.args.get('limit', 10)), 100)
    sort = request.args.get('sort', 'like_ratio')

    # Белый список полей для сортировки
    allowed = {'like_ratio', 'downloads', 'likes'}
    if sort not in allowed:
        sort = 'like_ratio'

    conn = get_db()

    period_filter = ''
    if period == 'day':
        period_filter = "AND upload_date >= date('now', '-1 day')"
    elif period == 'week':
        period_filter = "AND upload_date >= date('now', '-7 days')"
    elif period == 'month':
        period_filter = "AND upload_date >= date('now', '-30 days')"

    sql_order = 'DESC' if order == 'desc' else 'ASC'

# Убираем лимит загрузок если сортировка не дефолтная
    dl_filter = "AND downloads >= 5000" if sort == 'like_ratio' else "AND downloads >= 1000"

    rows = conn.execute(f'''
        SELECT * FROM levels
        WHERE 1=1
        {dl_filter}
        {period_filter}
        ORDER BY {sort} {sql_order}
        LIMIT ? OFFSET ?
    ''', (limit, offset)).fetchall()

    conn.close()
    return jsonify([row_to_dict(r) for r in rows])

# ───────────────────────────────────────────
# Добавь эти роуты в app.py после существующих
# ───────────────────────────────────────────

@app.route('/leaderboard')
def leaderboard_page():
    conn = get_db()

    # Последний снапшот — текущий топ
    latest_date = conn.execute(
        'SELECT MAX(date) FROM player_history'
    ).fetchone()[0]

    if not latest_date:
        conn.close()
        return render_template('leaderboard.html', players=[], dates=[])

    top = conn.execute("""
        SELECT ph.*, p.username, p.account_id
        FROM player_history ph
        JOIN players p ON ph.account_id = p.account_id
        WHERE ph.date = ?
        ORDER BY ph.rank ASC
        LIMIT 100
    """, (latest_date,)).fetchall()

    # Список дат для графика (последние 30 дней)
    dates = conn.execute("""
        SELECT DISTINCT date FROM player_history
        ORDER BY date DESC LIMIT 30
    """).fetchall()
    dates = [r['date'] for r in reversed(dates)]

    conn.close()
    return render_template('leaderboard.html',
        players=[dict(r) for r in top],
        dates=dates,
        updated=latest_date
    )

@app.route('/api/leaderboard/history')
def leaderboard_history_api():
    """
    Возвращает историю для графика.
    ?metric=stars|demons|coins|moons — что отображать
    ?accounts=id1,id2,id3 — фильтр по игрокам (макс 10)
    """
    metric   = request.args.get('metric', 'stars')
    accounts = request.args.get('accounts', '')

    allowed_metrics = {'stars', 'demons', 'coins', 'user_coins', 'diamonds', 'moons', 'cp', 'rank'}
    if metric not in allowed_metrics:
        metric = 'stars'

    conn = get_db()

    # Последние 30 дней
    dates = conn.execute("""
        SELECT DISTINCT date FROM player_history
        ORDER BY date DESC LIMIT 30
    """).fetchall()
    dates = [r['date'] for r in reversed(dates)]

    if accounts:
        aid_list = accounts.split(',')[:10]
    else:
        # Топ-10 по последнему снапшоту
        latest = conn.execute('SELECT MAX(date) FROM player_history').fetchone()[0]
        rows = conn.execute("""
            SELECT account_id FROM player_history
            WHERE date=? ORDER BY rank ASC LIMIT 10
        """, (latest,)).fetchall()
        aid_list = [r['account_id'] for r in rows]

    result = {}
    for aid in aid_list:
        username = conn.execute(
            'SELECT username FROM players WHERE account_id=?', (aid,)
        ).fetchone()
        if not username:
            continue
        history = conn.execute(f"""
            SELECT date, {metric} as value
            FROM player_history
            WHERE account_id=?
            ORDER BY date ASC
        """, (aid,)).fetchall()
        result[aid] = {
            'username': username['username'],
            'data': {r['date']: r['value'] for r in history}
        }

    conn.close()
    return jsonify({'dates': dates, 'players': result})

if __name__ == '__main__':
    print("Запускаем GD Stats...")
    print(f"База данных: {DB_FILE}")
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM levels').fetchone()[0]
    conn.close()
    print(f"Уровней в базе: {count:,}")
    app.run(debug=True, port=5000)

    