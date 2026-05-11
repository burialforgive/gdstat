import requests
import base64
from datetime import datetime

SECRET = "Wmfd2893gb7"
BASE_URL = "https://www.boomlings.com/database"
HEADERS = {"User-Agent": ""}

def si(val, default=0):
    try:
        return int(val) if val and str(val).strip() else default
    except:
        return default

def parse_robtop(data, separator=':'):
    parts = data.split(separator)
    result = {}
    for i in range(0, len(parts) - 1, 2):
        result[parts[i]] = parts[i + 1]
    return result

def decode_description(encoded):
    try:
        padded = encoded + '=' * (4 - len(encoded) % 4)
        return base64.urlsafe_b64decode(padded).decode('utf-8')
    except:
        return ''

def parse_upload_date(relative):
    from datetime import timedelta
    if not relative:
        return None
    try:
        parts = relative.strip().split()
        if len(parts) < 2:
            return None
        num = int(parts[0])
        unit = parts[1].lower()
        now = datetime.now()
        if 'year' in unit:
            return (now - timedelta(days=num * 365)).strftime('%Y-%m-%d')
        elif 'month' in unit:
            return (now - timedelta(days=num * 30)).strftime('%Y-%m-%d')
        elif 'week' in unit:
            return (now - timedelta(weeks=num)).strftime('%Y-%m-%d')
        elif 'day' in unit:
            return (now - timedelta(days=num)).strftime('%Y-%m-%d')
        return None
    except:
        return None

ID_TO_VERSION = {
    2172: "1.0", 13794: "1.1", 61916: "1.2", 74634: "1.3",
    181913: "1.4", 417148: "1.5", 825973: "1.6", 1286694: "1.7",
    2804282: "1.8", 11010134: "1.9", 28315639: "2.0",
    97426239: "2.1", 118028739: "2.2"
}

ID_TO_YEAR = {
    130629: "2013", 3938229: "2014", 15435856: "2015",
    27788667: "2016", 40559842: "2017", 51591727: "2018",
    58976287: "2019", 66144272: "2020", 77026243: "2021",
    87321749: "2022", 98379505: "2023", 113708332: "2024",
    118028739: "2025"
}

GAME_VERSION_MAP = {
    10: "1.0", 11: "1.1", 12: "1.2", 13: "1.3",
    14: "1.4", 15: "1.5", 16: "1.6", 17: "1.7",
    18: "1.8", 19: "1.9", 20: "2.0", 21: "2.1", 22: "2.2"
}

def get_game_version(raw_val):
    num = si(raw_val)
    return GAME_VERSION_MAP.get(num, "2.2")

def get_version_by_id(level_id):
    for max_id, version in ID_TO_VERSION.items():
        if level_id <= max_id:
            return version
    return "2.2"

def get_year_by_id(level_id):
    for max_id, year in ID_TO_YEAR.items():
        if level_id <= max_id:
            return year
    return "2025"

def difficulty_from_level(raw):
    is_demon = si(raw.get('17'))
    is_auto = si(raw.get('25'))
    demon_type = si(raw.get('43'))
    diff_num = si(raw.get('9'))
    diff_den = si(raw.get('8'))
    if is_auto:
        return 'Auto'
    if is_demon:
        demon_map = {0: 'Hard Demon', 3: 'Easy Demon', 4: 'Medium Demon', 5: 'Insane Demon', 6: 'Extreme Demon'}
        return demon_map.get(demon_type, 'Hard Demon')
    if diff_den == 0:
        return 'Unrated'
    ratio = diff_num / diff_den
    if ratio == 0: return 'Unrated'
    if ratio <= 10: return 'Easy'
    if ratio <= 20: return 'Normal'
    if ratio <= 30: return 'Hard'
    if ratio <= 40: return 'Harder'
    return 'Insane'

def parse_level(raw_data):
    parts = raw_data.split('#')
    raw = parse_robtop(parts[0])
    if not raw.get('1'):
        return None
    downloads = max(si(raw.get('10')), 1)
    likes = si(raw.get('14'))
    epic_val = si(raw.get('42'))
    length_map = {0: 'Tiny', 1: 'Short', 2: 'Medium', 3: 'Long', 4: 'XL', 5: 'Plat'}
    length = length_map.get(si(raw.get('15')), 'Unknown')
    platformer = si(raw.get('15')) == 5
    return {
        'id': si(raw.get('1')),
        'name': raw.get('2', ''),
        'description': decode_description(raw.get('3', '')),
        'author': '',
        'difficulty': difficulty_from_level(raw),
        'downloads': downloads,
        'likes': likes,
        'like_ratio': round(likes / downloads * 100, 2),
        'stars': si(raw.get('18')),
        'orbs': 0,
        'diamonds': 0,
        'objects': si(raw.get('45')),
        'featured': si(raw.get('19')) > 0,
        'epic': epic_val == 1,
        'legendary': epic_val == 2,
        'mythic': epic_val == 3,
        'platformer': platformer,
        'gameVersion': get_game_version(raw.get('12', '0')),
        'uploadVersion': get_version_by_id(si(raw.get('1', 0))),
        'uploadYear': get_year_by_id(si(raw.get('1', 0))),
        'length': length,
        'coins': si(raw.get('37')),
        'verifiedCoins': raw.get('38') == '1',
        'copiedID': raw.get('30', '0'),
        'twoPlayer': raw.get('31') == '1',
        'ldm': raw.get('40') == '1',
        'cp': 0,
        'songName': '', 'songAuthor': '', 'songSize': '',
        'version': si(raw.get('5'), 1),
        'editorTime': si(raw.get('46')),
        'collected_at': datetime.now().isoformat(),
        'source': 'robtop',
        'uploadDate': parse_upload_date(raw.get('28', ''))
    }

def fetch_level(level_id, db_conn=None):
    try:
        r = requests.post(
            f"{BASE_URL}/downloadGJLevel22.php",
            data={"levelID": level_id, "secret": SECRET},
            headers=HEADERS, timeout=10
        )
        if r.status_code != 200 or r.text.strip() in ['-1', '']:
            return None
        level = parse_level(r.text)
        if not level:
            return None
        if db_conn and not level['author']:
            row = db_conn.execute('SELECT author FROM levels WHERE id=?', (level_id,)).fetchone()
            if row:
                level['author'] = row[0]
        return level
    except Exception as e:
        print(f"fetch_level error: {e}")
        return None

def fetch_leaderboard(count=100):
    """
    Запрашивает глобальный топ игроков по звёздам.
    type=1 — топ по звёздам, type=2 — по создателям
    Возвращает список игроков с полной статистикой.
    """
    try:
        r = requests.post(
            f"{BASE_URL}/getGJScores20.php",
            data={"type": 1, "secret": SECRET, "count": count},
            headers=HEADERS,
            timeout=15
        )
        if r.status_code != 200 or r.text.strip() in ['-1', '']:
            return []

        players = []
        for i, entry in enumerate(r.text.split('|')):
            if not entry.strip():
                continue
            raw = parse_robtop(entry)
            if not raw.get('1'):
                continue
            players.append({
                'rank':       i + 1,
                'username':   raw.get('1', ''),
                'playerID':   raw.get('2', ''),
                'stars':      si(raw.get('3')),
                'demons':     si(raw.get('4')),
                'cp':         si(raw.get('8')),
                'coins':      si(raw.get('13')),
                'userCoins':  si(raw.get('17')),
                'diamonds':   si(raw.get('46')),
                'moons':      si(raw.get('52')),
                'accountID':  raw.get('16', ''),
                'moderator':  si(raw.get('11')),
            })
        return players
    except Exception as e:
        print(f"fetch_leaderboard error: {e}")
        return []

def fetch_player(username):
    try:
        r = requests.post(
            f"{BASE_URL}/getGJUsers20.php",
            data={"str": username, "secret": SECRET},
            headers=HEADERS, timeout=10
        )
        if r.status_code != 200 or r.text.strip() in ['-1', '']:
            return None
        first = r.text.split('|')[0]
        raw = parse_robtop(first.split('#')[0])
        if not raw.get('1'):
            return None
        account_id = raw.get('16', '')
        rank = 0
        raw2 = {}
        if account_id:
            r2 = requests.post(
                f"{BASE_URL}/getGJUserInfo20.php",
                data={"targetAccountID": account_id, "secret": SECRET},
                headers=HEADERS, timeout=10
            )
            if r2.status_code == 200 and r2.text.strip() not in ['-1', '']:
                raw2 = parse_robtop(r2.text)
                rank = si(raw2.get('30', 0))
        # Парсим пройденные уровни по сложностям (ключ 56)
        # формат: Auto,Easy,Normal,Hard,Harder,Insane,Daily,Gauntlet
        classic_levels = {}
        raw2 = parse_robtop(r2.text) if account_id else {}
        lvl_str = raw2.get('56', '')
        if lvl_str:
            parts56 = lvl_str.split(',')
            keys = ['auto','easy','normal','hard','harder','insane','daily','gauntlet']
            for i, k in enumerate(keys):
                classic_levels[k] = si(parts56[i]) if i < len(parts56) else 0

        # Парсим платформер уровни (ключ 57)
        # формат: Auto,Easy,Normal,Hard,Harder,Insane,Weekly(?)
        plat_levels = {}
        plat_str = raw2.get('57', '')
        if plat_str:
            parts57 = plat_str.split(',')
            keys57 = ['auto','easy','normal','hard','harder','insane']
            for i, k in enumerate(keys57):
                plat_levels[k] = si(parts57[i]) if i < len(parts57) else 0

        # Парсим демонов (ключ 55)
        # формат: easyC,mediumC,hardC,insaneC,extremeC,easyP,mediumP,...
        classic_demons = {}
        plat_demons = {}
        dem_str = raw2.get('55', '')
        if dem_str:
            parts55 = dem_str.split(',')
            dem_keys = ['easy','medium','hard','insane','extreme']
            for i, k in enumerate(dem_keys):
                classic_demons[k] = si(parts55[i]) if i < len(parts55) else 0
            for i, k in enumerate(dem_keys):
                plat_demons[k] = si(parts55[i+5]) if i+5 < len(parts55) else 0

        return {
            'username': raw.get('1', ''),
            'playerID': raw.get('2', ''),
            'accountID': account_id,
            'stars': si(raw.get('3')),
            'demons': si(raw.get('4')),
            'coins': si(raw.get('13')),
            'userCoins': si(raw.get('17')),
            'diamonds': si(raw.get('46')),
            'moons': si(raw.get('52')),
            'cp': si(raw.get('8')),
            'rank': rank,
            'moderator': si(raw.get('11')),
            'youtube': raw.get('20', ''),
            'twitter': raw.get('44', ''),
            'twitch': raw.get('45', ''),
            'classicDemonsCompleted': classic_demons,
            'platformerDemonsCompleted': plat_demons,
            'classicLevelsCompleted': classic_levels,
            'platformerLevelsCompleted': plat_levels,
            'socials': any([raw.get('20'), raw.get('44'), raw.get('45')])
        }
    except Exception as e:
        print(f"fetch_player error: {e}")
        return None

def search_levels(query, page=0):
    try:
        r = requests.post(
            f"{BASE_URL}/getGJLevels21.php",
            data={"str": query, "type": 0, "page": page, "secret": SECRET},
            headers=HEADERS, timeout=10
        )
        if r.status_code != 200 or r.text.strip() in ['-1', '']:
            return []
        sections = r.text.split('#')
        levels_raw = sections[0].split('|')
        authors = {}
        if len(sections) > 1:
            for a in sections[1].split('|'):
                if not a.strip():
                    continue
                parts = a.split(':')
                if len(parts) >= 2:
                    authors[parts[0]] = parts[1]
        levels = []
        for lvl_raw in levels_raw:
            if not lvl_raw.strip():
                continue
            lvl = parse_level(lvl_raw)
            if lvl:
                raw = parse_robtop(lvl_raw)
                author_id = raw.get('6', '')
                lvl['author'] = authors.get(author_id, 'Unknown')
                levels.append(lvl)
        return levels
    except Exception as e:
        print(f"search_levels error: {e}")
        return []

if __name__ == '__main__':
    print("Тест fetch_leaderboard (топ-5):")
    lb = fetch_leaderboard(5)
    for p in lb:
        print(f"  #{p['rank']} {p['username']} | {p['stars']:,} звёзд | {p['demons']} демонов")