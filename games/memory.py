# -*- coding: utf-8 -*-
import random
from games.base_game import BaseGame

SYMBOLS = ['★','●','■','▲','♥','♦','♣','♠','◆','✦','✚','⬟','☀','☾','✈','⌘']

class MemoryGame(BaseGame):
    def __init__(self):
        BaseGame.__init__(self, 'memory', 'Memory',
                           'Trova tutte le coppie di carte uguali nel minor numero di tentativi.',
                           'Memoria', 1, 8, 'MEM', 'ready')
        self.cards = []
        self.matched = []
        self.pending = []
        self.status = 'active'
        self.turn_index = 0
        self.participant_ids = []
        self.scores = {}
        self.last_message = ''

    def setup(self, pairs, participant_ids, mode='turno_conquistato'):
        pairs = max(4, min(int(pairs), len(SYMBOLS)))
        chosen = SYMBOLS[:pairs]
        deck = chosen * 2
        random.shuffle(deck)
        self.cards = deck
        self.matched = [False] * len(deck)
        self.pending = []
        self.status = 'active'
        self.mode = mode
        self.turn_index = 0
        self.participant_ids = list(participant_ids)
        self.scores = {pid: 0 for pid in self.participant_ids}
        self.last_message = 'Tocca a te: scegli la prima carta.'

    def current_player(self):
        if not self.participant_ids: return None
        return self.participant_ids[self.turn_index % len(self.participant_ids)]

    def advance_turn(self):
        if self.participant_ids:
            self.turn_index = (self.turn_index + 1) % len(self.participant_ids)

    def is_complete(self):
        return all(self.matched)

    def flip(self, index):
        if self.status != 'active': return False, 'La manche è conclusa.'
        if index is None or index < 0 or index >= len(self.cards): return False, 'Carta non valida.'
        if self.matched[index]: return False, 'Questa carta è già stata trovata.'
        if index in self.pending: return False, 'Carta già scoperta in questo turno.'
        if len(self.pending) >= 2: return False, 'Premi Continua prima di scoprire altre carte.'
        self.pending.append(index)
        if len(self.pending) == 1:
            self.last_message = 'Scegli la seconda carta.'
            return True, self.last_message
        a, b = self.pending
        if self.cards[a] == self.cards[b]:
            self.matched[a] = True; self.matched[b] = True
            pid = self.current_player()
            if pid: self.scores[pid] = self.scores.get(pid, 0) + 1
            self.pending = []
            self.last_message = 'Coppia trovata! Gioca ancora.'
            if self.is_complete():
                self.status = 'won'
                self.last_message = 'Tutte le coppie trovate!'
            elif self.mode == 'classico':
                self.advance_turn()
                self.last_message = 'Coppia trovata! Turno successivo.'
        else:
            self.last_message = 'Non è una coppia. Premi Continua per proseguire.'
        return True, self.last_message

    def continue_turn(self):
        if len(self.pending) < 2: return False, 'Non ci sono carte da nascondere.'
        self.pending = []
        self.advance_turn()
        self.last_message = 'Tocca al prossimo giocatore.'
        return True, self.last_message

    def export_state(self):
        return {'cards': self.cards, 'matched': self.matched, 'pending': self.pending, 'status': self.status,
                'mode': getattr(self,'mode','turno_conquistato'),
                'turn_index': self.turn_index, 'participant_ids': self.participant_ids, 'scores': self.scores,
                'last_message': self.last_message}

    @classmethod
    def from_state(cls, state):
        game = cls()
        game.cards = list(state.get('cards', []))
        game.matched = list(state.get('matched', []))
        game.pending = list(state.get('pending', []))
        game.status = state.get('status', 'active')
        game.mode = state.get('mode', 'turno_conquistato')
        game.turn_index = state.get('turn_index', 0)
        game.participant_ids = list(state.get('participant_ids', []))
        game.scores = dict(state.get('scores', {}))
        game.last_message = state.get('last_message', '')
        return game
