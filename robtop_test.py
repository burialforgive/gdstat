import requests

def download_level(level_id):
    """Скачивает данные уровня напрямую с серверов RobTop"""
    response = requests.post(
        "https://www.boomlings.com/database/downloadGJLevel22.php",
        data={
            "levelID": level_id,
            "secret": "Wmfd2893gb7"
        },
        headers={"User-Agent": ""},
        timeout=10
    )
    return response.text

def get_user(username):
    """Ищет игрока напрямую"""
    response = requests.post(
        "https://www.boomlings.com/database/getGJUsers20.php",
        data={
            "str": username,
            "secret": "Wmfd2893gb7"
        },
        headers={"User-Agent": ""},
        timeout=10
    )
    return response.text

# Тестируем
print("Тест уровня Bloodbath (ID 10565740):")
result = download_level(10565740)
print(result[:200])

print("\nТест игрока Serponge:")
result = get_user("Serponge")
print(result[:200])