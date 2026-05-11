import requests
import os

os.makedirs("static/difficulties", exist_ok=True)

# Пробуем несколько источников для демонов
demon_sources = [
    # Вариант 1 — другая ветка GDBrowser
    {
        "easyDemon.png":   "https://raw.githubusercontent.com/GDColon/GDBrowser/master/assets/difficulties/easy-demon.png",
        "mediumDemon.png": "https://raw.githubusercontent.com/GDColon/GDBrowser/master/assets/difficulties/medium-demon.png",
        "hardDemon.png":   "https://raw.githubusercontent.com/GDColon/GDBrowser/master/assets/difficulties/hard-demon.png",
        "insaneDemon.png": "https://raw.githubusercontent.com/GDColon/GDBrowser/master/assets/difficulties/insane-demon.png",
        "extremeDemon.png":"https://raw.githubusercontent.com/GDColon/GDBrowser/master/assets/difficulties/extreme-demon.png",
    },
    # Вариант 2 — с дефисом и заглавной
    {
        "easyDemon.png":   "https://raw.githubusercontent.com/GDColon/GDBrowser/master/assets/difficulties/Easy-Demon.png",
        "mediumDemon.png": "https://raw.githubusercontent.com/GDColon/GDBrowser/master/assets/difficulties/Medium-Demon.png",
        "hardDemon.png":   "https://raw.githubusercontent.com/GDColon/GDBrowser/master/assets/difficulties/Hard-Demon.png",
        "insaneDemon.png": "https://raw.githubusercontent.com/GDColon/GDBrowser/master/assets/difficulties/Insane-Demon.png",
        "extremeDemon.png":"https://raw.githubusercontent.com/GDColon/GDBrowser/master/assets/difficulties/Extreme-Demon.png",
    },
    # Вариант 3 — GDBrowser GitHub Pages
    {
        "easyDemon.png":   "https://gdbrowser.github.io/assets/difficulties/easyDemon.png",
        "mediumDemon.png": "https://gdbrowser.github.io/assets/difficulties/mediumDemon.png",
        "hardDemon.png":   "https://gdbrowser.github.io/assets/difficulties/hardDemon.png",
        "insaneDemon.png": "https://gdbrowser.github.io/assets/difficulties/insaneDemon.png",
        "extremeDemon.png":"https://gdbrowser.github.io/assets/difficulties/extremeDemon.png",
    },
]

demons = ["easyDemon.png","mediumDemon.png","hardDemon.png","insaneDemon.png","extremeDemon.png"]

for local in demons:
    saved = False
    for source in demon_sources:
        url = source[local]
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200 and len(r.content) > 500:
                with open(f"static/difficulties/{local}", "wb") as f:
                    f.write(r.content)
                print(f"✓ {local} ({len(r.content)} байт) — {url}")
                saved = True
                break
        except:
            pass
    if not saved:
        print(f"✗ {local} — не найден ни в одном источнике")