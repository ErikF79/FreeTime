# -*- coding: utf-8 -*-
import string
from games.base_game import BaseGame

MAX_ERRORS = 6
ALPHABET = set(string.ascii_uppercase)

class HangmanGame(BaseGame):
    def __init__(self):
        BaseGame.__init__(self, 'impiccato', 'Impiccato',
                           'Indovina la parola lettera per lettera: ogni giocatore ha i suoi tentativi.',
                           'Linguaggio', 1, 8, 'IMP', 'ready')
        self.category = ''
        self.phrase = ''
        self.guessed = []
        self.errors = {}
        self.status = 'active'
        self.mode = 'turno_conquistato'
        self.turn_index = 0
        self.participant_ids = []
        self.scores = {}
        self.last_message = ''

    def setup(self, category, phrase, participant_ids, mode='turno_conquistato'):
        self.category = (category or '').strip()
        self.phrase = (phrase or '').strip().upper()
        self.guessed = []
        self.status = 'active'
        self.mode = mode
        self.turn_index = 0
        self.participant_ids = list(participant_ids)
        self.errors = {pid: 0 for pid in self.participant_ids}
        self.scores = {pid: 0 for pid in self.participant_ids}
        self.last_message = 'Tocca a te: scegli una lettera.'

    def current_player(self):
        if not self.participant_ids: return None
        return self.participant_ids[self.turn_index % len(self.participant_ids)]

    def display_words(self):
        words = []
        for word in self.phrase.split(' '):
            chars = []
            for ch in word:
                if not ch.isalpha(): chars.append(ch)
                elif ch in self.guessed: chars.append(ch)
                else: chars.append('_')
            words.append(chars)
        return words

    def is_fully_revealed(self):
        return all((not ch.isalpha()) or (ch in self.guessed) for ch in self.phrase)

    def is_eliminated(self, pid):
        return self.errors.get(pid, 0) >= MAX_ERRORS

    def all_eliminated(self):
        if not self.participant_ids: return True
        return all(self.is_eliminated(pid) for pid in self.participant_ids)

    def advance_turn(self):
        if not self.participant_ids: return
        for _ in range(len(self.participant_ids)):
            self.turn_index = (self.turn_index + 1) % len(self.participant_ids)
            if not self.is_eliminated(self.current_player()):
                break

    def guess_letter(self, letter):
        if self.status != 'active': return False, 'La manche è conclusa.'
        letter = (letter or '').strip().upper()
        if not letter or len(letter) != 1 or not letter.isalpha():
            return False, 'Inserisci una singola lettera.'
        if letter in self.guessed: return False, 'Lettera già usata.'
        self.guessed.append(letter)
        pid = self.current_player()
        if letter in self.phrase:
            if pid: self.scores[pid] = self.scores.get(pid, 0) + self.phrase.count(letter)
            self.last_message = 'Corretto!'
            if self.is_fully_revealed():
                self.status = 'won'
                self.last_message = 'Parola completata!'
            elif self.mode == 'classico':
                self.advance_turn()
        else:
            if pid: self.errors[pid] = self.errors.get(pid, 0) + 1
            just_eliminated = pid and self.is_eliminated(pid)
            if self.all_eliminated():
                self.status = 'lost'
                self.last_message = 'Tutti i giocatori hanno esaurito i tentativi. La parola era: ' + self.phrase
            else:
                self.last_message = ('Lettera non presente: sei stato eliminato dal turno!' if just_eliminated
                                      else 'Lettera non presente. Turno successivo.')
                self.advance_turn()
        if self.status == 'active' and set(self.guessed) >= ALPHABET:
            self.status = 'lost'
            self.last_message = 'Tutte le lettere sono state tentate. La parola era: ' + self.phrase
        return True, self.last_message

    def export_state(self):
        return {'category': self.category, 'phrase': self.phrase, 'guessed': self.guessed, 'errors': self.errors,
                'status': self.status, 'mode': self.mode, 'turn_index': self.turn_index,
                'participant_ids': self.participant_ids, 'scores': self.scores, 'last_message': self.last_message}

    @classmethod
    def from_state(cls, state):
        game = cls()
        game.category = state.get('category', '')
        game.phrase = state.get('phrase', '')
        game.guessed = list(state.get('guessed', []))
        game.errors = dict(state.get('errors', {}))
        game.status = state.get('status', 'active')
        game.mode = state.get('mode', 'turno_conquistato')
        game.turn_index = state.get('turn_index', 0)
        game.participant_ids = list(state.get('participant_ids', []))
        game.scores = dict(state.get('scores', {}))
        game.last_message = state.get('last_message', '')
        return game
