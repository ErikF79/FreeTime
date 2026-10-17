# -*- coding: utf-8 -*-
"""Motore riutilizzabile per i contenuti inseriti dagli istruttori
(frasi per la Ruota, parole per Taboo/Passaparola, audio per Sarabanda...).
Ogni gioco pesca il prossimo contenuto non ancora usato per il proprio
game_id, cosi' non serve costruire un motore/dizionario dedicato per
ciascun gioco linguistico."""
import json, os, uuid
from datetime import datetime

def load_content(path):
    if not os.path.isfile(path): return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (ValueError, OSError):
        return []

def save_content(path, items):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def add_content(path, game_id, payload):
    items = load_content(path)
    item = {'id': uuid.uuid4().hex, 'game_id': game_id, 'used': False,
             'created_at': datetime.now().isoformat(timespec='seconds')}
    item.update(payload)
    items.append(item)
    save_content(path, items)
    return item

def pending_for(path, game_id):
    return [i for i in load_content(path) if i.get('game_id') == game_id and not i.get('used')]

def next_pending(path, game_id):
    items = pending_for(path, game_id)
    return items[0] if items else None

def mark_used(path, content_id):
    items = load_content(path)
    for item in items:
        if item.get('id') == content_id:
            item['used'] = True
            save_content(path, items)
            return True
    return False

def delete_content(path, content_id):
    items = load_content(path)
    filtered = [i for i in items if i.get('id') != content_id]
    if len(filtered) == len(items): return False
    save_content(path, filtered)
    return True
