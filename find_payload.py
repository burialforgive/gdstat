import json

data = json.load(open('data/history_index.json', encoding='utf-8'))

top = sorted(
    data.items(),
    key=lambda x: x[1]['history'][-1]['downloads'] - x[1]['history'][0]['downloads'],
    reverse=True
)[:5]

for k, v in top:
    growth = v['history'][-1]['downloads'] - v['history'][0]['downloads']
    print(f"ID: {k} | {v['name']} by {v['author']} | рост: +{growth:,}")