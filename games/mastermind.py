# -*- coding: utf-8 -*-
import random
from games.base_game import BaseGame

COLORS = ['R','G','B','Y','O','P']
COLOR_NAMES = {'R':'Rosso','G':'Verde','B':'Blu','Y':'Giallo','O':'Arancio','P':'Viola'}
DIFFICULTIES = {
    'easy':   {'length':3,'colors':4,'attempts':12,'label':'Facile'},
    'medium': {'length':4,'colors':5,'attempts':10,'label':'Media'},
    'hard':   {'length':4,'colors':6,'attempts':8,'label':'Difficile'},
}

class MastermindGame(BaseGame):
    def __init__(self):
        BaseGame.__init__(self, 'mastermind', 'Mastermind',
                           'Indovina il codice segreto colore per colore, un tentativo alla volta.',
                           'Logica', 1, 8, 'MM', 'ready')
        self.difficulty = 'medium'
        self.code = []
        self.length = 4
        self.palette = COLORS[:5]
        self.max_attempts = 10
        self.guesses = []
        self.status = 'active'
        self.turn_index = 0
        self.participant_ids = []
        self.winner_id = None
        self.last_message = ''

    def setup(self, difficulty, participant_ids, mode='classico'):
        conf = DIFFICULTIES.get(difficulty, DIFFICULTIES['medium'])
        self.difficulty = difficulty if difficulty in DIFFICULTIES else 'medium'
        self.length = conf['length']
        self.palette = COLORS[:conf['colors']]
        self.max_attempts = conf['attempts']
        self.code = [random.choice(self.palette) for _ in range(self.length)]
        self.guesses = []
        self.status = 'active'
        self.mode = mode
        self.turn_index = 0
        self.participant_ids = list(participant_ids)
        self.winner_id = None
        self.last_message = 'Tocca a te: prova un codice.'

    def current_player(self):
        if not self.participant_ids: return None
        return self.participant_ids[self.turn_index % len(self.participant_ids)]

    def advance_turn(self):
        if self.participant_ids:
            self.turn_index = (self.turn_index + 1) % len(self.participant_ids)

    def evaluate(self, guess):
        black = sum(1 for i in range(self.length) if guess[i] == self.code[i])
        code_rest = [self.code[i] for i in range(self.length) if guess[i] != self.code[i]]
        guess_rest = [guess[i] for i in range(self.length) if guess[i] != self.code[i]]
        white = 0
        for c in list(guess_rest):
            if c in code_rest:
                white += 1
                code_rest.remove(c)
        return black, white

    def guess(self, colors):
        if self.status != 'active': return False, 'La manche è conclusa.'
        colors = list(colors)
        if len(colors) != self.length or any(c not in self.palette for c in colors):
            return False, 'Tentativo non valido: scegli un colore per ogni casella.'
        pid = self.current_player()
        black, white = self.evaluate(colors)
        self.guesses.append({'guess': colors, 'black': black, 'white': white, 'player_id': pid})
        if black == self.length:
            self.status = 'won'; self.winner_id = pid
            self.last_message = 'Codice indovinato!'
            return True, self.last_message
        if len(self.guesses) >= self.max_attempts:
            self.status = 'lost'
            self.last_message = 'Tentativi esauriti. Il codice era: ' + ' '.join(COLOR_NAMES[c] for c in self.code)
            return True, self.last_message
        if self.mode == 'turno_conquistato' and (black > 0 or white > 0):
            self.last_message = '{0} esatti, {1} presenti ma spostati. Continua tu!'.format(black, white)
        else:
            self.advance_turn()
            self.last_message = '{0} esatti, {1} presenti ma spostati.'.format(black, white)
        return True, self.last_message

    def export_state(self):
        return {'difficulty': self.difficulty, 'code': self.code, 'length': self.length, 'palette': self.palette,
                'max_attempts': self.max_attempts, 'guesses': self.guesses, 'status': self.status,
                'mode': getattr(self,'mode','classico'),
                'turn_index': self.turn_index, 'participant_ids': self.participant_ids,
                'winner_id': self.winner_id, 'last_message': self.last_message}

    @classmethod
    def from_state(cls, state):
        game = cls()
        game.difficulty = state.get('difficulty', 'medium')
        game.code = list(state.get('code', []))
        game.length = state.get('length', 4)
        game.palette = list(state.get('palette', COLORS[:5]))
        game.max_attempts = state.get('max_attempts', 10)
        game.guesses = list(state.get('guesses', []))
        game.status = state.get('status', 'active')
        game.mode = state.get('mode', 'classico')
        game.turn_index = state.get('turn_index', 0)
        game.participant_ids = list(state.get('participant_ids', []))
        game.winner_id = state.get('winner_id')
        game.last_message = state.get('last_message', '')
        return game
