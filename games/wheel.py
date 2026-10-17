# -*- coding: utf-8 -*-
import random
from games.base_game import BaseGame

SPIN_VALUES = [100, 150, 200, 200, 250, 300, 350, 400, 450, 500, 'PERDITURNO']
PHRASE_BONUS = 500

class WheelGame(BaseGame):
    def __init__(self):
        BaseGame.__init__(self, 'wheel', 'Ruota della fortuna',
                           'Indovina la frase segreta lettera per lettera, girando la ruota per i punti.',
                           'Linguaggio', 1, 8, 'RF', 'ready')
        self.category = ''
        self.phrase = ''
        self.guessed = []
        self.spin_value = None
        self.status = 'active'
        self.turn_index = 0
        self.participant_ids = []
        self.scores = {}
        self.last_message = ''

    def setup(self, category, phrase, participant_ids, mode='turno_conquistato'):
        self.category = (category or '').strip()
        self.phrase = (phrase or '').strip().upper()
        self.guessed = []
        self.spin_value = None
        self.status = 'active'
        self.mode = mode
        self.turn_index = 0
        self.participant_ids = list(participant_ids)
        self.scores = {pid: 0 for pid in self.participant_ids}
        self.last_message = 'Tocca a te: gira la ruota per iniziare.'

    def current_player(self):
        if not self.participant_ids: return None
        return self.participant_ids[self.turn_index % len(self.participant_ids)]

    def display(self):
        out = []
        for ch in self.phrase:
            if ch == ' ':
                out.append(' ')
            elif not ch.isalpha():
                out.append(ch)
            elif ch in self.guessed:
                out.append(ch)
            else:
                out.append('_')
        return out

    def display_words(self):
        words = []
        for word in self.phrase.split(' '):
            chars = []
            for ch in word:
                if not ch.isalpha():
                    chars.append(ch)
                elif ch in self.guessed:
                    chars.append(ch)
                else:
                    chars.append('_')
            words.append(chars)
        return words

    def is_fully_revealed(self):
        return all((not ch.isalpha()) or (ch in self.guessed) for ch in self.phrase)

    def advance_turn(self):
        if self.participant_ids:
            self.turn_index = (self.turn_index + 1) % len(self.participant_ids)
        self.spin_value = None

    def spin(self):
        if self.status != 'active': return False, 'La manche è conclusa.'
        if self.spin_value is not None: return False, 'Hai già girato la ruota: indovina una lettera.'
        self.spin_value = random.choice(SPIN_VALUES)
        if self.spin_value == 'PERDITURNO':
            self.last_message = 'Turno perso! Passa al prossimo giocatore.'
            self.advance_turn()
        else:
            self.last_message = 'Hai ottenuto {0} punti a lettera. Scegli una lettera.'.format(self.spin_value)
        return True, self.last_message

    def guess_letter(self, letter):
        if self.status != 'active': return False, 'La manche è conclusa.'
        if self.spin_value is None: return False, 'Gira la ruota prima di indovinare una lettera.'
        letter = (letter or '').strip().upper()
        if not letter or len(letter) != 1 or not letter.isalpha():
            return False, 'Inserisci una singola lettera.'
        if letter in self.guessed:
            return False, 'Lettera già usata.'
        self.guessed.append(letter)
        occurrences = self.phrase.count(letter)
        if occurrences > 0:
            pid = self.current_player()
            if pid: self.scores[pid] = self.scores.get(pid, 0) + occurrences * self.spin_value
            self.spin_value = None
            self.last_message = 'Corretto! {0} lettera/e trovate.'.format(occurrences)
            if self.is_fully_revealed():
                self.status = 'won'
                self.last_message = 'Frase completata!'
            elif self.mode == 'classico':
                self.advance_turn()
        else:
            self.last_message = 'Lettera non presente. Turno successivo.'
            self.advance_turn()
        return True, self.last_message

    def attack(self, target_id):
        if self.status != 'active': return False, 'La manche è conclusa.'
        if self.mode != 'distruttivo': return False, 'Questa azione è disponibile solo in modalità Distruttivo.'
        if self.spin_value is None: return False, 'Gira la ruota prima di attaccare.'
        if not target_id or target_id not in self.participant_ids or target_id == self.current_player():
            return False, 'Scegli un avversario valido.'
        self.scores[target_id] = max(0, self.scores.get(target_id, 0) - self.spin_value)
        self.last_message = 'Hai tolto {0} punti a un avversario!'.format(self.spin_value)
        self.spin_value = None
        self.advance_turn()
        return True, self.last_message

    def guess_phrase(self, text):
        if self.status != 'active': return False, 'La manche è conclusa.'
        guess = (text or '').strip().upper()
        if not guess: return False, 'Scrivi una frase.'
        if guess == self.phrase:
            pid = self.current_player()
            if pid: self.scores[pid] = self.scores.get(pid, 0) + PHRASE_BONUS
            for ch in self.phrase:
                if ch.isalpha() and ch not in self.guessed: self.guessed.append(ch)
            self.status = 'won'
            self.last_message = 'Frase indovinata! +{0} punti bonus.'.format(PHRASE_BONUS)
            return True, self.last_message
        self.last_message = 'Frase sbagliata. Turno successivo.'
        self.advance_turn()
        return False, self.last_message

    def export_state(self):
        return {'category': self.category, 'phrase': self.phrase, 'guessed': self.guessed,
                'spin_value': self.spin_value, 'status': self.status, 'mode': getattr(self,'mode','turno_conquistato'),
                'turn_index': self.turn_index, 'participant_ids': self.participant_ids, 'scores': self.scores,
                'last_message': self.last_message}

    @classmethod
    def from_state(cls, state):
        game = cls()
        game.category = state.get('category', '')
        game.phrase = state.get('phrase', '')
        game.guessed = list(state.get('guessed', []))
        game.spin_value = state.get('spin_value')
        game.status = state.get('status', 'active')
        game.mode = state.get('mode', 'turno_conquistato')
        game.turn_index = state.get('turn_index', 0)
        game.participant_ids = list(state.get('participant_ids', []))
        game.scores = dict(state.get('scores', {}))
        game.last_message = state.get('last_message', '')
        return game
