import json
import os
from datetime import datetime

DATA_DIR = "data"

def build_index():
    """
    Читает все снапшоты и строит индекс:
    для каждого уровня — список его состояний во времени
    """
    print("Строим индекс истории уровней...")
    
    # Находим все снапшоты коллектора
    snapshots = sorted([
        f for f in os.listdir(DATA_DIR) 
        if f.startswith('levels_2') and f.endswith('.json')
    ])
    
    print(f"Найдено снапшотов: {len(snapshots)}")
    
    # Индекс: id уровня -> список {time, downloads, likes, like_ratio}
    index = {}
    
    for filename in snapshots:
        path = os.path.join(DATA_DIR, filename)
        timestamp = filename.replace('levels_', '').replace('.json', '')
        
        try:
            with open(path, encoding='utf-8') as f:
                levels = json.load(f)
            
            for level in levels:
                level_id = str(level.get('id', ''))
                if not level_id:
                    continue
                
                if level_id not in index:
                    index[level_id] = {
                        'name': level.get('name', ''),
                        'author': level.get('author', ''),
                        'history': []
                    }
                
                downloads = max(level.get('downloads', 1), 1)
                likes = level.get('likes', 0)
                
                index[level_id]['history'].append({
                    'time': timestamp,
                    'downloads': level.get('downloads', 0),
                    'likes': likes,
                    'like_ratio': round(likes / downloads * 100, 2)
                })
        
        except Exception as e:
            print(f"Ошибка в {filename}: {e}")
    
    # Оставляем только уровни с историей из 2+ точек
    tracked = {k: v for k, v in index.items() if len(v['history']) >= 2}
    
    # Сохраняем индекс
    index_path = os.path.join(DATA_DIR, "history_index.json")
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(tracked, f, ensure_ascii=False, indent=2)
    
    print(f"Уровней с историей: {len(tracked)}")
    print(f"Индекс сохранён: {index_path}")
    
    # Показываем топ по росту загрузок
    growth = []
    for level_id, data in tracked.items():
        history = data['history']
        first = history[0]['downloads']
        last = history[-1]['downloads']
        if first > 0:
            growth_pct = round((last - first) / first * 100, 1)
            growth.append((data['name'], data['author'], first, last, growth_pct))
    
    growth.sort(key=lambda x: x[4], reverse=True)
    
    print("\nТоп 10 по росту загрузок:")
    for name, author, first, last, pct in growth[:10]:
        print(f"  {name} by {author}: {first:,} → {last:,} (+{pct}%)")
    
    return tracked

build_index()