# -*- coding: utf-8 -*-
from games.base_game import BaseGame
from engine.crossword_builder import build_layout

WORD_POINTS = 5
LETTER_COST = 15

class CrosswordGame(BaseGame):
    def __init__(self):
        BaseGame.__init__(self, 'crossword', 'Cruciverba',
                           'Uno schema a incroci reali: indovina le parole intere, la prima lettera è gratis per chi apre la partita.',
                           'Linguaggio', 1, 8, 'CRW', 'ready')
        self.title = ''
        self.width = 0
        self.height = 0
        self.entries = []
        self.cells = []
        self.dropped = []
        self.status = 'active'
        self.moves_played = 0
        self.turn_index = 0
        self.participant_ids = []
        self.scores = {}
        self.last_message = ''

    def setup(self, title, raw_entries, participant_ids):
        layout = build_layout(raw_entries)
        self.title = (title or '').strip()
        self.entries = []
        self.cells = []
        self.dropped = []
        if layout:
            self.width = layout['width']
            self.height = layout['height']
            self.dropped = layout.get('dropped', [])
            cell_map = {}
            for e in layout['entries']:
                e = dict(e)
                e['awarded'] = False
                self.entries.append(e)
                dr, dc = (0, 1) if e['direction'] == 'across' else (1, 0)
                for i, ch in enumerate(e['answer']):
                    r, c = e['row'] + dr * i, e['col'] + dc * i
                    cell_map[(r, c)] = ch
            self.cells = [{'row': r, 'col': c, 'letter': ch, 'revealed': False, 'current_letter': None}
                          for (r, c), ch in cell_map.items()]
        self.status = 'active'
        self.moves_played = 0
        self.turn_index = 0
        self.participant_ids = list(participant_ids)
        self.scores = {pid: 0 for pid in self.participant_ids}
        self.last_message = ('Il primo turno può scegliere una lettera gratis (valida su tutto lo schema) '
                              'oppure tentare subito una parola.')

    def current_player(self):
        if not self.participant_ids: return None
        return self.participant_ids[self.turn_index % len(self.participant_ids)]

    def advance_turn(self):
        if self.participant_ids:
            self.turn_index = (self.turn_index + 1) % len(self.participant_ids)

    def _cell_map(self):
        return {(c['row'], c['col']): c for c in self.cells}

    def entry_positions(self, entry):
        dr, dc = (0, 1) if entry['direction'] == 'across' else (1, 0)
        return [(entry['row'] + dr * i, entry['col'] + dc * i) for i in range(len(entry['answer']))]

    def display_entry(self, entry):
        cmap = self._cell_map()
        out = []
        for (r, c) in self.entry_positions(entry):
            cell = cmap.get((r, c))
            if cell and cell['revealed']:
                out.append(cell['letter'])
            elif cell and cell.get('current_letter'):
                out.append(cell['current_letter'])
            else:
                out.append('_')
        return out

    def is_entry_solved(self, entry):
        cmap = self._cell_map()
        return all(cmap.get((r, c), {}).get('revealed') for (r, c) in self.entry_positions(entry))

    def is_complete(self):
        return all(c['revealed'] for c in self.cells) if self.cells else False

    def matrix(self):
        cmap = self._cell_map()
        starts = {(e['row'], e['col']): e['number'] for e in self.entries}
        rows = []
        for r in range(self.height):
            row = []
            for c in range(self.width):
                cell = cmap.get((r, c))
                if not cell:
                    row.append({'active': False})
                else:
                    if cell['revealed']:
                        disp, tentative = cell['letter'], False
                    elif cell.get('current_letter'):
                        disp, tentative = cell['current_letter'], True
                    else:
                        disp, tentative = '', False
                    row.append({'active': True, 'letter': disp, 'tentative': tentative,
                                'number': starts.get((r, c))})
            rows.append(row)
        return rows

    def _award_if_solved(self, entry, pid):
        if pid and not entry.get('awarded') and self.is_entry_solved(entry):
            self.scores[pid] = self.scores.get(pid, 0) + WORD_POINTS
            entry['awarded'] = True
            return True
        return False

    def guess_word(self, entry_index, word):
        if self.status != 'active': return False, 'Il cruciverba è concluso.'
        if entry_index is None or entry_index < 0 or entry_index >= len(self.entries):
            return False, 'Parola non valida.'
        entry = self.entries[entry_index]
        if self.is_entry_solved(entry): return False, 'Questa parola è già stata risolta.'
        word = (word or '').strip().upper()
        if not word.isalpha(): return False, 'La parola può contenere solo lettere.'
        if len(word) != len(entry['answer']):
            return False, 'La parola deve avere {0} lettere.'.format(len(entry['answer']))
        positions = self.entry_positions(entry)
        cmap = self._cell_map()
        for (r, c), ch in zip(positions, word):
            cell = cmap[(r, c)]
            if cell['revealed'] and cell['letter'] != ch:
                return False, 'La parola non è compatibile con le lettere già confermate in quel punto dello schema.'
        pid = self.current_player()
        if word == entry['answer']:
            for (r, c) in positions:
                cmap[(r, c)]['revealed'] = True
                cmap[(r, c)]['current_letter'] = None
            self._award_if_solved(entry, pid)
            self.last_message = 'Parola corretta! +{0} punti alla squadra.'.format(WORD_POINTS)
        else:
            for (r, c), ch in zip(positions, word):
                if not cmap[(r, c)]['revealed']:
                    cmap[(r, c)]['current_letter'] = ch
            self.last_message = 'Parola inserita ma non corretta: resta in griglia finché qualcuno non la corregge.'
        self.moves_played += 1
        if self.is_complete():
            self.status = 'won'
            self.last_message = 'Schema completato!'
        else:
            self.advance_turn()
        return True, self.last_message

    def reveal_letter(self, letter):
        if self.status != 'active': return False, 'Il cruciverba è concluso.'
        letter = (letter or '').strip().upper()
        if not letter or len(letter) != 1 or not letter.isalpha():
            return False, 'Inserisci una singola lettera.'
        cost = 0 if self.moves_played == 0 else LETTER_COST
        pid = self.current_player()
        if cost > 0 and self.scores.get(pid, 0) < cost:
            return False, 'Servono almeno {0} punti per comprare una lettera.'.format(LETTER_COST)
        changed = False
        for cell in self.cells:
            if cell['letter'] == letter and not cell['revealed']:
                cell['revealed'] = True
                cell['current_letter'] = None
                changed = True
        if not changed:
            return False, 'Lettera non presente nello schema o già rivelata ovunque.'
        if cost > 0 and pid:
            self.scores[pid] = self.scores.get(pid, 0) - cost
        for entry in self.entries:
            self._award_if_solved(entry, pid)
        self.moves_played += 1
        self.last_message = 'Lettera "{0}" rivelata in tutto lo schema{1}.'.format(
            letter, '' if cost == 0 else ' (-{0} punti)'.format(LETTER_COST))
        if self.is_complete():
            self.status = 'won'
            self.last_message = 'Schema completato!'
        else:
            self.advance_turn()
        return True, self.last_message

    def pass_turn(self):
        if self.status != 'active': return False, 'Il cruciverba è concluso.'
        self.moves_played += 1
        self.last_message = 'Turno passato alla prossima squadra.'
        self.advance_turn()
        return True, self.last_message

    def export_state(self):
        return {'title': self.title, 'width': self.width, 'height': self.height, 'entries': self.entries,
                'cells': self.cells, 'dropped': self.dropped, 'status': self.status, 'moves_played': self.moves_played,
                'turn_index': self.turn_index, 'participant_ids': self.participant_ids, 'scores': self.scores,
                'last_message': self.last_message}

    @classmethod
    def from_state(cls, state):
        game = cls()
        game.title = state.get('title', '')
        game.width = state.get('width', 0)
        game.height = state.get('height', 0)
        game.entries = [dict(e) for e in state.get('entries', [])]
        game.cells = [dict(c) for c in state.get('cells', [])]
        game.dropped = list(state.get('dropped', []))
        game.status = state.get('status', 'active')
        game.moves_played = state.get('moves_played', 0)
        game.turn_index = state.get('turn_index', 0)
        game.participant_ids = list(state.get('participant_ids', []))
        game.scores = dict(state.get('scores', {}))
        game.last_message = state.get('last_message', '')
        return game
