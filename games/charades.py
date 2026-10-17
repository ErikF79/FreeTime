# -*- coding: utf-8 -*-
from games.base_game import BaseGame

class CharadesGame(BaseGame):
    def __init__(self):
        BaseGame.__init__(self, 'mimo', 'Indovina mimando',
                           'Mima un film, una canzone o una frase: gli altri devono indovinare a voce.',
                           'Sociale', 2, 8, 'MIM', 'ready')
        self.category = ''
        self.phrase = ''
        self.status = 'active'
        self.turn_index = 0
        self.participant_ids = []
        self.scores = {}
        self.rounds_played = 0
        self.last_message = ''

    def setup(self, participant_ids, mode='classico'):
        self.status = 'active'
        self.mode = mode
        self.turn_index = 0
        self.participant_ids = list(participant_ids)
        self.scores = {pid: 0 for pid in self.participant_ids}
        self.rounds_played = 0
        self.category = ''
        self.phrase = ''
        self.last_message = ''

    def current_player(self):
        if not self.participant_ids: return None
        return self.participant_ids[self.turn_index % len(self.participant_ids)]

    def advance_turn(self):
        if self.participant_ids:
            self.turn_index = (self.turn_index + 1) % len(self.participant_ids)

    def load_round(self, content):
        if content:
            self.category = content.get('category', '')
            self.phrase = content.get('phrase', '')
            return True
        self.category = ''
        self.phrase = ''
        return False

    def resolve(self, correct):
        pid = self.current_player()
        if correct and pid: self.scores[pid] = self.scores.get(pid, 0) + 1
        self.rounds_played += 1
        if not (self.mode == 'turno_conquistato' and correct):
            self.advance_turn()

    def export_state(self):
        return {'category': self.category, 'phrase': self.phrase, 'status': self.status,
                'mode': getattr(self,'mode','classico'),
                'turn_index': self.turn_index, 'participant_ids': self.participant_ids,
                'scores': self.scores, 'rounds_played': self.rounds_played, 'last_message': self.last_message}

    @classmethod
    def from_state(cls, state):
        game = cls()
        game.category = state.get('category', '')
        game.phrase = state.get('phrase', '')
        game.status = state.get('status', 'active')
        game.mode = state.get('mode', 'classico')
        game.turn_index = state.get('turn_index', 0)
        game.participant_ids = list(state.get('participant_ids', []))
        game.scores = dict(state.get('scores', {}))
        game.rounds_played = state.get('rounds_played', 0)
        game.last_message = state.get('last_message', '')
        return game
