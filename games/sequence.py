# -*- coding: utf-8 -*-
import random, time, colorsys
from games.base_game import BaseGame

SEQUENCE_TYPES = {
    'numeri': 'Numeri crescenti',
    'lettere': 'Lettere in ordine',
    'multipli': 'Multipli crescenti',
    'colori': 'Sfumature dal chiaro allo scuro',
}

def generate_items(grid_size, sequence_type):
    items = []
    if sequence_type == 'lettere':
        for rank in range(1, grid_size + 1):
            items.append({'label': chr(ord('A') + rank - 1), 'rank': rank, 'kind': 'text'})
    elif sequence_type == 'multipli':
        base = random.choice([2, 3, 4, 5])
        for rank in range(1, grid_size + 1):
            items.append({'label': str(base * rank), 'rank': rank, 'kind': 'text'})
    elif sequence_type == 'colori':
        hue = random.choice([0.0, 0.11, 0.33, 0.58, 0.75])
        for rank in range(1, grid_size + 1):
            t = (rank - 1) / max(1, grid_size - 1)
            lightness = 0.85 - t * 0.68
            r, g, b = colorsys.hls_to_rgb(hue, lightness, 0.6)
            hexcolor = '#{0:02x}{1:02x}{2:02x}'.format(int(r * 255), int(g * 255), int(b * 255))
            items.append({'label': hexcolor, 'rank': rank, 'kind': 'color'})
    else:
        for rank in range(1, grid_size + 1):
            items.append({'label': str(rank), 'rank': rank, 'kind': 'text'})
    return items

class SequenceGame(BaseGame):
    def __init__(self):
        BaseGame.__init__(self, 'sequence', 'Sequenza numeri',
                           'Tocca la sequenza in ordine il più veloce possibile: numeri, lettere, multipli o sfumature di colore.',
                           'Attenzione', 1, 8, 'SEQ', 'ready')
        self.grid_size = 16
        self.sequence_type = 'numeri'
        self.participant_ids = []
        self.turn_index = 0
        self.phase = 'waiting_ready'
        self.items = []
        self.done_indices = []
        self.next_expected = 1
        self.start_time = None
        self.results = {}
        self.status = 'active'
        self.last_message = ''

    def setup(self, grid_size, sequence_type, participant_ids):
        self.grid_size = grid_size
        self.sequence_type = sequence_type if sequence_type in SEQUENCE_TYPES else 'numeri'
        self.participant_ids = list(participant_ids)
        self.turn_index = 0
        self.phase = 'waiting_ready'
        self.items = []
        self.done_indices = []
        self.next_expected = 1
        self.start_time = None
        self.results = {}
        self.status = 'active'
        self.last_message = 'Tocca "Pronti? Via!" quando sei pronto.'

    def current_player(self):
        if not self.participant_ids: return None
        return self.participant_ids[self.turn_index % len(self.participant_ids)]

    def next_item(self):
        for item in self.items:
            if item['rank'] == self.next_expected:
                return item
        return None

    def start_turn(self):
        if self.phase != 'waiting_ready': return False, 'Non è il momento di iniziare.'
        self.items = generate_items(self.grid_size, self.sequence_type)
        random.shuffle(self.items)
        self.done_indices = []
        self.next_expected = 1
        self.start_time = time.time()
        self.phase = 'playing'
        self.last_message = 'Via! Tocca nell\'ordine giusto.'
        return True, self.last_message

    def tap(self, index):
        if self.phase != 'playing': return False, 'Devi prima toccare "Pronti? Via!".'
        if index is None or index < 0 or index >= len(self.items): return False, 'Selezione non valida.'
        if index in self.done_indices: return False, 'Già selezionato.'
        if self.items[index]['rank'] != self.next_expected:
            return False, 'Ordine sbagliato, riprova.'
        self.done_indices.append(index)
        self.next_expected += 1
        if self.next_expected > self.grid_size:
            elapsed = round(time.time() - self.start_time, 2)
            pid = self.current_player()
            if pid: self.results[pid] = elapsed
            self.last_message = 'Completato in {0} secondi!'.format(elapsed)
            remaining = [p for p in self.participant_ids if p not in self.results]
            if not remaining:
                self.status = 'finished'
                self.phase = 'finished'
                self.last_message = 'Gara conclusa!'
            else:
                for _ in range(len(self.participant_ids)):
                    self.turn_index = (self.turn_index + 1) % len(self.participant_ids)
                    if self.current_player() not in self.results: break
                self.phase = 'waiting_ready'
        else:
            self.last_message = 'Corretto! Prossimo.'
        return True, self.last_message

    def export_state(self):
        return {'grid_size': self.grid_size, 'sequence_type': self.sequence_type,
                'participant_ids': self.participant_ids, 'turn_index': self.turn_index,
                'phase': self.phase, 'items': self.items, 'done_indices': self.done_indices,
                'next_expected': self.next_expected, 'start_time': self.start_time, 'results': self.results,
                'status': self.status, 'last_message': self.last_message}

    @classmethod
    def from_state(cls, state):
        game = cls()
        game.grid_size = state.get('grid_size', 16)
        game.sequence_type = state.get('sequence_type', 'numeri')
        game.participant_ids = list(state.get('participant_ids', []))
        game.turn_index = state.get('turn_index', 0)
        game.phase = state.get('phase', 'waiting_ready')
        game.items = list(state.get('items', []))
        game.done_indices = list(state.get('done_indices', []))
        game.next_expected = state.get('next_expected', 1)
        game.start_time = state.get('start_time')
        game.results = dict(state.get('results', {}))
        game.status = state.get('status', 'active')
        game.last_message = state.get('last_message', '')
        return game
