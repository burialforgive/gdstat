import json
import os

DATA_DIR = "data"
SOURCE_FILE = os.path.join(DATA_DIR, "data (sorted).json")
OUTPUT_FILE = os.path.join(DATA_DIR, "all_levels.json")

print("Читаем файл HeXi... (может занять минуту)")

with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
    raw = json.load(f)

print(f"Загружено записей: {len(raw):,}")

# Его формат: словарь {id: данные} или список — определим автоматически
if isinstance(raw, dict):
    levels_raw = list(raw.values())
elif isinstance(raw, list):
    levels_raw = raw

print("Конвертируем в наш формат...")

levels = []
skipped = 0

for item in levels_raw:
    # Пропускаем несуществующие уровни (None)
    if item is None:
        skipped += 1
        continue
    if not isinstance(item, dict):
        skipped += 1
        continue
    if 'id' not in item or 'name' not in item:
        skipped += 1
        continue

    # Считаем метрику качества
    downloads = max(item.get('downloads', 1), 1)
    likes = item.get('likes', 0)
    item['like_ratio'] = round(likes / downloads * 100, 2)
    item['source'] = 'gdls'

    levels.append(item)

print(f"Уровней после фильтрации: {len(levels):,}")
print(f"Пропущено (None/битые): {skipped:,}")

# Загружаем нашу текущую базу чтобы объединить
existing = []
if os.path.exists(OUTPUT_FILE):
    print("Загружаем нашу текущую базу...")
    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        existing = json.load(f)
    print(f"Наших уровней: {len(existing):,}")

# Объединяем — наши данные приоритетнее (у нас актуальные загрузки)
print("Объединяем базы...")
combined = {str(l['id']): l for l in levels}  # сначала GDLS
for l in existing:
    combined[str(l['id'])] = l  # наши перезаписывают

result = list(combined.values())

print(f"Итого уникальных уровней: {len(result):,}")
print("Сохраняем...")

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False)

print(f"Готово! Файл сохранён: {OUTPUT_FILE}")
print(f"Размер базы: {os.path.getsize(OUTPUT_FILE) / 1024 / 1024:.1f} МБ")