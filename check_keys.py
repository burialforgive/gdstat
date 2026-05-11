import requests
from robtop import parse_robtop

r = requests.post(
    "https://www.boomlings.com/database/downloadGJLevel22.php",
    data={"levelID": 10565740, "secret": "Wmfd2893gb7"},
    headers={"User-Agent": ""},
    timeout=10
)

raw = parse_robtop(r.text.split('#')[0])

# Показываем все ключи кроме поля 4 (данные карты)
for k, v in sorted(raw.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 999):
    if k != '4':
        print(f"  {k}: {v[:80] if len(str(v)) > 80 else v}")