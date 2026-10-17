# -*- coding: utf-8 -*-
"""Genera automaticamente uno schema di parole crociate con intersezioni,
a partire da una lista di coppie indizio/risposta inserite dall'istruttore.

Garantisce che OGNI parola nello schema finale sia collegata (in senso
orizzontale o verticale) ad almeno un'altra: nessuna parola isolata,
come in un vero cruciverba. Se una parola non riesce a trovare
un'intersezione valida nemmeno dopo più tentativi, viene esclusa dallo
schema piuttosto che piazzata scollegata (il chiamante puo' segnalarlo
tramite la chiave 'dropped' del risultato).
"""
import re

DIRECTIONS = {'across': (0, 1), 'down': (1, 0)}


def _clean(answer):
    return re.sub(r'[^A-Za-zÀ-ÖØ-öø-ÿ]', '', answer or '').upper()


def build_layout(raw_entries):
    words = []
    for e in raw_entries:
        ans = _clean(e.get('answer', ''))
        clue = (e.get('clue') or '').strip()
        if ans and clue and len(ans) >= 2:
            words.append({'answer': ans, 'clue': clue})
    if len(words) < 2:
        return None

    words.sort(key=lambda w: -len(w['answer']))

    placed = []
    grid = {}

    def fits(word, direction, row, col):
        dr, dc = DIRECTIONS[direction]
        crosses = 0
        for i, ch in enumerate(word):
            r, c = row + dr * i, col + dc * i
            existing = grid.get((r, c))
            if existing is not None:
                if existing != ch:
                    return None
                crosses += 1
            else:
                if direction == 'across':
                    if grid.get((r - 1, c)) is not None or grid.get((r + 1, c)) is not None:
                        return None
                else:
                    if grid.get((r, c - 1)) is not None or grid.get((r, c + 1)) is not None:
                        return None
        r0, c0 = row - dr, col - dc
        r1, c1 = row + dr * len(word), col + dc * len(word)
        if grid.get((r0, c0)) is not None or grid.get((r1, c1)) is not None:
            return None
        return crosses

    def try_place(word):
        best = None
        for p in placed:
            other_dir = 'down' if p['direction'] == 'across' else 'across'
            for i, ch in enumerate(word['answer']):
                for j, pch in enumerate(p['answer']):
                    if ch != pch:
                        continue
                    dr, dc = DIRECTIONS[p['direction']]
                    pr, pc = p['row'] + dr * j, p['col'] + dc * j
                    ndr, ndc = DIRECTIONS[other_dir]
                    row, col = pr - ndr * i, pc - ndc * i
                    crosses = fits(word['answer'], other_dir, row, col)
                    if crosses is not None and (best is None or crosses > best[0]):
                        best = (crosses, other_dir, row, col)
        if not best:
            return False
        _, direction, row, col = best
        dr, dc = DIRECTIONS[direction]
        for i, ch in enumerate(word['answer']):
            grid[(row + dr * i, col + dc * i)] = ch
        placed.append({'answer': word['answer'], 'clue': word['clue'], 'direction': direction, 'row': row, 'col': col})
        return True

    first = words[0]
    for i, ch in enumerate(first['answer']):
        grid[(0, i)] = ch
    placed.append({'answer': first['answer'], 'clue': first['clue'], 'direction': 'across', 'row': 0, 'col': 0})

    remaining = words[1:]
    progress = True
    while remaining and progress:
        progress = False
        still_remaining = []
        for word in remaining:
            if try_place(word):
                progress = True
            else:
                still_remaining.append(word)
        remaining = still_remaining

    dropped = [w['answer'] for w in remaining]
    if len(placed) < 2:
        return None

    min_r = min(r for r, c in grid.keys())
    min_c = min(c for r, c in grid.keys())
    for p in placed:
        p['row'] -= min_r
        p['col'] -= min_c
    normalized = {(r - min_r, c - min_c): ch for (r, c), ch in grid.items()}

    max_r = max(r for r, c in normalized.keys())
    max_c = max(c for r, c in normalized.keys())

    starts = sorted({(p['row'], p['col']) for p in placed}, key=lambda rc: (rc[0], rc[1]))
    number_map = {rc: idx for idx, rc in enumerate(starts, start=1)}
    for p in placed:
        p['number'] = number_map[(p['row'], p['col'])]

    return {'width': max_c + 1, 'height': max_r + 1, 'entries': placed, 'dropped': dropped}
